from __future__ import annotations

from types import SimpleNamespace

from samotech_iptv.application.dtos.provider import ProviderHealthStatus
from samotech_iptv.application.use_cases.check_provider_health import (
    CheckProviderHealth,
    CheckProviderHealthRequest,
)
from samotech_iptv.domain.value_objects.provider_capability import ProviderCapability


class FakeResolver:
    def __init__(self, provider: object) -> None:
        self.provider = provider

    def resolve_capability_provider(self, provider_id: str) -> object:
        assert provider_id == "provider-1"
        return self.provider


def test_provider_health_maps_authenticated_state_and_capabilities() -> None:
    provider = SimpleNamespace(
        supported_capabilities=lambda: frozenset(
            {
                ProviderCapability.LIVE,
                ProviderCapability.VOD,
                ProviderCapability.SERIES,
                ProviderCapability.EPG,
            }
        ),
        is_authenticated=True,
    )

    response = CheckProviderHealth(FakeResolver(provider)).execute(
        CheckProviderHealthRequest("provider-1")
    )

    assert response.error is None
    assert response.health.status is ProviderHealthStatus.CONNECTED
    assert response.health.authentication_status is True
    assert response.health.live_available is True
    assert response.health.vod_available is True
    assert response.health.series_available is True
    assert response.health.epg_available is True
    assert response.health.last_checked is not None
    assert response.health.response_time_ms is not None


def test_provider_health_distinguishes_unauthenticated_from_unknown() -> None:
    unauthenticated = SimpleNamespace(
        supported_capabilities=lambda: frozenset({ProviderCapability.LIVE}),
        is_authenticated=False,
    )
    unknown = SimpleNamespace(
        supported_capabilities=lambda: frozenset({ProviderCapability.LIVE}),
    )

    failed = CheckProviderHealth(FakeResolver(unauthenticated)).execute(
        CheckProviderHealthRequest("provider-1")
    )
    unresolved = CheckProviderHealth(FakeResolver(unknown)).execute(
        CheckProviderHealthRequest("provider-1")
    )

    assert failed.health.status is ProviderHealthStatus.AUTHENTICATION_FAILED
    assert unresolved.health.status is ProviderHealthStatus.UNKNOWN


def test_provider_health_never_returns_provider_exception_text() -> None:
    class BrokenResolver:
        def resolve_capability_provider(self, provider_id: str) -> object:
            raise RuntimeError("password=never-expose")

    response = CheckProviderHealth(BrokenResolver()).execute(
        CheckProviderHealthRequest("provider-1")
    )

    assert response.health.status is ProviderHealthStatus.UNKNOWN
    assert response.error == "Provider health could not be read"
    assert "password" not in (response.health.message or "")
