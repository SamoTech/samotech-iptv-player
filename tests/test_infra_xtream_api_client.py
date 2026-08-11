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
async def test_live_streams_returns_object_records() -> None:
    records = await _client([{"stream_id": 1, "name": "News"}]).live_streams()

    assert records[0]["name"] == "News"


@pytest.mark.asyncio
async def test_client_rejects_malformed_responses() -> None:
    with pytest.raises(ProviderError):
        await _client({}).live_streams()
