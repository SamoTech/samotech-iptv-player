from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import pytest

from samotech_iptv.application.dtos import LoadRegisteredEPGRequest
from samotech_iptv.application.ports.provider_capabilities import EPGProvider
from samotech_iptv.application.ports.provider_resolver_port import ProviderResolverPort
from samotech_iptv.application.use_cases.load_registered_epg import LoadRegisteredEPG
from samotech_iptv.domain.entities.epg_entry import EPGEntry
from samotech_iptv.domain.value_objects.channel_id import ChannelId

if TYPE_CHECKING:
    from samotech_iptv.application.ports.provider_capabilities import (
        CatalogProvider,
        CategoryProvider,
        PlaybackProvider,
        SearchProvider,
    )


class FakeEPGProvider(EPGProvider):
    """EPG capability double retaining the requested channel identifier."""

    def __init__(self) -> None:
        self.channel_ids: list[str] = []
        start = datetime(2026, 8, 12, 10, 0, tzinfo=UTC)
        self.entries = [
            EPGEntry(
                id="programme-1",
                channel_id=ChannelId("channel-1"),
                title="Morning News",
                start=start,
                end=start + timedelta(minutes=30),
                description="Details without provider credentials",
                category="News",
            ),
            EPGEntry(
                id="programme-2",
                channel_id=ChannelId("channel-1"),
                title="Weather Update",
                start=start + timedelta(minutes=30),
                end=start + timedelta(minutes=45),
            ),
        ]

    async def load_epg(self, channel_id: ChannelId) -> list[EPGEntry]:
        self.channel_ids.append(channel_id.value)
        return self.entries


class FakeResolver(ProviderResolverPort):
    """Resolver double exposing only EPG capability for the selected provider."""

    def __init__(self, provider: EPGProvider | None = None) -> None:
        self._provider = provider
        self.provider_ids: list[str] = []

    def resolve_catalog_provider(self, provider_id: str) -> CatalogProvider:
        raise AssertionError(f"Unexpected catalogue resolution for {provider_id}")

    def resolve_category_provider(self, provider_id: str) -> CategoryProvider:
        raise AssertionError(f"Unexpected category resolution for {provider_id}")

    def resolve_playback_provider(self, provider_id: str) -> PlaybackProvider:
        raise AssertionError(f"Unexpected playback resolution for {provider_id}")

    def resolve_search_provider(self, provider_id: str) -> SearchProvider:
        raise AssertionError(f"Unexpected search resolution for {provider_id}")

    def resolve_epg_provider(self, provider_id: str) -> EPGProvider:
        self.provider_ids.append(provider_id)
        if self._provider is None:
            raise RuntimeError("Provider is unavailable")
        return self._provider


@pytest.mark.asyncio
async def test_load_registered_epg_resolves_provider_and_returns_bounded_safe_entries() -> None:
    provider = FakeEPGProvider()
    resolver = FakeResolver(provider)

    response = await LoadRegisteredEPG(resolver).execute(
        LoadRegisteredEPGRequest(provider_id="mag-demo", channel_id="channel-1", limit=1)
    )

    assert resolver.provider_ids == ["mag-demo"]
    assert provider.channel_ids == ["channel-1"]
    assert response.error is None
    assert len(response.entries) == 1
    assert response.entries[0].title == "Morning News"
    assert response.entries[0].start == "2026-08-12T10:00:00+00:00"
    assert response.entries[0].end == "2026-08-12T10:30:00+00:00"
    assert response.entries[0].description == "Details without provider credentials"
    assert response.entries[0].category == "News"


@pytest.mark.asyncio
async def test_load_registered_epg_returns_safe_error_for_provider_resolution_failure() -> None:
    response = await LoadRegisteredEPG(FakeResolver()).execute(
        LoadRegisteredEPGRequest(provider_id="missing", channel_id="channel-1")
    )

    assert response.entries == []
    assert response.error == "Unable to load EPG for the selected channel"
