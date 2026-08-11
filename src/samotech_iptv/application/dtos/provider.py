"""Provider metadata DTOs."""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = ["ProviderCapabilities", "ProviderMetadata"]


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
class ProviderMetadata:
    """Summary of a registered provider, safe to pass to the presentation layer."""

    id: str
    name: str
    type: str
    base_url: str
    is_active: bool
    capabilities: ProviderCapabilities = field(default_factory=ProviderCapabilities)
