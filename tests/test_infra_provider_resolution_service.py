from __future__ import annotations

import pytest

from samotech_iptv.application.ports.provider_capabilities import CatalogProvider
from samotech_iptv.core.exceptions import ProviderError
from samotech_iptv.domain.entities.channel import Channel
from samotech_iptv.domain.value_objects.channel_id import ChannelId
from samotech_iptv.domain.value_objects.provider_id import ProviderId
from samotech_iptv.domain.value_objects.stream_id import StreamId
from samotech_iptv.infrastructure.providers.provider_factory import ProviderFactory
from samotech_iptv.infrastructure.providers.provider_metadata import (
    InfraProviderMetadata,
)
from samotech_iptv.infrastructure.providers.provider_registry import ProviderRegistry
from samotech_iptv.infrastructure.providers.provider_resolution_service import (
    ProviderResolutionService,
)


class FakeCatalogProvider(CatalogProvider):
    """Catalogue-capable adapter double returned by the provider factory."""

    async def load_channels(self) -> list[Channel]:
        return [
            Channel(
                id=ChannelId("channel-1"),
                provider_id=ProviderId("m3u-demo"),
                stream_id=StreamId("stream-1"),
                name="Demo Channel",
            )
        ]


def test_resolver_builds_catalogue_provider_with_shared_context() -> None:
    registry = ProviderRegistry()
    registry.register(
        InfraProviderMetadata(
            provider_id="m3u-demo",
            provider_type="m3u",
            base_url="https://example.invalid/playlist.m3u",
        )
    )
    factory = ProviderFactory()
    context = object()
    provider = FakeCatalogProvider()
    received_contexts: list[object] = []

    def build_provider(_: InfraProviderMetadata, *, context: object) -> FakeCatalogProvider:
        received_contexts.append(context)
        return provider

    factory.register_type("m3u", build_provider)

    result = ProviderResolutionService(  # type: ignore[arg-type]
        registry,
        factory,
        context,
    ).resolve_catalog_provider("m3u-demo")

    assert result is provider
    assert received_contexts == [context]


def test_resolver_rejects_provider_without_catalogue_capability() -> None:
    registry = ProviderRegistry()
    registry.register(
        InfraProviderMetadata(
            provider_id="unsupported",
            provider_type="unsupported",
            base_url="https://example.invalid",
        )
    )
    factory = ProviderFactory()
    factory.register_type("unsupported", lambda _, **__: object())

    resolver = ProviderResolutionService(  # type: ignore[arg-type]
        registry,
        factory,
        object(),
    )

    with pytest.raises(ProviderError, match="does not support channel browsing"):
        resolver.resolve_catalog_provider("unsupported")
