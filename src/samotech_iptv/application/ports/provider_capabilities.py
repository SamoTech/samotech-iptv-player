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

    from samotech_iptv.domain.entities.channel import Channel
    from samotech_iptv.domain.entities.epg_entry import EPGEntry
    from samotech_iptv.domain.value_objects.channel_id import ChannelId
    from samotech_iptv.domain.value_objects.credential import Credential
    from samotech_iptv.domain.value_objects.provider_capability import ProviderCapability
    from samotech_iptv.domain.value_objects.provider_id import ProviderId
    from samotech_iptv.domain.value_objects.url import URL

__all__ = [
    "AuthenticationProvider",
    "CatalogProvider",
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
    async def resolve_stream(self, channel_id: ChannelId) -> URL:
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
