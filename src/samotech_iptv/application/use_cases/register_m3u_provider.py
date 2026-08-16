"""Secure manual M3U provider-profile registration use case."""

from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.application.dtos.provider_registration import RegisterXtreamProviderResponse
from samotech_iptv.core.error_taxonomy import safe_user_message
from samotech_iptv.core.logging import get_logger

if TYPE_CHECKING:
    from samotech_iptv.application.dtos.provider_registration import RegisterM3UProviderRequest
    from samotech_iptv.application.ports.provider_registration_port import ProviderRegistrationPort

__all__ = ["RegisterM3UProvider"]

_LOG = get_logger(__name__)


class RegisterM3UProvider:
    """Register one manual M3U profile through the secure registration port."""

    def __init__(self, registration: ProviderRegistrationPort) -> None:
        self._registration = registration

    async def execute(self, request: RegisterM3UProviderRequest) -> RegisterXtreamProviderResponse:
        """Register a playlist source without logging sensitive URL material."""
        try:
            provider_id = await self._registration.register_m3u(request)
        except Exception as exc:  # noqa: BLE001
            _LOG.error("M3U provider registration failed: %s", exc)
            return RegisterXtreamProviderResponse(
                error=safe_user_message(exc, fallback="Unable to register M3U provider")
            )
        return RegisterXtreamProviderResponse(provider_id=provider_id)
