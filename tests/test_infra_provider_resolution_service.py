from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from samotech_iptv.application.ports.provider_capabilities import (
    CatalogProvider,
    CategoryProvider,
    EPGProvider,
    PlaybackProvider,
    SearchProvider,
)
from samotech_iptv.core.exceptions import ProviderError
from samotech_iptv.domain.entities.category import Category
from samotech_iptv.domain.entities.channel import Channel
from samotech_iptv.domain.value_objects.channel_id import ChannelId
from samotech_iptv.domain.value_objects.provider_id import ProviderId
from samotech_iptv.domain.value_objects.stream_id import StreamId
from samotech_iptv.domain.value_objects.url import URL
from samotech_iptv.infrastructure.providers.provider_factory import ProviderFactory
from samotech_iptv.infrastructure.providers.provider_metadata import (
    InfraProviderMetadata,
)
from samotech_iptv.infrastructure.providers.provider_registry import ProviderRegistry
from samotech_iptv.infrastructure.providers.provider_resolution_service import (
    ProviderResolutionService,
)

if TYPE_CHECKING:
    from samotech_iptv.domain.entities.epg_entry import EPGEntry


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


class FakeCategoryProvider(CategoryProvider):
    """Live-category-capable adapter double returned by the provider factory."""

    async def load_live_categories(self) -> list[Category]:
        return [Category(id="news", name="News", provider_id="xtream-demo")]

    async def load_vod_categories(self) -> list[Category]:
        return []

    async def load_series_categories(self) -> list[Category]:
        return []


class FakePlaybackProvider(PlaybackProvider):
    """Playback-capable adapter double returned by the provider factory."""

    async def resolve_stream(self, _: ChannelId) -> URL:
        return URL("https://example.invalid/live.m3u8")


class FakeEPGProvider(EPGProvider):
    """EPG-capable adapter double returned by the provider factory."""

    async def load_epg(self, _: ChannelId) -> list[EPGEntry]:
        return []


class FakeAllCapabilitiesProvider(
    CatalogProvider,
    CategoryProvider,
    SearchProvider,
    PlaybackProvider,
    EPGProvider,
):
    """Provider double implementing every capability resolved by the service."""

    async def load_channels(self) -> list[Channel]:
        return []

    async def load_live_categories(self) -> list[Category]:
        return []

    async def load_vod_categories(self) -> list[Category]:
        return []

    async def load_series_categories(self) -> list[Category]:
        return []

    async def search_channels(self, _: str, limit: int = 100) -> list[Channel]:
        return []

    async def resolve_stream(self, _: ChannelId) -> URL:
        return URL("https://example.invalid/live.m3u8")

    async def load_epg(self, _: ChannelId) -> list[EPGEntry]:
        return []


def test_resolver_reuses_one_provider_across_all_capabilities() -> None:
    registry = ProviderRegistry()
    registry.register(
        InfraProviderMetadata(
            provider_id="all-demo",
            provider_type="all",
            base_url="https://example.invalid",
        )
    )
    factory = ProviderFactory()
    provider = FakeAllCapabilitiesProvider()
    construction_count = 0

    def build(_: InfraProviderMetadata, **__: object) -> FakeAllCapabilitiesProvider:
        nonlocal construction_count
        construction_count += 1
        return provider

    factory.register_type("all", build)
    resolver = ProviderResolutionService(registry, factory, object())  # type: ignore[arg-type]

    resolved = [
        resolver.resolve_catalog_provider("all-demo"),
        resolver.resolve_category_provider("all-demo"),
        resolver.resolve_search_provider("all-demo"),
        resolver.resolve_playback_provider("all-demo"),
        resolver.resolve_epg_provider("all-demo"),
    ]

    assert all(item is provider for item in resolved)
    assert construction_count == 1


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


def test_resolver_builds_category_provider_with_shared_context() -> None:
    registry = ProviderRegistry()
    registry.register(
        InfraProviderMetadata(
            provider_id="xtream-demo",
            provider_type="xtream",
            base_url="https://example.invalid",
        )
    )
    factory = ProviderFactory()
    context = object()
    provider = FakeCategoryProvider()
    factory.register_type("xtream", lambda _, **__: provider)

    result = ProviderResolutionService(  # type: ignore[arg-type]
        registry,
        factory,
        context,
    ).resolve_category_provider("xtream-demo")

    assert result is provider


def test_resolver_builds_playback_provider_with_shared_context() -> None:
    registry = ProviderRegistry()
    registry.register(
        InfraProviderMetadata(
            provider_id="xtream-demo",
            provider_type="xtream",
            base_url="https://example.invalid",
        )
    )
    factory = ProviderFactory()
    context = object()
    provider = FakePlaybackProvider()
    factory.register_type("xtream", lambda _, **__: provider)

    result = ProviderResolutionService(  # type: ignore[arg-type]
        registry,
        factory,
        context,
    ).resolve_playback_provider("xtream-demo")

    assert result is provider


def test_resolver_builds_epg_provider_with_shared_context() -> None:
    registry = ProviderRegistry()
    registry.register(
        InfraProviderMetadata(
            provider_id="mag-demo",
            provider_type="mag",
            base_url="https://example.invalid",
        )
    )
    factory = ProviderFactory()
    context = object()
    provider = FakeEPGProvider()
    factory.register_type("mag", lambda _, **__: provider)

    result = ProviderResolutionService(  # type: ignore[arg-type]
        registry,
        factory,
        context,
    ).resolve_epg_provider("mag-demo")

    assert result is provider


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
    with pytest.raises(ProviderError, match="does not support category browsing"):
        resolver.resolve_category_provider("unsupported")
    with pytest.raises(ProviderError, match="does not support playback"):
        resolver.resolve_playback_provider("unsupported")
    with pytest.raises(ProviderError, match="does not support EPG"):
        resolver.resolve_epg_provider("unsupported")
