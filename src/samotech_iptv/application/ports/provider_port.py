"""ProviderPort — coarse-grained provider contract (backward compat).

New code should prefer the fine-grained capability interfaces in
``provider_capabilities.py``.  ``ProviderPort`` remains for the
migration window and for providers that implement all capabilities.
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
    from samotech_iptv.domain.value_objects.provider_id import ProviderId
    from samotech_iptv.domain.value_objects.url import URL

__all__ = ["ProviderPort"]


class ProviderPort(ABC):
    """Full-featured provider adapter contract.

    Providers that implement every capability (e.g. MAG) implement this
    class directly.  Partial providers (e.g. M3U) should implement only
    the specific capability interfaces from ``provider_capabilities``.
    """

    @abstractmethod
    async def authenticate(self, credential: Credential) -> bool: ...

    @abstractmethod
    async def refresh_session(self) -> bool: ...

    @abstractmethod
    async def load_channels(self) -> Sequence[Channel]: ...

    @abstractmethod
    async def resolve_stream(self, channel_id: ChannelId) -> URL: ...

    @abstractmethod
    async def load_epg(self, channel_id: ChannelId) -> Sequence[EPGEntry]: ...

    @property
    @abstractmethod
    def provider_id(self) -> ProviderId: ...

    @property
    @abstractmethod
    def is_authenticated(self) -> bool: ...
