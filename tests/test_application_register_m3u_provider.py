"""Tests for the manual M3U provider-registration application use case."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import pytest

from samotech_iptv.application.dtos.provider_registration import RegisterM3UProviderRequest
from samotech_iptv.application.use_cases.register_m3u_provider import RegisterM3UProvider

if TYPE_CHECKING:
    from samotech_iptv.application.ports.provider_registration_port import ProviderRegistrationPort


class FakeRegistration:
    """Registration-port double that receives ephemeral M3U source input only."""

    def __init__(self) -> None:
        self.request: RegisterM3UProviderRequest | None = None

    async def register_m3u(self, request: RegisterM3UProviderRequest) -> str:
        self.request = request
        return request.provider_id


@pytest.mark.asyncio
async def test_register_m3u_delegates_ephemeral_source_to_secure_port() -> None:
    registration = FakeRegistration()
    use_case = RegisterM3UProvider(cast("ProviderRegistrationPort", registration))
    request = RegisterM3UProviderRequest(
        provider_id="demo",
        source="https://playlist.example.test/list.m3u?token=test-only-token",  # noqa: S105
    )

    response = await use_case.execute(request)

    assert response.provider_id == "demo"
    assert response.error is None
    assert registration.request == request
