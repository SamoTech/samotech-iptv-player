"""ISP capability interfaces — fine-grained provider contracts.

Interface Segregation Principle applied to provider capabilities.
A provider implements only the interfaces matching its feature set.

Capability matrix (planned):

  Capability             MAG   Xtream   M3U   Future
  AuthenticationProvider  ✓      ✓       ✗      ?
  SessionProvider         ✓      ✓       ✗      ?
  CatalogProvider         ✓      ✓       ✓      ?
  EPGProvider             ✓      ✓       ✗      ?
  SearchProvider          ✓      ✓       ✗      ?
  PlaybackProvider        ✓      ✓       ✓      ?
  CapabilityProvider      ✓      ✓       ✓      ?
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from samotech_iptv.application.dtos.playback import ResolvedPlayback
    from samotech_iptv.domain.entities.category import Category
    from samotech_iptv.domain.entities.channel import Channel
    from samotech_iptv.domain.entities.epg_entry import EPGEntry
    from samotech_iptv.domain.entities.episode import Episode
    from samotech_iptv.domain.entities.movie import Movie
    from samotech_iptv.domain.entities.season import Season
    from samotech_iptv.domain.entities.series import Series
    from samotech_iptv.domain.value_objects.channel_id import ChannelId
    from samotech_iptv.domain.value_objects.credential import Credential
    from samotech_iptv.domain.value_objects.provider_capability import ProviderCapability
    from samotech_iptv.domain.value_objects.provider_id import ProviderId

__all__ = [
    "AuthenticationProvider",
    "CatalogProvider",
    "CategoryProvider",
    "VodProvider",
    "MovieDetailProvider",
    "SeriesProvider",
    "MoviePlaybackProvider",
    "SeriesDetailProvider",
    "EpisodePlaybackProvider",
    "EPGProvider",
    "SearchProvider",
    "PlaybackProvider",
    "SessionProvider",
    "CapabilityProvider",
]


class AuthenticationProvider(ABC):
    """Capability: authenticate with a remote service using credentials."""

    @abstractmethod
    async def authenticate(self, credential: Credential) -> bool:
        """Authenticate and return True on success."""
        ...

    @property
    @abstractmethod
    def is_authenticated(self) -> bool:
        """True if a valid session is currently held."""
        ...

    @property
    @abstractmethod
    def provider_id(self) -> ProviderId:
        """Stable identity of this provider instance."""
        ...


class SessionProvider(ABC):
    """Capability: maintain and refresh a session token."""

    @abstractmethod
    async def refresh_session(self) -> bool:
        """Refresh the current session.  Return True on success."""
        ...


class CatalogProvider(ABC):
    """Capability: load channel catalogue from a remote service."""

    @abstractmethod
    async def load_channels(self) -> Sequence[Channel]:
        """Return the full channel list."""
        ...


class CategoryProvider(ABC):
    """Capability: load provider category families without cross-family identifier collisions."""

    @abstractmethod
    async def load_live_categories(self) -> Sequence[Category]:
        """Return categories used to group the provider's live channels."""
        ...

    @abstractmethod
    async def load_vod_categories(self) -> Sequence[Category]:
        """Return categories used to group the provider's VOD movies."""
        ...

    @abstractmethod
    async def load_series_categories(self) -> Sequence[Category]:
        """Return categories used to group the provider's series catalogue."""
        ...


class VodProvider(ABC):
    """Capability: load a provider's VOD movie catalogue."""

    @abstractmethod
    async def load_movies(self) -> Sequence[Movie]:
        """Return the full movie catalogue available to this provider."""
        ...


class MovieDetailProvider(ABC):
    """Capability: load one canonical VOD detail record."""

    @abstractmethod
    async def load_movie_details(self, movie_id: str) -> Movie:
        """Return provider-owned movie metadata without resolving playback."""
        ...


class SeriesProvider(ABC):
    """Capability: load a provider's VOD series catalogue."""

    @abstractmethod
    async def load_series(self) -> Sequence[Series]:
        """Return the full series catalogue available to this provider."""
        ...


class MoviePlaybackProvider(ABC):
    """Capability: resolve one canonical movie only at the provider-to-player boundary."""

    @abstractmethod
    async def resolve_movie_stream(self, movie_id: str, resource_id: str) -> ResolvedPlayback:
        """Return a playable URL for a validated opaque movie identity."""
        ...


class SeriesDetailProvider(ABC):
    """Capability: discover canonical seasons and episodes for one series."""

    @abstractmethod
    async def load_seasons(self, series_id: str) -> Sequence[Season]:
        """Return provider-scoped seasons for the requested canonical series."""
        ...

    @abstractmethod
    async def load_episodes(self, series_id: str, season_number: int) -> Sequence[Episode]:
        """Return canonical episodes for one requested series season."""
        ...


class EpisodePlaybackProvider(ABC):
    """Capability: resolve one canonical episode only at the provider-to-player boundary."""

    @abstractmethod
    async def resolve_episode_stream(self, episode_id: str, resource_id: str) -> ResolvedPlayback:
        """Return a playable URL for a validated opaque episode identity."""
        ...


class EPGProvider(ABC):
    """Capability: load Electronic Programme Guide data."""

    @abstractmethod
    async def load_epg(self, channel_id: ChannelId) -> Sequence[EPGEntry]:
        """Return EPG entries for a given channel."""
        ...


class SearchProvider(ABC):
    """Capability: search channels or VOD by keyword.

    Optional capability — providers that do not support server-side
    search omit this interface; the application falls back to
    ``ChannelRepository.search`` (local index).
    """

    @abstractmethod
    async def search_channels(self, query: str, limit: int = 100) -> Sequence[Channel]:
        """Search channels by keyword.  Limit is a hint only."""
        ...


class PlaybackProvider(ABC):
    """Capability: resolve a playable stream URL for a channel."""

    @abstractmethod
    async def resolve_stream(self, channel_id: ChannelId) -> ResolvedPlayback:
        """Return a playable URL for the given channel."""
        ...


class CapabilityProvider(ABC):
    """Capability: advertise which capabilities this provider supports.

    Implementing this interface allows the application to adapt its
    behaviour at runtime without isinstance checks.
    """

    @abstractmethod
    def supported_capabilities(self) -> frozenset[ProviderCapability]:
        """Return the canonical capabilities this provider implements at runtime."""
        ...
