"""Stalker portal session management."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING

from ..base.errors import AuthError, NetworkError
from .constants import MAX_RECONNECT_TRIES, RECONNECT_BASE_DELAY, RECONNECT_MAX_DELAY
from .protocol_profile import LegacyMAGProtocolProfile, MAGOperation, MAGProtocolProfile

if TYPE_CHECKING:
    from .connection import MAGConnection
    from .credentials import MAGCredentials

log = logging.getLogger(__name__)


class MAGSession:
    """Own a private MAG token and send requests through one selected profile."""

    def __init__(
        self,
        connection: MAGConnection,
        credentials: MAGCredentials,
        profile: MAGProtocolProfile | None = None,
    ) -> None:
        self._conn = connection
        self._creds = credentials
        self._profile = profile or LegacyMAGProtocolProfile()
        self._token_expires_at: float = 0.0
        self._refresh_task: asyncio.Task[None] | None = None

    @property
    def token(self) -> str:
        return self._creds.token

    @property
    def profile(self) -> MAGProtocolProfile:
        """Return the current fixed protocol profile without credential data."""
        return self._profile

    @property
    def credentials(self) -> MAGCredentials:
        """Return legacy-layer credentials only for local protocol discovery."""
        return self._creds

    @property
    def is_authenticated(self) -> bool:
        return bool(self._creds.token) and time.monotonic() < self._token_expires_at

    def select_profile(self, profile: MAGProtocolProfile) -> None:
        """Select a discovery-verified profile before authentication starts."""
        if self._creds.token:
            raise AuthError("MAG protocol profile cannot change during an active session")
        self._profile = profile

    async def authenticate(self) -> None:
        """Perform one profile-owned handshake and retain its token privately."""
        request = self._profile.build_request(self._creds.portal_url, MAGOperation.HANDSHAKE)
        payload = await self._conn.get(
            request.endpoint,
            params=request.params,
            headers={**request.headers, **self._request_headers()},
            base_url=request.base_url,
        )
        self._store_token(payload)
        self._schedule_refresh()
        log.info("MAG authentication successful")

    async def refresh(self) -> None:
        """Refresh the token through the same selected protocol profile."""
        try:
            request = self._profile.build_request(self._creds.portal_url, MAGOperation.HANDSHAKE)
            payload = await self._conn.get(
                request.endpoint,
                params=request.params,
                headers={**request.headers, **self._request_headers()},
                base_url=request.base_url,
            )
            self._store_token(payload)
            log.debug("MAG token refreshed")
        except NetworkError:
            log.warning("MAG token refresh failed; will retry")
            raise

    async def request(
        self,
        operation: MAGOperation,
        *,
        params: dict[str, str | int] | None = None,
    ) -> object:
        """Perform a selected-profile operation with the current session headers."""
        request = self._profile.build_request(self._creds.portal_url, operation, params=params)
        return await self._conn.get(
            request.endpoint,
            params=request.params,
            headers={**request.headers, **self._request_headers()},
            base_url=request.base_url,
        )

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
            except (NetworkError, AuthError):
                log.warning("MAG auto-refresh attempt %d failed", attempt)
                if attempt < MAX_RECONNECT_TRIES:
                    sleep_for = min(delay, RECONNECT_MAX_DELAY)
                    await asyncio.sleep(sleep_for)
                    delay *= 2
        log.error("All MAG token refresh attempts exhausted")

    def _request_headers(self) -> dict[str, str]:
        """Build selected-profile headers privately for one runtime request."""
        return self._profile.request_headers(
            self._creds.portal_url,
            mac_address=self._creds.mac_address,
            serial_number=self._creds.serial_number,
            device_id=self._creds.device_id,
            device_id2=self._creds.device_id2,
            token=self._creds.token,
            mag_model=self._creds.mag_model,
        )

    def _store_token(self, payload: object) -> None:
        handshake = self._profile.parse_handshake(payload)
        self._creds.token = handshake.token
        self._token_expires_at = time.monotonic() + handshake.ttl_seconds
        log.debug("MAG token stored (TTL=%ds)", handshake.ttl_seconds)

    def get_headers(self) -> dict[str, str]:
        """Return current auth headers for compatibility with older callers."""
        return self._request_headers()
