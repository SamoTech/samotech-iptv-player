"""Tests for deterministic Xtream API client response contracts."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import pytest

from samotech_iptv.core.exceptions import ProviderError
from samotech_iptv.domain.value_objects.credential import Credential
from samotech_iptv.domain.value_objects.url import URL
from samotech_iptv.infrastructure.providers.xtream_api_client import XtreamApiClient
from samotech_iptv.infrastructure.providers.xtream_request_builder import XtreamRequestBuilder

if TYPE_CHECKING:
    from samotech_iptv.infrastructure.network.http_client import AsyncHttpClient


class FakeHttpClient:
    """Test-only deterministic JSON responder."""

    def __init__(self, payload: object) -> None:
        self.payload = payload

    async def get_json(self, _: str) -> object:
        return self.payload


def _client(payload: object) -> XtreamApiClient:
    return XtreamApiClient(
        cast("AsyncHttpClient", FakeHttpClient(payload)),
        XtreamRequestBuilder(URL("https://portal.example.test"), Credential("user", "secret")),
    )


@pytest.mark.asyncio
async def test_authenticate_accepts_active_user_response() -> None:
    assert await _client({"user_info": {"auth": 1}}).authenticate() is True


@pytest.mark.asyncio
async def test_account_and_server_info_return_object_records() -> None:
    client = _client(
        {
            "user_info": {"auth": 1, "status": "Active"},
            "server_info": {"server_protocol": "https", "version": "1.0"},
        }
    )

    assert (await client.account_info())["status"] == "Active"
    assert (await client.server_info())["version"] == "1.0"


@pytest.mark.asyncio
async def test_account_and_server_info_reject_missing_sections() -> None:
    client = _client({"user_info": {"auth": 1}})

    with pytest.raises(ProviderError):
        await client.server_info()


@pytest.mark.asyncio
async def test_live_streams_returns_object_records() -> None:
    records = await _client([{"stream_id": 1, "name": "News"}]).live_streams()

    assert records[0]["name"] == "News"


@pytest.mark.asyncio
async def test_series_returns_object_records() -> None:
    records = await _client([{"series_id": 84, "name": "Example Series"}]).series()

    assert records[0]["name"] == "Example Series"


@pytest.mark.asyncio
async def test_vod_and_series_detail_operations_return_object_records() -> None:
    vod_detail = await _client({"movie_data": {"stream_id": 42}}).vod_info("42")
    series_detail = await _client({"episodes": {"1": []}}).series_info("84")

    assert vod_detail["movie_data"] == {"stream_id": 42}
    assert series_detail["episodes"] == {"1": []}


@pytest.mark.asyncio
async def test_live_categories_returns_object_records() -> None:
    records = await _client([{"category_id": "news", "category_name": "News"}]).live_categories()

    assert records[0]["category_name"] == "News"


@pytest.mark.asyncio
async def test_short_epg_returns_listing_records() -> None:
    records = await _client({"epg_listings": [{"title": "Example Programme"}]}).short_epg("101")

    assert records[0]["title"] == "Example Programme"


@pytest.mark.asyncio
async def test_client_rejects_malformed_responses() -> None:
    with pytest.raises(ProviderError):
        await _client({}).live_streams()
    with pytest.raises(ProviderError):
        await _client([]).vod_info("42")
