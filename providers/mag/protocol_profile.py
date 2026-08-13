"""Evidence-based MAG/Stalker protocol request profiles.

Profiles own endpoint construction, protocol headers, safe cookie construction, and
operation parameters.  The application-facing adapter retains credential ownership
and session lifecycle; no profile exposes a token or device identity in diagnostics.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from urllib.parse import quote, urlsplit, urlunsplit

from ..base.errors import AuthError
from .constants import DEFAULT_TOKEN_TTL_S, ENDPOINT_HANDSHAKE, USER_AGENT

__all__ = [
    "LegacyMAGProtocolProfile",
    "MAGAuthMode",
    "MAGAuthState",
    "MAGHandshake",
    "MAGOperation",
    "MAGProtocolProfile",
    "MAGProtocolRequest",
    "StalkerClientCompatibilityProfile",
    "StalkerHelperCompatibilityProfile",
    "StalkerQueryProtocolProfile",
]


class MAGAuthMode(StrEnum):
    """Explicit MAG authentication modes; no mode is inferred."""

    MAC_ONLY = "mac_only"
    MAC_PLUS_LOGIN = "mac_plus_login"
    AUTHORIZATION_KEY = "authorization_key"


class MAGAuthState(StrEnum):
    """Private authentication state-machine stages."""

    DISCOVERY = "discovery"
    HANDSHAKE = "handshake"
    TOKEN_RECEIVED = "token_received"  # noqa: S105
    PROFILE_REQUIRED = "profile_required"
    GET_PROFILE = "get_profile"
    DO_AUTH = "do_auth"
    SESSION_VALIDATED = "session_validated"
    CATALOGUE = "catalogue"


class MAGOperation(StrEnum):
    """Protocol operations supported by the MAG live-TV boundary."""

    HANDSHAKE = "handshake"
    GET_PROFILE = "get_profile"
    DO_AUTH = "do_auth"
    ACCOUNT_INFO = "account_info"
    CHANNELS = "channels"
    LIVE_GENRES = "live_genres"
    LIVE_ORDERED_LIST = "live_ordered_list"
    EPG = "epg"
    VOD = "vod"
    SERIES = "series"
    CREATE_LIVE_LINK = "create_live_link"
    CREATE_VOD_LINK = "create_vod_link"


@dataclass(frozen=True)
class MAGProtocolRequest:
    """A fully constructed protocol request without credential values."""

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
    """Describe profile-owned request construction and handshake semantics.

    ``use_origin_base`` permits only a profile's fixed endpoint family to use a
    portal origin instead of a configured application path.  It never accepts a
    path supplied by a response.  ``user_agent`` preserves the historic field
    name for the ``X-User-Agent`` header; ``http_user_agent`` controls the actual
    HTTP ``User-Agent`` header.
    """

    name: str
    handshake_endpoint: str = ENDPOINT_HANDSHAKE
    use_origin_base: bool = False
    handshake_params: Mapping[str, str] = field(default_factory=dict)
    http_user_agent: str | None = None
    user_agent: str | None = None
    model_x_user_agent: bool = False
    model_link: str = "WiFi"
    referer_suffix: str | None = None
    extra_headers: Mapping[str, str] = field(default_factory=dict)
    uses_stalker_cookies: bool = False
    quote_mac_cookie: bool = True
    cookie_language: str = "en"
    cookie_timezone: str = "Europe/Paris"
    uses_ordered_live_catalogue: bool = False
    ordered_live_start_page: int = 0
    uses_channel_command_for_live_link: bool = False

    def request_base_url(self, portal_url: str) -> str:
        """Return the safe base URL selected by this fixed profile."""
        if not self.use_origin_base:
            return portal_url
        parsed = urlsplit(portal_url)
        return urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))

    def protocol_headers(self, portal_url: str) -> dict[str, str]:
        """Return fixed profile headers without identity, cookies, or tokens."""
        headers: dict[str, str] = {}
        if self.http_user_agent:
            headers["User-Agent"] = self.http_user_agent
        if self.user_agent:
            headers["X-User-Agent"] = self.user_agent
        if self.referer_suffix:
            parsed = urlsplit(portal_url)
            origin = urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))
            headers["Referer"] = f"{origin}{self.referer_suffix}"
        headers.update(self.extra_headers)
        return headers

    def request_headers(
        self,
        portal_url: str,
        *,
        mac_address: str,
        serial_number: str,
        device_id: str,
        device_id2: str,
        token: str,
        mag_model: str = "",
    ) -> dict[str, str]:
        """Build one private request-header set without logging sensitive values."""
        headers = self.protocol_headers(portal_url)
        if self.model_x_user_agent and mag_model.strip():
            headers["X-User-Agent"] = f"Model: {mag_model.strip()}; Link: {self.model_link}"
        if self.uses_stalker_cookies:
            encoded_mac = (
                quote(mac_address.strip()) if self.quote_mac_cookie else mac_address.strip()
            )
            cookies = {
                "mac": encoded_mac,
                "stb_lang": quote(self.cookie_language),
                "timezone": quote(self.cookie_timezone),
            }
            if token:
                cookies["token"] = quote(token)
                headers["Authorization"] = f"Bearer {token}"
            headers["Cookie"] = "; ".join(f"{key}={value}" for key, value in cookies.items())
            return headers

        if token:
            headers["Authorization"] = f"Bearer {token}"
        if mac_address:
            headers["X-User-Mac"] = mac_address
        if serial_number:
            headers["X-Device-Serial"] = serial_number
        if device_id:
            headers["X-Device-ID"] = device_id
        if device_id2:
            headers["X-Device-ID2"] = device_id2
        return headers

    def operation_params(self, operation: MAGOperation) -> dict[str, str | int]:
        """Return fixed protocol parameters for one supported operation."""
        if operation is MAGOperation.HANDSHAKE:
            return dict(self.handshake_params)
        if operation is MAGOperation.GET_PROFILE:
            return {"type": "stb", "action": "get_profile", "JsHttpRequest": "1-xml"}
        if operation is MAGOperation.DO_AUTH:
            return {"type": "stb", "action": "do_auth", "JsHttpRequest": "1-xml"}
        if operation is MAGOperation.ACCOUNT_INFO:
            return {"type": "account_info", "action": "get_main_info"}
        if operation is MAGOperation.CHANNELS:
            return {"type": "itv", "action": "get_all_channels"}
        if operation is MAGOperation.LIVE_GENRES:
            return {"type": "itv", "action": "get_genres", "JsHttpRequest": "1-xml"}
        if operation is MAGOperation.LIVE_ORDERED_LIST:
            return {"type": "itv", "action": "get_ordered_list", "JsHttpRequest": "1-xml"}
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

    def profile_params(
        self,
        *,
        serial_number: str = "",
        device_id: str = "",
        device_id2: str = "",
        mag_model: str = "",
        signature: str = "",
    ) -> dict[str, str | int]:
        """Build minimal get_profile params plus only explicitly supplied identity."""
        params = self.operation_params(MAGOperation.GET_PROFILE)
        if serial_number:
            params["sn"] = serial_number
        if device_id:
            params["device_id"] = device_id
        if device_id2:
            params["device_id2"] = device_id2
        if mag_model:
            params["stb_type"] = mag_model
        if signature:
            params["signature"] = signature
        return params

    def do_auth_params(
        self,
        *,
        login: str,
        password: str,
        device_id: str = "",
        device_id2: str = "",
        signature: str = "",
    ) -> dict[str, str | int]:
        """Build the source-observed login form without logging its values."""
        params = self.operation_params(MAGOperation.DO_AUTH)
        params.update({"login": login, "password": password})
        if device_id:
            params["device_id"] = device_id
        if device_id2:
            params["device_id2"] = device_id2
        if signature:
            params["signature"] = signature
        return params

    def live_link_params(self, command: str) -> dict[str, str | int]:
        """Build profile-owned live ``create_link`` parameters from a private command."""
        params: dict[str, str | int] = {"cmd": command, "JsHttpRequest": "1-xml"}
        if not self.uses_channel_command_for_live_link:
            params.update({"forced_storage": "undefined", "disable_ad": "0"})
        return params

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
    """Observed Stalker query/header handshake variant used by bounded discovery."""

    name: str = "stalker_query"
    handshake_params: Mapping[str, str] = field(
        default_factory=lambda: {
            "type": "stb",
            "action": "handshake",
            "token": "",
            "JsHttpRequest": "1-xml",
        }
    )
    model_x_user_agent: bool = True
    referer_suffix: str | None = "/c/"


@dataclass(frozen=True)
class StalkerClientCompatibilityProfile(MAGProtocolProfile):
    """Exact observed GUI ``portal.php`` request profile.

    The GUI source sends the MAG200 User-Agent and pre-authentication MAC/language/
    London-timezone cookies but does not send an empty ``token`` parameter,
    X-User-Agent, Referer, or the helper-only browser-style headers. Model-dependent
    X-User-Agent values are never inferred by this implementation.
    """

    name: str = "stalker_gui_compatibility"
    handshake_endpoint: str = "portal.php"
    use_origin_base: bool = True
    handshake_params: Mapping[str, str] = field(
        default_factory=lambda: {
            "type": "stb",
            "action": "handshake",
            "JsHttpRequest": "1-xml",
        }
    )
    http_user_agent: str | None = USER_AGENT
    quote_mac_cookie: bool = False
    cookie_timezone: str = "Europe/London"
    uses_stalker_cookies: bool = True
    uses_ordered_live_catalogue: bool = True
    uses_channel_command_for_live_link: bool = True


@dataclass(frozen=True)
class StalkerHelperCompatibilityProfile(MAGProtocolProfile):
    """Exact observed helper ``stalker_portal/server/load.php`` profile.

    This profile deliberately omits the helper's unverified random-token/prehash
    retry and never fabricates serial, device identity, or model values. Its
    model-dependent X-User-Agent is emitted only when ``mag_model`` is explicitly
    supplied by authorized configuration.
    """

    name: str = "stalker_helper_compatibility"
    handshake_endpoint: str = "stalker_portal/server/load.php"
    use_origin_base: bool = True
    handshake_params: Mapping[str, str] = field(
        default_factory=lambda: {
            "type": "stb",
            "action": "handshake",
            "token": "",
            "JsHttpRequest": "1-xml",
        }
    )
    http_user_agent: str | None = USER_AGENT
    model_x_user_agent: bool = True
    referer_suffix: str | None = "/stalker_portal/c/index.html"
    extra_headers: Mapping[str, str] = field(
        default_factory=lambda: {
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Pragma": "no-cache",
            "Connection": "Close",
            "Accept-Encoding": "gzip, deflate",
        }
    )
    uses_stalker_cookies: bool = True
    uses_ordered_live_catalogue: bool = True
    ordered_live_start_page: int = 1
    uses_channel_command_for_live_link: bool = True
