"""Tests for the capability-oriented Xtream live-channel adapter."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import pytest

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
        if "get_live_streams" in url:
            return [{"stream_id": 1, "name": "News"}, {"stream_id": 2, "name": "Sports"}]
        if "get_vod_streams" in url:
            return [{"stream_id": 42, "name": "Example Movie"}]
        return {"user_info": {"auth": 1}}


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
    assert [channel.name for channel in await adapter.load_channels()] == ["News", "Sports"]
    assert [channel.name for channel in await adapter.search_channels("sport")] == ["Sports"]
    assert [movie.title for movie in await adapter.load_movies()] == ["Example Movie"]


def test_adapter_advertises_only_implemented_capabilities_and_registers_with_factory() -> None:
    adapter = _adapter()
    factory = ProviderFactory()
    register_xtream_with_factory(factory)

    assert adapter.supported_capabilities() == {
        ProviderCapability.AUTHENTICATION,
        ProviderCapability.LIVE,
        ProviderCapability.VOD,
        ProviderCapability.SEARCH,
    }
    assert factory.is_registered("xtream")
