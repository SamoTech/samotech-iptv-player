"""Provider profile-registration contract for manual entry flows."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from samotech_iptv.application.dtos.provider_registration import (
        RegisterM3UProviderRequest,
        RegisterMAGProviderRequest,
        RegisterXtreamProviderRequest,
    )

__all__ = ["ProviderRegistrationPort"]


class ProviderRegistrationPort(ABC):
    """Register provider metadata and credentials through a secure composition boundary."""

    @abstractmethod
    async def register_mag(self, request: RegisterMAGProviderRequest) -> str:
        """Register an authorized MAG/Stalker profile and secure device identity."""
        ...

    @abstractmethod
    async def register_m3u(self, request: RegisterM3UProviderRequest) -> str:
        """Register an M3U profile and protect tokenized source URLs."""
        ...

    @abstractmethod
    async def register_xtream(self, request: RegisterXtreamProviderRequest) -> str:
        """Register an Xtream profile and persist its credential securely."""
        ...
