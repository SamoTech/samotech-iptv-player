"""Credential-safe registered-provider update and removal use cases."""

from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.application.dtos.provider_registration import ProviderLifecycleResponse
from samotech_iptv.core.logging import get_logger

if TYPE_CHECKING:
    from samotech_iptv.application.dtos.provider_registration import UpdateProviderRequest
    from samotech_iptv.application.ports.provider_registration_port import ProviderRegistrationPort

__all__ = ["RemoveProvider", "UpdateProvider"]

_LOG = get_logger(__name__)


class UpdateProvider:
    """Update non-secret provider metadata and explicitly supplied credentials only."""

    def __init__(self, registration: ProviderRegistrationPort) -> None:
        self._registration = registration

    async def execute(self, request: UpdateProviderRequest) -> ProviderLifecycleResponse:
        """Delegate a provider edit without exposing failure details to presentation."""
        try:
            provider_id = await self._registration.update(request)
        except Exception:  # noqa: BLE001
            _LOG.error("Provider update failed")
            return ProviderLifecycleResponse(error="Unable to update provider")
        return ProviderLifecycleResponse(provider_id=provider_id)


class RemoveProvider:
    """Remove a provider's metadata, keyring credential, and runtime registration."""

    def __init__(self, registration: ProviderRegistrationPort) -> None:
        self._registration = registration

    async def execute(self, provider_id: str) -> ProviderLifecycleResponse:
        """Delegate removal and return only generic safe failure feedback."""
        try:
            removed_provider_id = await self._registration.remove(provider_id)
        except Exception:  # noqa: BLE001
            _LOG.error("Provider removal failed")
            return ProviderLifecycleResponse(error="Unable to remove provider")
        return ProviderLifecycleResponse(provider_id=removed_provider_id)
