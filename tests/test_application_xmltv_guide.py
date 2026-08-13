from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, cast

import pytest

from samotech_iptv.application.dtos import (
    ConfigureXMLTVBindingRequest,
    RefreshXMLTVGuideRequest,
    XMLTVChannelMappingRequest,
)
from samotech_iptv.application.ports.provider_capabilities import CatalogProvider
from samotech_iptv.application.ports.xmltv_guide_port import XMLTVGuidePort
from samotech_iptv.application.use_cases.configure_xmltv_binding import ConfigureXMLTVBinding
from samotech_iptv.application.use_cases.refresh_xmltv_guide import RefreshXMLTVGuide
from samotech_iptv.domain.entities.channel import Channel
from samotech_iptv.domain.entities.epg_entry import EPGEntry
from samotech_iptv.domain.repositories.xmltv_binding_repository import XMLTVBindingRepository
from samotech_iptv.domain.value_objects.channel_id import ChannelId
from samotech_iptv.domain.value_objects.provider_id import ProviderId
from samotech_iptv.domain.value_objects.stream_id import StreamId

if TYPE_CHECKING:
    from collections.abc import Sequence

    from samotech_iptv.application.ports.provider_resolver_port import ProviderResolverPort
    from samotech_iptv.domain.entities.xmltv_binding import XMLTVBinding


class FakeCatalogProvider(CatalogProvider):
    """Catalogue double exposing one canonical registered channel."""

    async def load_channels(self) -> list[Channel]:
        return [
            Channel(
                id=ChannelId("demo:news"),
                provider_id=ProviderId("demo"),
                stream_id=StreamId("news"),
                name="News",
            )
        ]


class FakeResolver:
    """Minimal resolver double used only for configured-channel validation."""

    def resolve_catalog_provider(self, provider_id: str) -> CatalogProvider:
        assert provider_id == "demo"
        return FakeCatalogProvider()


class InMemoryBindingRepository(XMLTVBindingRepository):
    """Binding repository double retaining only the current non-secret binding."""

    def __init__(self) -> None:
        self.binding: XMLTVBinding | None = None

    async def initialise(self) -> None:
        return None

    async def load(self, provider_id: ProviderId) -> XMLTVBinding | None:
        if self.binding is None or self.binding.provider_id != provider_id:
            return None
        return self.binding

    async def save(self, binding: XMLTVBinding) -> None:
        self.binding = binding

    async def delete(self, provider_id: ProviderId) -> bool:
        if await self.load(provider_id) is None:
            return False
        self.binding = None
        return True


class FakeGuideService(XMLTVGuidePort):
    """Guide service double returning one canonical entry."""

    def __init__(self, entries: Sequence[EPGEntry]) -> None:
        self._entries = entries
        self.bindings: list[XMLTVBinding] = []

    async def refresh(self, binding: XMLTVBinding) -> Sequence[EPGEntry]:
        self.bindings.append(binding)
        return self._entries


def _request(channel_id: str = "demo:news") -> ConfigureXMLTVBindingRequest:
    return ConfigureXMLTVBindingRequest(
        provider_id="demo",
        source="/guides/demo.xml",
        mappings=(
            XMLTVChannelMappingRequest(
                source_channel_id="source.news",
                channel_id=channel_id,
            ),
        ),
    )


@pytest.mark.asyncio
async def test_configure_binding_validates_registered_channel_then_persists_local_source() -> None:
    repository = InMemoryBindingRepository()
    response = await ConfigureXMLTVBinding(
        cast("ProviderResolverPort", FakeResolver()), repository
    ).execute(_request())

    assert response.success is True
    assert response.error is None
    assert repository.binding is not None
    assert repository.binding.channel_mapping == {"source.news": ChannelId("demo:news")}


@pytest.mark.asyncio
async def test_configure_binding_returns_generic_failure_for_unknown_canonical_channel() -> None:
    repository = InMemoryBindingRepository()
    response = await ConfigureXMLTVBinding(
        cast("ProviderResolverPort", FakeResolver()), repository
    ).execute(_request(channel_id="demo:missing"))

    assert response.success is False
    assert response.error == "Unable to save XMLTV guide configuration"
    assert repository.binding is None


@pytest.mark.asyncio
async def test_refresh_returns_bounded_safe_entries_from_persisted_binding() -> None:
    repository = InMemoryBindingRepository()
    await ConfigureXMLTVBinding(cast("ProviderResolverPort", FakeResolver()), repository).execute(
        _request()
    )
    start = datetime(2026, 8, 13, 1, 0, tzinfo=UTC)
    guide_service = FakeGuideService(
        [
            EPGEntry(
                id="guide-1",
                channel_id=ChannelId("demo:news"),
                title="Morning News",
                start=start,
                end=start + timedelta(minutes=30),
                description="Private provider guide text",
            )
        ]
    )

    response = await RefreshXMLTVGuide(repository, guide_service).execute(
        RefreshXMLTVGuideRequest(provider_id="demo")
    )

    assert response.error is None
    assert len(response.entries) == 1
    assert response.entries[0].title == "Morning News"
    assert response.entries[0].description is None
    assert len(guide_service.bindings) == 1


@pytest.mark.asyncio
async def test_refresh_returns_generic_error_without_a_configured_binding() -> None:
    response = await RefreshXMLTVGuide(InMemoryBindingRepository(), FakeGuideService([])).execute(
        RefreshXMLTVGuideRequest(provider_id="missing")
    )

    assert response.entries == []
    assert response.error == "Unable to refresh XMLTV guide"
