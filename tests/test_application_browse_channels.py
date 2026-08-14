from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from samotech_iptv.application.channel_catalogue_cache import ChannelCatalogueCache
from samotech_iptv.application.dtos import ChannelDTO, LoadChannelsRequest
from samotech_iptv.application.ports.provider_capabilities import CatalogProvider

if TYPE_CHECKING:
    from samotech_iptv.application.ports.provider_capabilities import (
        CategoryProvider,
        PlaybackProvider,
    )
from samotech_iptv.application.ports.provider_resolver_port import ProviderResolverPort
from samotech_iptv.application.use_cases.browse_channels import BrowseChannels
from samotech_iptv.domain.entities.channel import Channel
from samotech_iptv.domain.value_objects.channel_id import ChannelId
from samotech_iptv.domain.value_objects.provider_id import ProviderId
from samotech_iptv.domain.value_objects.stream_id import StreamId


class FakeCatalogProvider(CatalogProvider):
    """Catalogue provider double returning one canonical channel."""

    async def load_channels(self) -> list[Channel]:
        return [
            Channel(
                id=ChannelId("channel-1"),
                provider_id=ProviderId("demo"),
                stream_id=StreamId("stream-1"),
                name="Demo Channel",
            )
        ]


class FakeResolver(ProviderResolverPort):
    """Resolver double recording the requested registered provider."""

    def __init__(self, provider: CatalogProvider | None = None) -> None:
        self._provider = provider
        self.provider_ids: list[str] = []

    def resolve_catalog_provider(self, provider_id: str) -> CatalogProvider:
        self.provider_ids.append(provider_id)
        if self._provider is None:
            raise RuntimeError("Provider is unavailable")
        return self._provider

    def resolve_category_provider(self, provider_id: str) -> CategoryProvider:
        raise AssertionError(f"Unexpected category resolution for {provider_id}")

    def resolve_playback_provider(self, provider_id: str) -> PlaybackProvider:
        raise AssertionError(f"Unexpected playback resolution for {provider_id}")

    def resolve_search_provider(self, provider_id: str) -> object:
        raise AssertionError(f"Unexpected search resolution for {provider_id}")

    def resolve_epg_provider(self, provider_id: str) -> object:
        raise AssertionError(f"Unexpected EPG resolution for {provider_id}")


@pytest.mark.asyncio
async def test_browse_channels_resolves_provider_then_returns_channel_dtos() -> None:
    resolver = FakeResolver(FakeCatalogProvider())

    response = await BrowseChannels(resolver).execute(LoadChannelsRequest(provider_id="demo"))

    assert resolver.provider_ids == ["demo"]
    assert response.error is None
    assert response.total == 1
    assert response.channels[0].name == "Demo Channel"
    assert response.channels[0].stream_id == "stream-1"


@pytest.mark.asyncio
async def test_browse_channels_replaces_complete_catalogue_cache() -> None:
    resolver = FakeResolver(FakeCatalogProvider())
    cache = ChannelCatalogueCache()

    response = await BrowseChannels(resolver, cache).execute(
        LoadChannelsRequest(provider_id="demo")
    )

    cached = cache.search("demo", "", limit=10)
    assert cached is not None
    assert cached[0] is response.channels[0]


@pytest.mark.asyncio
async def test_browse_after_invalidation_replaces_fresh_snapshot() -> None:
    resolver = FakeResolver(FakeCatalogProvider())
    cache = ChannelCatalogueCache()
    cache.replace(
        "demo",
        (ChannelDTO("stale", "Stale", "demo", "stale-stream"),),
    )
    cache.invalidate("demo")

    response = await BrowseChannels(resolver, cache).execute(
        LoadChannelsRequest(provider_id="demo")
    )

    cached = cache.search("demo", "", limit=10)
    assert response.error is None
    assert cached is not None
    assert cached[0].id == "channel-1"
    assert cached[0] is response.channels[0]


@pytest.mark.asyncio
async def test_browse_channels_returns_resolution_errors_without_loading() -> None:
    resolver = FakeResolver()

    response = await BrowseChannels(resolver).execute(LoadChannelsRequest(provider_id="missing"))

    assert resolver.provider_ids == ["missing"]
    assert response.channels == []
    assert response.total == 0
    assert response.error == "Provider is unavailable"
