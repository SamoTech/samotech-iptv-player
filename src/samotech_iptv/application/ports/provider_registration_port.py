"""Provider profile-registration contract for manual entry flows."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from samotech_iptv.application.dtos.provider_registration import (
        RegisterXtreamProviderRequest,
    )

__all__ = ["ProviderRegistrationPort"]


class ProviderRegistrationPort(ABC):
    """Register provider metadata and credentials through a secure composition boundary."""

    @abstractmethod
    async def register_xtream(self, request: RegisterXtreamProviderRequest) -> str:
        """Register an Xtream profile and persist its credential securely."""
        ...
