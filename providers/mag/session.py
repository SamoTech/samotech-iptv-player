"""Stalker portal session management."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Mapping
from typing import TYPE_CHECKING

from ..base.errors import AuthError, NetworkError
from .constants import MAX_RECONNECT_TRIES, RECONNECT_BASE_DELAY, RECONNECT_MAX_DELAY
from .protocol_profile import (
    LegacyMAGProtocolProfile,
    MAGAuthMode,
    MAGAuthState,
    MAGOperation,
    MAGProtocolProfile,
    MAGProtocolRequest,
)

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
        self._auth_state = MAGAuthState.DISCOVERY
        self._last_profile_classification = "NOT_REQUESTED"

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
    def auth_state(self) -> MAGAuthState:
        """Return the private state-machine stage without credential data."""
        return self._auth_state

    @property
    def last_profile_classification(self) -> str:
        """Return only the safe classification of the last profile response."""
        return self._last_profile_classification

    @property
    def is_authenticated(self) -> bool:
        return bool(self._creds.token) and time.monotonic() < self._token_expires_at

    def select_profile(self, profile: MAGProtocolProfile) -> None:
        """Select a discovery-verified profile before authentication starts."""
        if self._creds.token:
            raise AuthError("MAG protocol profile cannot change during an active session")
        self._profile = profile

    async def authenticate(self) -> None:
        """Run the evidence-backed optional authentication state machine."""
        self._auth_state = MAGAuthState.HANDSHAKE
        request = self._profile.build_request(self._creds.portal_url, MAGOperation.HANDSHAKE)
        payload = await self._send_profile_request(request)
        self._store_token(payload)
        self._auth_state = MAGAuthState.TOKEN_RECEIVED
        try:
            await self._run_post_handshake_stages()
        except (AuthError, NetworkError):
            self._invalidate_session()
            raise
        self._auth_state = MAGAuthState.SESSION_VALIDATED
        self._schedule_refresh()
        log.info("MAG authentication successful")

    async def _run_post_handshake_stages(self) -> None:
        """Run explicitly selected stages after a structurally valid token."""
        if self._creds.profile_required or self._creds.profile_second_step:
            self._auth_state = MAGAuthState.PROFILE_REQUIRED
            await self.get_profile(auth_second_step=self._creds.profile_second_step)
        if self._creds.auth_mode == MAGAuthMode.MAC_PLUS_LOGIN.value:
            self._auth_state = MAGAuthState.DO_AUTH
            await self.do_auth()
        elif self._creds.auth_mode == MAGAuthMode.AUTHORIZATION_KEY.value:
            self._auth_state = MAGAuthState.AUTH_KEY_REQUIRED
            if not self._creds.authorization_key:
                raise AuthError("AUTH_KEY_REQUIRED: authorization key is not configured")
            raise AuthError(
                "AUTH_KEY_TRANSPORT_UNSUPPORTED: authorization-key request transport "
                "is not established"
            )

    async def get_profile(self, *, auth_second_step: bool = False) -> object:
        """Request the minimal or explicitly populated profile stage."""
        self._auth_state = MAGAuthState.GET_PROFILE
        request = self._profile.build_request(self._creds.portal_url, MAGOperation.GET_PROFILE)
        params = self._profile.profile_params(
            serial_number=self._creds.serial_number,
            device_id=self._creds.device_id,
            device_id2=self._creds.device_id2,
            mag_model=self._creds.mag_model,
            signature=self._creds.signature,
            hd=self._creds.profile_hd,
            auth_second_step=auth_second_step,
        )
        payload = await self._conn.get(
            request.endpoint,
            params=params,
            headers={**request.headers, **self._request_headers()},
            base_url=request.base_url,
        )
        raw_js = payload.get("js") if isinstance(payload, Mapping) else None
        if isinstance(raw_js, Mapping) and raw_js.get("error"):
            classification = self._classify_policy(raw_js.get("error"))
            self._last_profile_classification = classification
            raise AuthError(f"{classification}: portal rejected get_profile")
        if not isinstance(raw_js, (Mapping, list, str, int, float, bool)):
            self._last_profile_classification = "PROFILE_REQUIRED"
            raise AuthError("PROFILE_REQUIRED: portal returned no profile object")
        self._last_profile_classification = "PROFILE_SUCCESS"
        return payload

    async def do_auth(self) -> object:
        """Run explicit login/password authentication using form POST only."""
        if not self._creds.login or not self._creds.password:
            raise AuthError("LOGIN_REQUIRED: login/password are not configured")
        request = self._profile.build_request(self._creds.portal_url, MAGOperation.DO_AUTH)
        params = self._profile.do_auth_params(
            login=self._creds.login,
            password=self._creds.password,
            device_id=self._creds.device_id,
            device_id2=self._creds.device_id2,
            signature=self._creds.signature,
        )
        headers = {**request.headers, **self._request_headers()}
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        payload = await self._conn.post(
            request.endpoint,
            data=params,
            headers=headers,
            base_url=request.base_url,
        )
        raw_js = payload.get("js") if isinstance(payload, Mapping) else None
        if raw_js is True or (isinstance(raw_js, str) and raw_js.casefold() == "true"):
            return payload
        self._auth_state = MAGAuthState.DO_AUTH
        raise AuthError("LOGIN_REQUIRED: portal rejected explicit do_auth credentials")

    @staticmethod
    def _classify_policy(value: object) -> str:
        """Normalize a machine-readable policy marker without retaining its body."""
        text = str(value).casefold()
        if "model" in text or "stb_type" in text:
            return "STB_MODEL_REJECTED"
        if "device" in text or "serial" in text:
            return "DEVICE_ID_REQUIRED"
        if "login" in text or "password" in text:
            return "LOGIN_REQUIRED"
        if "key" in text or "token" in text:
            return "AUTH_KEY_REQUIRED"
        if "unauthor" in text or "auth" in text or "active" in text:
            return "STB_NOT_AUTHORIZED"
        return "PROFILE_AUTH_ERROR"

    async def _send_profile_request(
        self,
        request: MAGProtocolRequest,
        *,
        params: dict[str, str | int] | None = None,
    ) -> object:
        """Execute one profile-owned handshake without mixing query and form data."""
        profile_request = request
        headers = {
            **profile_request.headers,
            **self._request_headers(),
        }
        if profile_request.method.upper() == "POST":
            headers["Content-Type"] = "application/x-www-form-urlencoded"
            return await self._conn.post(
                profile_request.endpoint,
                data=profile_request.form,
                headers=headers,
                base_url=profile_request.base_url,
            )
        return await self._conn.get(
            profile_request.endpoint,
            params=params if params is not None else profile_request.params,
            headers=headers,
            base_url=profile_request.base_url,
        )

    async def refresh(self) -> None:
        """Refresh the token through the same selected protocol profile."""
        try:
            request = self._profile.build_request(self._creds.portal_url, MAGOperation.HANDSHAKE)
            params = dict(request.params)
            if self._creds.token and "token" in params:
                params["token"] = self._creds.token
            payload = await self._send_profile_request(request, params=params)
            self._store_token(payload)
            try:
                await self._run_post_handshake_stages()
            except (AuthError, NetworkError):
                self._invalidate_session()
                raise
            self._auth_state = MAGAuthState.SESSION_VALIDATED
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

    def _invalidate_session(self) -> None:
        """Clear token state after a required authentication stage fails."""
        self._creds.token = ""
        self._token_expires_at = 0.0

    def _store_token(self, payload: object) -> None:
        handshake = self._profile.parse_handshake(payload)
        self._creds.token = handshake.token
        self._token_expires_at = time.monotonic() + handshake.ttl_seconds
        log.debug("MAG token stored (TTL=%ds)", handshake.ttl_seconds)

    def get_headers(self) -> dict[str, str]:
        """Return current auth headers for compatibility with older callers."""
        return self._request_headers()
