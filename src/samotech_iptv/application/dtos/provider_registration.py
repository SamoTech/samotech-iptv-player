"""Provider-registration DTOs for manual entry flows."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "RegisterMAGProviderRequest",
    "RegisterM3UProviderRequest",
    "RegisterXtreamProviderRequest",
    "ProviderLifecycleResponse",
    "RegisterXtreamProviderResponse",
    "UpdateProviderRequest",
]


@dataclass(frozen=True)
class RegisterMAGProviderRequest:
    """Ephemeral MAG portal and device identity input; never serialize or log the MAC address."""

    provider_id: str
    portal_url: str
    mac_address: str


@dataclass(frozen=True)
class RegisterM3UProviderRequest:
    """Ephemeral M3U source input; tokenized source URLs must never be serialized or logged."""

    provider_id: str
    source: str


@dataclass(frozen=True)
class RegisterXtreamProviderRequest:
    """Ephemeral manual Xtream profile input; never serialize or log the password."""

    provider_id: str
    base_url: str
    username: str
    password: str


@dataclass(frozen=True)
class UpdateProviderRequest:
    """Ephemeral provider-edit input; ``None`` retains the existing field or credential.

    The provider type is derived from the registered profile rather than accepted from
    presentation. Credentials must never be serialized, logged, or prefilled in a dialog.
    """

    provider_id: str
    base_url: str | None = None
    source: str | None = None
    username: str | None = None
    password: str | None = None
    mac_address: str | None = None


@dataclass(frozen=True)
class ProviderLifecycleResponse:
    """Safe result returned after an update or removal operation."""

    provider_id: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class RegisterXtreamProviderResponse:
    """Safe result returned to presentation after profile registration."""

    provider_id: str | None = None
    error: str | None = None
