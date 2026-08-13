"""Evidence-based MAG/Stalker protocol request profiles.

Profiles own endpoint construction, query parameters, protocol headers, and
handshake-response interpretation.  The application-facing MAG adapter remains
responsible for secure credential ownership and session lifecycle.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from urllib.parse import urlsplit, urlunsplit

from ..base.errors import AuthError
from .constants import DEFAULT_TOKEN_TTL_S, ENDPOINT_HANDSHAKE

__all__ = [
    "LegacyMAGProtocolProfile",
    "MAGHandshake",
    "MAGOperation",
    "MAGProtocolProfile",
    "MAGProtocolRequest",
    "StalkerQueryProtocolProfile",
]


class MAGOperation(StrEnum):
    """Protocol operations supported by the legacy live-TV boundary."""

    HANDSHAKE = "handshake"
    ACCOUNT_INFO = "account_info"
    CHANNELS = "channels"
    EPG = "epg"
    VOD = "vod"
    SERIES = "series"
    CREATE_LIVE_LINK = "create_live_link"
    CREATE_VOD_LINK = "create_vod_link"


@dataclass(frozen=True)
class MAGProtocolRequest:
    """A fully constructed protocol request without any credential value."""

    base_url: str
    endpoint: str
    params: dict[str, str | int]
    headers: dict[str, str]


@dataclass(frozen=True)
class MAGHandshake:
    """Private handshake details returned only to the session manager."""

    token: str
    ttl_seconds: int


@dataclass(frozen=True)
class MAGProtocolProfile:
    """Describe protocol-owned request construction and handshake semantics.

    ``use_origin_base`` allows a profile to construct a request from the portal
    origin rather than an application-configured path such as ``/c/``.  This is
    used only by the bounded discovery candidates; it never accepts a path from
    an untrusted response.
    """

    name: str
    handshake_endpoint: str = ENDPOINT_HANDSHAKE
    use_origin_base: bool = False
    handshake_params: Mapping[str, str] = field(default_factory=dict)
    user_agent: str | None = None
    referer_suffix: str | None = None

    def request_base_url(self, portal_url: str) -> str:
        """Return the safe base URL selected by this profile."""
        if not self.use_origin_base:
            return portal_url
        parsed = urlsplit(portal_url)
        return urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))

    def protocol_headers(self, portal_url: str) -> dict[str, str]:
        """Return profile-specific headers without device identity or tokens."""
        headers: dict[str, str] = {}
        if self.user_agent:
            headers["X-User-Agent"] = self.user_agent
        if self.referer_suffix:
            parsed = urlsplit(portal_url)
            origin = urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))
            headers["Referer"] = f"{origin}{self.referer_suffix}"
        return headers

    def operation_params(self, operation: MAGOperation) -> dict[str, str | int]:
        """Return fixed protocol parameters for one supported operation."""
        if operation is MAGOperation.HANDSHAKE:
            return dict(self.handshake_params)
        if operation is MAGOperation.ACCOUNT_INFO:
            return {"type": "account_info", "action": "get_main_info"}
        if operation is MAGOperation.CHANNELS:
            return {"type": "itv", "action": "get_all_channels"}
        if operation is MAGOperation.EPG:
            return {"type": "epg", "action": "get_simple_data_table"}
        if operation is MAGOperation.VOD:
            return {"type": "vod", "action": "get_ordered_list"}
        if operation is MAGOperation.SERIES:
            return {"type": "series", "action": "get_ordered_list"}
        if operation is MAGOperation.CREATE_LIVE_LINK:
            return {"type": "itv", "action": "create_link"}
        if operation is MAGOperation.CREATE_VOD_LINK:
            return {"type": "vod", "action": "create_link"}
        raise ValueError(f"Unsupported MAG operation: {operation!r}")

    def build_request(
        self,
        portal_url: str,
        operation: MAGOperation,
        *,
        params: Mapping[str, str | int] | None = None,
    ) -> MAGProtocolRequest:
        """Construct one request using only this profile's fixed endpoint family."""
        request_params = self.operation_params(operation)
        if params:
            request_params.update(params)
        return MAGProtocolRequest(
            base_url=self.request_base_url(portal_url),
            endpoint=self.handshake_endpoint,
            params=request_params,
            headers=self.protocol_headers(portal_url),
        )

    def handshake_request(self, portal_url: str) -> tuple[str, dict[str, str], dict[str, str]]:
        """Return the legacy handshake tuple retained for profile compatibility."""
        request = self.build_request(portal_url, MAGOperation.HANDSHAKE)
        return (
            request.endpoint,
            {key: str(value) for key, value in request.params.items()},
            request.headers,
        )

    def parse_handshake(self, payload: object) -> MAGHandshake:
        """Validate and extract a token without exposing it outside session state."""
        if not isinstance(payload, Mapping):
            raise AuthError("Portal handshake response did not contain a JSON object")
        raw_js = payload.get("js", {})
        js = raw_js if isinstance(raw_js, Mapping) else {}
        token = js.get("token") or payload.get("token")
        if not token:
            raise AuthError(
                "Portal handshake response did not contain a token. "
                "Check that your credentials are correct and that you are authorised "
                "to access this portal."
            )
        raw_ttl = js.get("token_TTL")
        try:
            ttl = int(str(raw_ttl)) if raw_ttl else DEFAULT_TOKEN_TTL_S
        except ValueError as exc:
            raise AuthError("Portal handshake response contained an invalid token TTL") from exc
        return MAGHandshake(token=str(token), ttl_seconds=ttl)

    def classify_handshake(self, payload: object) -> tuple[str, bool]:
        """Classify JSON response structure while never returning a token value."""
        try:
            self.parse_handshake(payload)
        except AuthError:
            if isinstance(payload, Mapping):
                raw_js = payload.get("js")
                if isinstance(raw_js, Mapping) or "token" in payload:
                    return "JSON_WITHOUT_TOKEN", False
            return "UNKNOWN_PROTOCOL", False
        return "VALID_STALKER_HANDSHAKE", True


@dataclass(frozen=True)
class LegacyMAGProtocolProfile(MAGProtocolProfile):
    """Bare configured-base ``/server/load.php`` legacy profile."""

    name: str = "legacy"


@dataclass(frozen=True)
class StalkerQueryProtocolProfile(MAGProtocolProfile):
    """Observed Stalker query/header handshake variant.

    The default instance remains opt-in.  Bounded discovery may instantiate this
    profile with one of its fixed, approved endpoint families.
    """

    name: str = "stalker_query"
    handshake_params: Mapping[str, str] = field(
        default_factory=lambda: {
            "type": "stb",
            "action": "handshake",
            "token": "",
            "JsHttpRequest": "1-xml",
        }
    )
    user_agent: str | None = "Model: MAG254; Link: WiFi"
    referer_suffix: str | None = "/c/"
