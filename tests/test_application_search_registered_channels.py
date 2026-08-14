from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from samotech_iptv.application.channel_catalogue_cache import ChannelCatalogueCache
from samotech_iptv.application.dtos import ChannelDTO, SearchRegisteredChannelsRequest
from samotech_iptv.application.ports.provider_capabilities import SearchProvider
from samotech_iptv.application.ports.provider_resolver_port import ProviderResolverPort
from samotech_iptv.application.use_cases.search_registered_channels import (
    SearchRegisteredChannels,
)
from samotech_iptv.domain.entities.channel import Channel
from samotech_iptv.domain.value_objects.channel_id import ChannelId
from samotech_iptv.domain.value_objects.provider_id import ProviderId
from samotech_iptv.domain.value_objects.stream_id import StreamId

if TYPE_CHECKING:
    from samotech_iptv.application.ports.provider_capabilities import (
        CatalogProvider,
        CategoryProvider,
        PlaybackProvider,
    )


class FakeSearchProvider(SearchProvider):
    """Search-capable provider double recording query and limit inputs."""

    def __init__(self) -> None:
        self.requests: list[tuple[str, int]] = []

    async def search_channels(self, query: str, limit: int = 100) -> list[Channel]:
        self.requests.append((query, limit))
        return [
            Channel(
                id=ChannelId("channel-1"),
                provider_id=ProviderId("demo"),
                stream_id=StreamId("stream-1"),
                name="Demo Channel",
            )
        ]


class FakeResolver(ProviderResolverPort):
    """Resolver double exposing only search capability for the selected provider."""

    def __init__(self, provider: SearchProvider) -> None:
        self._provider = provider
        self.provider_ids: list[str] = []

    def resolve_catalog_provider(self, provider_id: str) -> CatalogProvider:
        raise AssertionError(f"Unexpected catalogue resolution for {provider_id}")

    def resolve_category_provider(self, provider_id: str) -> CategoryProvider:
        raise AssertionError(f"Unexpected category resolution for {provider_id}")

    def resolve_playback_provider(self, provider_id: str) -> PlaybackProvider:
        raise AssertionError(f"Unexpected playback resolution for {provider_id}")

    def resolve_search_provider(self, provider_id: str) -> SearchProvider:
        self.provider_ids.append(provider_id)
        return self._provider

    def resolve_epg_provider(self, provider_id: str) -> object:
        raise AssertionError(f"Unexpected EPG resolution for {provider_id}")


@pytest.mark.asyncio
async def test_search_registered_channels_filters_cached_dtos_without_provider_calls() -> None:
    provider = FakeSearchProvider()
    resolver = FakeResolver(provider)
    cache = ChannelCatalogueCache()
    cached_channels = (
        ChannelDTO(
            id="channel-1",
            name="Demo News",
            provider_id="demo",
            stream_id="stream-1",
        ),
        ChannelDTO(
            id="channel-2",
            name="Demo Sports",
            provider_id="demo",
            stream_id="stream-2",
        ),
    )
    cache.replace("demo", cached_channels)
    use_case = SearchRegisteredChannels(resolver, cache)

    common = await use_case.execute(
        SearchRegisteredChannelsRequest(provider_id="demo", query="news", limit=25)
    )
    no_match = await use_case.execute(
        SearchRegisteredChannelsRequest(provider_id="demo", query="missing", limit=25)
    )
    empty = await use_case.execute(
        SearchRegisteredChannelsRequest(provider_id="demo", query="", limit=25)
    )
    repeated = await use_case.execute(
        SearchRegisteredChannelsRequest(provider_id="demo", query="news", limit=25)
    )

    assert resolver.provider_ids == []
    assert provider.requests == []
    assert common.channels[0] is cached_channels[0]
    assert common.total == 1
    assert no_match.channels == ()
    assert empty.channels == cached_channels
    assert repeated.channels[0] is cached_channels[0]


@pytest.mark.asyncio
async def test_search_registered_channels_filters_39753_cached_dtos_without_provider_calls() -> (
    None
):
    provider = FakeSearchProvider()
    resolver = FakeResolver(provider)
    cache = ChannelCatalogueCache()
    cached_channels = tuple(
        ChannelDTO(
            id=f"channel-{index}",
            name=f"Demo Channel {index}",
            provider_id="demo",
            stream_id=f"stream-{index}",
        )
        for index in range(39_753)
    )
    cache.replace("demo", cached_channels)

    response = await SearchRegisteredChannels(resolver, cache).execute(
        SearchRegisteredChannelsRequest(provider_id="demo", query="channel", limit=100)
    )

    assert resolver.provider_ids == []
    assert provider.requests == []
    assert response.total == 100
    assert response.channels[0] is cached_channels[0]


@pytest.mark.asyncio
async def test_search_registered_channels_resolves_provider_and_returns_safe_channel_dtos() -> None:
    provider = FakeSearchProvider()
    resolver = FakeResolver(provider)

    response = await SearchRegisteredChannels(resolver).execute(
        SearchRegisteredChannelsRequest(provider_id="demo", query="news", limit=25)
    )

    assert resolver.provider_ids == ["demo"]
    assert provider.requests == [("news", 25)]
    assert response.total == 1
    assert response.channels[0].name == "Demo Channel"
    assert response.channels[0].stream_id == "stream-1"
