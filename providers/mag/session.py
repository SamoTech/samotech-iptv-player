"""
Stalker portal session management.

Handles the Stalker handshake, token issuance and automatic refresh.
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Optional

from .constants import (
    DEFAULT_TOKEN_TTL_S,
    MAX_RECONNECT_TRIES,
    RECONNECT_BASE_DELAY,
    RECONNECT_MAX_DELAY,
    ENDPOINT_HANDSHAKE,
)
from .credentials import MAGCredentials
from .connection import MAGConnection
from ..base.errors import AuthError, NetworkError

log = logging.getLogger(__name__)


class MAGSession:
    def __init__(self, connection: MAGConnection, credentials: MAGCredentials) -> None:
        self._conn = connection
        self._creds = credentials
        self._token_expires_at: float = 0.0
        self._refresh_task: Optional[asyncio.Task] = None

    @property
    def token(self) -> str:
        return self._creds.token

    @property
    def is_authenticated(self) -> bool:
        return bool(self._creds.token) and time.monotonic() < self._token_expires_at

    async def authenticate(self) -> None:
        log.info("Authenticating with portal %s", self._creds.portal_url)
        payload = await self._conn.get(
            ENDPOINT_HANDSHAKE,
            headers=self._auth_headers(),
        )
        self._store_token(payload)
        self._schedule_refresh()
        log.info("Authentication successful — token acquired")

    async def refresh(self) -> None:
        log.debug("Refreshing portal token")
        try:
            payload = await self._conn.get(
                ENDPOINT_HANDSHAKE,
                headers=self._auth_headers(),
            )
            self._store_token(payload)
            log.debug("Token refreshed")
        except NetworkError as exc:
            log.warning("Token refresh failed: %s — will retry", exc)
            raise

    async def close(self) -> None:
        if self._refresh_task and not self._refresh_task.done():
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                pass

    def _schedule_refresh(self) -> None:
        ttl = max(self._token_expires_at - time.monotonic() - 60, 30)
        if self._refresh_task and not self._refresh_task.done():
            self._refresh_task.cancel()
        self._refresh_task = asyncio.get_event_loop().create_task(
            self._refresh_loop(ttl)
        )

    async def _refresh_loop(self, initial_delay: float) -> None:
        await asyncio.sleep(initial_delay)
        delay = RECONNECT_BASE_DELAY
        for attempt in range(1, MAX_RECONNECT_TRIES + 1):
            try:
                await self.refresh()
                self._schedule_refresh()
                return
            except (NetworkError, AuthError) as exc:
                log.warning("Auto-refresh attempt %d failed: %s", attempt, exc)
                if attempt < MAX_RECONNECT_TRIES:
                    sleep_for = min(delay, RECONNECT_MAX_DELAY)
                    await asyncio.sleep(sleep_for)
                    delay *= 2
        log.error("All token refresh attempts exhausted")

    def _auth_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {
            "Authorization": f"Bearer {self._creds.token}" if self._creds.token else "",
            "X-User-Mac": self._creds.mac_address,
        }
        if self._creds.serial_number:
            headers["X-Device-Serial"] = self._creds.serial_number
        if self._creds.device_id:
            headers["X-Device-ID"] = self._creds.device_id
        if self._creds.device_id2:
            headers["X-Device-ID2"] = self._creds.device_id2
        return {k: v for k, v in headers.items() if v}

    def _store_token(self, payload: dict) -> None:
        js = payload.get("js", {})
        token = js.get("token") or payload.get("token")
        if not token:
            raise AuthError(
                "Portal handshake response did not contain a token. "
                "Check that your credentials are correct and that you are "
                "authorised to access this portal."
            )
        self._creds.token = str(token)
        ttl = int(js.get("token_TTL") or DEFAULT_TOKEN_TTL_S)
        self._token_expires_at = time.monotonic() + ttl
        log.debug("Token stored (TTL=%ds)", ttl)

    def get_headers(self) -> dict[str, str]:
        return self._auth_headers()
