"""Port interfaces — application-defined contracts for infrastructure.

Ports are abstract classes that the application layer depends on.
Infrastructure adapters implement these interfaces.
The application layer is never aware of concrete implementations.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Sequence

from samotech_iptv.domain.entities import Channel, EPGEntry, Provider
from samotech_iptv.domain.value_objects import ChannelId, Credential, ProviderId, URL

__all__ = [
    "ProviderPort",
    "PlayerPort",
    "StoragePort",
    "CredentialStorePort",
    "NotificationPort",
]


class ProviderPort(ABC):
    """Contract for a content-provider adapter.

    Infrastructure implementations (MAG, Xtream, M3U) must satisfy
    this interface.  The application layer calls only these methods.
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


class PlayerPort(ABC):
    """Contract for the media-player backend (MPV, VLC, WinRT, …)."""

    @abstractmethod
    async def play(self, url: URL) -> None: ...

    @abstractmethod
    async def stop(self) -> None: ...

    @abstractmethod
    async def pause(self) -> None: ...

    @abstractmethod
    async def resume(self) -> None: ...

    @property
    @abstractmethod
    def is_playing(self) -> bool: ...


class StoragePort(ABC):
    """Contract for the local persistence adapter (SQLite, JSON, …)."""

    @abstractmethod
    async def initialise(self) -> None: ...

    @abstractmethod
    async def close(self) -> None: ...


class CredentialStorePort(ABC):
    """Contract for secure credential storage (OS keyring, vault, …)."""

    @abstractmethod
    async def store(self, provider_id: ProviderId, credential: Credential) -> None: ...

    @abstractmethod
    async def retrieve(self, provider_id: ProviderId) -> Optional[Credential]: ...

    @abstractmethod
    async def delete(self, provider_id: ProviderId) -> bool: ...


class NotificationPort(ABC):
    """Contract for user-facing notifications (toast, tray, …)."""

    @abstractmethod
    async def info(self, title: str, message: str) -> None: ...

    @abstractmethod
    async def warning(self, title: str, message: str) -> None: ...

    @abstractmethod
    async def error(self, title: str, message: str) -> None: ...
