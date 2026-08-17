"""Secure manual MAG/Stalker provider-profile registration use case."""

from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.application.dtos.provider_registration import RegisterXtreamProviderResponse
from samotech_iptv.core.diagnostics import log_exception
from samotech_iptv.core.error_taxonomy import safe_user_message
from samotech_iptv.core.logging import get_logger

if TYPE_CHECKING:
    from samotech_iptv.application.dtos.provider_registration import RegisterMAGProviderRequest
    from samotech_iptv.application.ports.provider_registration_port import ProviderRegistrationPort

__all__ = ["RegisterMAGProvider"]

_LOG = get_logger(__name__)


class RegisterMAGProvider:
    """Register one authorized MAG/Stalker profile through the secure registration port."""

    def __init__(self, registration: ProviderRegistrationPort) -> None:
        self._registration = registration

    async def execute(self, request: RegisterMAGProviderRequest) -> RegisterXtreamProviderResponse:
        """Register portal metadata and device identity without logging the identity."""
        try:
            provider_id = await self._registration.register_mag(request)
        except Exception as exc:  # noqa: BLE001
            log_exception(_LOG, "MAG provider registration failed", exc)
            return RegisterXtreamProviderResponse(
                error=safe_user_message(exc, fallback="Unable to register MAG provider")
            )
        return RegisterXtreamProviderResponse(provider_id=provider_id)
