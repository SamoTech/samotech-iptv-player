"""Provider-registration DTOs for manual entry flows."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["RegisterXtreamProviderRequest", "RegisterXtreamProviderResponse"]


@dataclass(frozen=True)
class RegisterXtreamProviderRequest:
    """Ephemeral manual Xtream profile input; never serialize or log the password."""

    provider_id: str
    base_url: str
    username: str
    password: str


@dataclass(frozen=True)
class RegisterXtreamProviderResponse:
    """Safe result returned to presentation after profile registration."""

    provider_id: str | None = None
    error: str | None = None
