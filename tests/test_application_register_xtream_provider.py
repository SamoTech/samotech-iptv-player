"""Tests for the manual Xtream provider-registration application use case."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import pytest

from samotech_iptv.application.dtos.provider_registration import (
    RegisterXtreamProviderRequest,
)
from samotech_iptv.application.use_cases.register_xtream_provider import RegisterXtreamProvider

if TYPE_CHECKING:
    from samotech_iptv.application.ports.provider_registration_port import (
        ProviderRegistrationPort,
    )


class FakeRegistration:
    """Registration-port double that receives ephemeral input only."""

    def __init__(self) -> None:
        self.request: RegisterXtreamProviderRequest | None = None

    async def register_xtream(self, request: RegisterXtreamProviderRequest) -> str:
        self.request = request
        return request.provider_id


@pytest.mark.asyncio
async def test_register_xtream_delegates_ephemeral_request_to_secure_port() -> None:
    registration = FakeRegistration()
    use_case = RegisterXtreamProvider(cast("ProviderRegistrationPort", registration))
    request = RegisterXtreamProviderRequest(
        provider_id="demo",
        base_url="https://example.test",
        username="user",
        password="test-only-password",  # noqa: S106
    )

    response = await use_case.execute(request)

    assert response.provider_id == "demo"
    assert response.error is None
    assert registration.request == request
