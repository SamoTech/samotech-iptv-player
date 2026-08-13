"""
Stalker portal session management.

Handles the Stalker handshake, token issuance and automatic refresh.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Mapping
from typing import TYPE_CHECKING

from ..base.errors import AuthError, NetworkError
from .constants import (
    DEFAULT_TOKEN_TTL_S,
    MAX_RECONNECT_TRIES,
    RECONNECT_BASE_DELAY,
    RECONNECT_MAX_DELAY,
)
from .protocol_profile import LegacyMAGProtocolProfile, MAGProtocolProfile

if TYPE_CHECKING:
    from samotech_iptv.core.typing import JSON

    from .connection import MAGConnection
    from .credentials import MAGCredentials

log = logging.getLogger(__name__)


class MAGSession:
    def __init__(
        self,
        connection: MAGConnection,
        credentials: MAGCredentials,
        profile: MAGProtocolProfile | None = None,
    ) -> None:
        self._conn = connection
        self._creds = credentials
        self._profile = profile
        self._token_expires_at: float = 0.0
        self._refresh_task: asyncio.Task[None] | None = None

    @property
    def token(self) -> str:
        return self._creds.token

    @property
    def is_authenticated(self) -> bool:
        return bool(self._creds.token) and time.monotonic() < self._token_expires_at

    async def authenticate(self) -> None:
        log.info("Authenticating with portal %s", self._creds.portal_url)
        profile = self._profile or LegacyMAGProtocolProfile()
        endpoint, params, profile_headers = profile.handshake_request(self._creds.portal_url)
        headers = {**profile_headers, **self._auth_headers()}
        payload = await self._conn.get(endpoint, params=params, headers=headers)
        self._store_token(payload)
        self._schedule_refresh()
        log.info("Authentication successful — token acquired")

    async def refresh(self) -> None:
        log.debug("Refreshing portal token")
        try:
            profile = self._profile or LegacyMAGProtocolProfile()
            endpoint, params, profile_headers = profile.handshake_request(self._creds.portal_url)
            headers = {**profile_headers, **self._auth_headers()}
            payload = await self._conn.get(endpoint, params=params, headers=headers)
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
        self._refresh_task = asyncio.get_event_loop().create_task(self._refresh_loop(ttl))

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

    def _store_token(self, payload: JSON) -> None:
        if not isinstance(payload, Mapping):
            raise AuthError("Portal handshake response did not contain a JSON object")
        raw_js = payload.get("js", {})
        js = raw_js if isinstance(raw_js, Mapping) else {}
        token = js.get("token") or payload.get("token")
        if not token:
            raise AuthError(
                "Portal handshake response did not contain a token. "
                "Check that your credentials are correct and that you are "
                "authorised to access this portal."
            )
        self._creds.token = str(token)
        raw_ttl = js.get("token_TTL")
        try:
            ttl = int(str(raw_ttl)) if raw_ttl else DEFAULT_TOKEN_TTL_S
        except ValueError as exc:
            raise AuthError("Portal handshake response contained an invalid token TTL") from exc
        self._token_expires_at = time.monotonic() + ttl
        log.debug("Token stored (TTL=%ds)", ttl)

    def get_headers(self) -> dict[str, str]:
        return self._auth_headers()
