"""Tests for safe runtime capability summaries used by presentation navigation."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from samotech_iptv.application.dtos.provider import ProviderCapabilityState
from samotech_iptv.application.use_cases.load_provider_capabilities import (
    LoadProviderCapabilities,
)
from samotech_iptv.core.exceptions import ProviderError
from samotech_iptv.domain.value_objects.provider_capability import ProviderCapability

if TYPE_CHECKING:
    from samotech_iptv.application.ports.provider_content_resolver_port import (
        ProviderContentResolverPort,
    )


class FakeCapabilityProvider:
    def __init__(self, capabilities: frozenset[ProviderCapability]) -> None:
        self.capabilities = capabilities
        self.calls = 0

    def supported_capabilities(self) -> frozenset[ProviderCapability]:
        self.calls += 1
        return self.capabilities


class FakeCapabilityResolver:
    def __init__(self, provider: FakeCapabilityProvider) -> None:
        self.provider = provider
        self.provider_ids: list[str] = []

    def resolve_capability_provider(self, provider_id: str) -> FakeCapabilityProvider:
        self.provider_ids.append(provider_id)
        return self.provider


def test_load_provider_capabilities_maps_runtime_declarations_without_metadata_guesses() -> None:
    provider = FakeCapabilityProvider(
        frozenset(
            {
                ProviderCapability.LIVE,
                ProviderCapability.VOD,
                ProviderCapability.SERIES,
                ProviderCapability.EPG,
            }
        )
    )
    resolver = FakeCapabilityResolver(provider)

    result = LoadProviderCapabilities(cast("ProviderContentResolverPort", resolver)).execute(
        "xtream-demo"
    )

    assert result.live_tv is True
    assert result.vod_movies is True
    assert result.vod_series is True
    assert result.epg is True
    assert result.catchup is False
    assert result.truth.live_tv is ProviderCapabilityState.SUPPORTED
    assert result.truth.catchup is ProviderCapabilityState.NOT_SUPPORTED
    assert resolver.provider_ids == ["xtream-demo"]
    assert provider.calls == 1


def test_load_provider_capabilities_reports_no_unavailable_domains() -> None:
    class UnsupportedResolver(FakeCapabilityResolver):
        def resolve_capability_provider(self, provider_id: str) -> FakeCapabilityProvider:
            raise ProviderError("Provider does not expose capabilities")

    result = LoadProviderCapabilities(
        cast(
            "ProviderContentResolverPort",
            UnsupportedResolver(FakeCapabilityProvider(frozenset())),
        )
    ).execute("m3u-demo")

    assert result.live_tv is False
    assert result.vod_movies is False
    assert result.vod_series is False
    assert result.truth.live_tv is ProviderCapabilityState.NOT_AVAILABLE
    assert result.truth.catchup is ProviderCapabilityState.NOT_AVAILABLE
