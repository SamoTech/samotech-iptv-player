"""CredentialStorePort — secure credential storage contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from samotech_iptv.domain.value_objects.credential import Credential
    from samotech_iptv.domain.value_objects.provider_id import ProviderId

__all__ = ["CredentialStorePort"]


class CredentialStorePort(ABC):
    """Contract for secure credential storage (OS keyring, vault, …)."""

    @abstractmethod
    async def store(self, provider_id: ProviderId, credential: Credential) -> None: ...

    @abstractmethod
    async def retrieve(self, provider_id: ProviderId) -> Credential | None: ...

    @abstractmethod
    async def delete(self, provider_id: ProviderId) -> bool: ...
