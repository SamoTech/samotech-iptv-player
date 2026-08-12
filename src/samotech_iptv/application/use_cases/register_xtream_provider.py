"""Secure manual Xtream provider-profile registration use case."""

from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.application.dtos.provider_registration import (
    RegisterXtreamProviderResponse,
)
from samotech_iptv.core.logging import get_logger

if TYPE_CHECKING:
    from samotech_iptv.application.dtos.provider_registration import (
        RegisterXtreamProviderRequest,
    )
    from samotech_iptv.application.ports.provider_registration_port import (
        ProviderRegistrationPort,
    )

__all__ = ["RegisterXtreamProvider"]

_LOG = get_logger(__name__)


class RegisterXtreamProvider:
    """Register one manual Xtream profile through a credential-safe port."""

    def __init__(self, registration: ProviderRegistrationPort) -> None:
        self._registration = registration

    async def execute(
        self, request: RegisterXtreamProviderRequest
    ) -> RegisterXtreamProviderResponse:
        """Register safe metadata and a credential without logging the secret."""
        try:
            provider_id = await self._registration.register_xtream(request)
        except Exception as exc:  # noqa: BLE001
            _LOG.error("Xtream provider registration failed: %s", exc)
            return RegisterXtreamProviderResponse(error=str(exc))
        return RegisterXtreamProviderResponse(provider_id=provider_id)
