"""Provider metadata DTOs."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

__all__ = [
    "ProviderCapabilities",
    "ProviderHealth",
    "ProviderHealthStatus",
    "ProviderMetadata",
]


@dataclass(frozen=True)
class ProviderCapabilities:
    """Advertises which features a provider supports."""

    live_tv: bool = False
    vod_movies: bool = False
    vod_series: bool = False
    epg: bool = False
    timeshift: bool = False
    catchup: bool = False


@dataclass(frozen=True)
class ProviderHealthStatus(StrEnum):
    """Conservative, credential-free provider health states."""

    CONNECTED = "connected"
    AUTHENTICATION_FAILED = "authentication_failed"
    SERVER_UNAVAILABLE = "server_unavailable"
    TIMEOUT = "timeout"
    NO_CONTENT = "no_content"
    PARTIAL = "partial"
    UNKNOWN = "unknown"
    CHECKING = "checking"


@dataclass(frozen=True)
class ProviderHealth:
    """Safe health snapshot with unknown content fields when not probed."""

    provider_id: str
    protocol: str
    status: ProviderHealthStatus = ProviderHealthStatus.UNKNOWN
    authentication_status: bool | None = None
    last_checked: str | None = None
    response_time_ms: float | None = None
    live_available: bool | None = None
    vod_available: bool | None = None
    series_available: bool | None = None
    epg_available: bool | None = None
    message: str | None = None


@dataclass(frozen=True)
class ProviderMetadata:
    """Summary of a registered provider, safe to pass to the presentation layer."""

    id: str
    name: str
    type: str
    base_url: str
    is_active: bool
    capabilities: ProviderCapabilities = field(default_factory=ProviderCapabilities)
    health: ProviderHealth | None = None
