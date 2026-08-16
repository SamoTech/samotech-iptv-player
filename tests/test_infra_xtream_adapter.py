"""Tests for the capability-oriented Xtream live-channel adapter."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import pytest

from samotech_iptv.domain.value_objects.channel_id import ChannelId
from samotech_iptv.domain.value_objects.credential import Credential
from samotech_iptv.domain.value_objects.provider_capability import ProviderCapability
from samotech_iptv.infrastructure.providers.provider_factory import ProviderFactory
from samotech_iptv.infrastructure.providers.provider_metadata import InfraProviderMetadata
from samotech_iptv.infrastructure.providers.xtream_adapter import (
    XtreamProviderAdapter,
    register_xtream_with_factory,
)

if TYPE_CHECKING:
    from samotech_iptv.domain.value_objects.provider_id import ProviderId
    from samotech_iptv.infrastructure.providers.provider_context import ProviderContext


class FakeHttpClient:
    """Deterministic Xtream player API responder."""

    async def get_json(self, url: str) -> object:
        if "get_vod_info" in url:
            return {
                "movie_data": {"stream_id": 42, "name": "Example Movie"},
                "info": {"plot": "Detail metadata", "container_extension": "mp4"},
            }
        if "get_series_info" in url:
            return {
                "seasons": [{"season_number": 1, "name": "Season One"}],
                "episodes": {
                    "1": [
                        {
                            "id": 501,
                            "episode_num": 1,
                            "title": "Pilot",
                            "container_extension": "mp4",
                            "info": {"duration_secs": 1200, "plot": "Episode metadata"},
                        }
                    ]
                },
            }
        if "get_live_streams" in url:
            return [
                {"stream_id": 1, "name": "News", "container_extension": "m3u8"},
                {"stream_id": 2, "name": "Sports"},
            ]
        if "get_vod_streams" in url:
            return [{"stream_id": 42, "name": "Example Movie"}]
        if "get_live_categories" in url:
            return [{"category_id": "news", "category_name": "News"}]
        if "get_vod_categories" in url:
            return [{"category_id": "movies", "category_name": "Movies"}]
        if "get_series_categories" in url:
            return [{"category_id": "drama", "category_name": "Drama"}]
        if "get_series" in url:
            return [{"series_id": 84, "name": "Example Series"}]
        if "get_short_epg" in url:
            return {
                "epg_listings": [
                    {
                        "title": "RXhhbXBsZSBQcm9ncmFtbWU=",
                        "start_timestamp": 1_700_000_000,
                        "stop_timestamp": 1_700_003_600,
                    }
                ]
            }
        return {
            "user_info": {
                "auth": 1,
                "status": "Active",
                "active_cons": "1",
                "max_connections": "2",
            },
            "server_info": {
                "server_name": "Synthetic Xtream",
                "server_protocol": "https",
                "version": "1.0",
            },
        }


class FakeCredentialStore:
    """In-memory credential-store fake used only for adapter contracts."""

    def __init__(self) -> None:
        self.credential: Credential | None = None

    async def store(self, _: ProviderId, credential: Credential) -> None:
        self.credential = credential

    async def retrieve(self, _: ProviderId) -> Credential | None:
        return self.credential


class FakeContext:
    """Property-compatible context fake for the isolated Xtream adapter contract."""

    def __init__(self) -> None:
        self._http_client = FakeHttpClient()
        self._credential_store = FakeCredentialStore()

    @property
    def http_client(self) -> FakeHttpClient:
        return self._http_client

    @property
    def credential_store(self) -> FakeCredentialStore:
        return self._credential_store


def _adapter() -> XtreamProviderAdapter:
    context = cast("ProviderContext", FakeContext())
    metadata = InfraProviderMetadata(
        provider_id="xtream-demo",
        provider_type="xtream",
        base_url="https://portal.example.test",
    )
    return XtreamProviderAdapter(metadata, context)


@pytest.mark.asyncio
async def test_adapter_authenticates_stores_credentials_and_translates_live_channels() -> None:
    adapter = _adapter()

    assert await adapter.authenticate(Credential("user", "secret")) is True
    assert adapter.is_authenticated is True
    account = await adapter.load_account_info()
    server = await adapter.load_server_info()
    assert account.status == "active"
    assert account.max_connections == 2
    assert server.name == "Synthetic Xtream"
    assert server.protocol == "https"
    assert [channel.name for channel in await adapter.load_channels()] == ["News", "Sports"]
    assert [channel.name for channel in await adapter.search_channels("sport")] == ["Sports"]
    assert [movie.title for movie in await adapter.load_movies()] == ["Example Movie"]
    assert [series.title for series in await adapter.load_series()] == ["Example Series"]
    assert [category.id for category in await adapter.load_live_categories()] == ["news"]
    assert [category.id for category in await adapter.load_vod_categories()] == ["movies"]
    assert [category.id for category in await adapter.load_series_categories()] == ["drama"]
    assert [entry.title for entry in await adapter.load_epg(ChannelId("xtream-demo:1"))] == [
        "Example Programme"
    ]
    assert (
        await adapter.resolve_stream(ChannelId("xtream-demo:1"))
    ).value == "https://portal.example.test/live/user/secret/1.m3u8"
    movie = await adapter.load_movie_details("xtream-demo:42")
    assert movie.plot == "Detail metadata"
    assert (
        await adapter.resolve_movie_stream("xtream-demo:42", movie.stream_id.value)
    ).value.endswith("/movie/user/secret/42.mp4")
    seasons = await adapter.load_seasons("xtream-demo:84")
    assert [season.number for season in seasons] == [1]
    episodes = await adapter.load_episodes("xtream-demo:84", 1)
    assert [episode.title for episode in episodes] == ["Pilot"]
    assert (
        await adapter.resolve_episode_stream(episodes[0].id, episodes[0].stream_id.value)
    ).value.endswith("/series/user/secret/501.mp4")


def test_adapter_advertises_only_implemented_capabilities_and_registers_with_factory() -> None:
    adapter = _adapter()
    factory = ProviderFactory()
    register_xtream_with_factory(factory)

    assert adapter.supported_capabilities() == {
        ProviderCapability.AUTHENTICATION,
        ProviderCapability.ACCOUNT_INFO,
        ProviderCapability.SERVER_INFO,
        ProviderCapability.LIVE,
        ProviderCapability.CATEGORIES,
        ProviderCapability.EPG,
        ProviderCapability.STREAM_RESOLUTION,
        ProviderCapability.VOD,
        ProviderCapability.SERIES,
        ProviderCapability.MOVIE_PLAYBACK,
        ProviderCapability.SERIES_DETAILS,
        ProviderCapability.EPISODE_PLAYBACK,
        ProviderCapability.SEARCH,
    }
    assert factory.is_registered("xtream")


class MalformedCatalogHttpClient(FakeHttpClient):
    """Return realistic malformed and duplicate catalogue records for hardening tests."""

    async def get_json(self, url: str) -> object:
        if "get_live_streams" in url:
            return [
                {"stream_id": 1, "name": "Good Live"},
                {"stream_id": 1, "name": "Duplicate Live"},
                {"name": "Missing Live ID"},
            ]
        if "get_vod_streams" in url:
            return [
                {"stream_id": 42, "name": "Good Movie"},
                {"stream_id": 42, "name": "Duplicate Movie"},
                {"name": "Missing Movie ID"},
            ]
        if "get_series" in url:
            return [
                {"series_id": 84, "name": "Good Series"},
                {"series_id": 84, "name": "Duplicate Series"},
                {"name": "Missing Series ID"},
            ]
        return await super().get_json(url)


@pytest.mark.asyncio
async def test_adapter_skips_malformed_and_duplicate_catalogue_records() -> None:
    context = FakeContext()
    context._http_client = MalformedCatalogHttpClient()
    adapter = XtreamProviderAdapter(
        InfraProviderMetadata(
            provider_id="xtream-demo",
            provider_type="xtream",
            base_url="https://portal.example.test",
        ),
        cast("ProviderContext", context),
    )

    assert await adapter.authenticate(Credential("user", "secret")) is True
    assert [channel.name for channel in await adapter.load_channels()] == ["Good Live"]
    assert [movie.title for movie in await adapter.load_movies()] == ["Good Movie"]
    assert [series.title for series in await adapter.load_series()] == ["Good Series"]
