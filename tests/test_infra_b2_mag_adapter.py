"""Unit tests for Phase B.2 — MagProviderAdapter.

All MAGProvider calls are mocked.  No real network access.
"""
from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from samotech_iptv.infrastructure.providers.provider_metadata import InfraProviderMetadata
from samotech_iptv.infrastructure.providers.provider_context import ProviderContext
from samotech_iptv.infrastructure.providers.provider_factory import ProviderFactory
from samotech_iptv.infrastructure.providers.provider_registry import ProviderRegistry
from samotech_iptv.infrastructure.providers.mag_adapter import (
    MagProviderAdapter,
    register_with_factory,
)
from samotech_iptv.infrastructure.providers.mag_dto_translator import MagDtoTranslator
from samotech_iptv.infrastructure.providers.mag_error_translator import translate_mag_error
from samotech_iptv.application.dtos.auth import AuthenticateRequest
from samotech_iptv.application.dtos.channels import LoadChannelsRequest
from samotech_iptv.application.dtos.epg import LoadEPGRequest
from samotech_iptv.application.dtos.stream import ResolveStreamRequest
from samotech_iptv.core.exceptions import (
    AuthenticationError,
    NetworkError,
    ProviderError,
    ValidationError,
)


# ──────────────────────────────────── Fixtures

@pytest.fixture
def meta() -> InfraProviderMetadata:
    return InfraProviderMetadata(
        provider_id="mag-test",
        provider_type="mag",
        base_url="http://portal.example.com",
    )


@pytest.fixture
def mock_context() -> ProviderContext:
    ctx = MagicMock(spec=ProviderContext)
    ctx.config = MagicMock()
    ctx.config.network_config.return_value = MagicMock(
        connect_timeout=10.0,
        read_timeout=30.0,
        max_retries=3,
    )
    return ctx


@pytest.fixture
def mock_legacy() -> MagicMock:
    """A fully mocked MAGProvider instance."""
    provider = MagicMock()
    provider._session = MagicMock()
    provider._session.token = "test-token-abc"
    provider.connect = AsyncMock()
    provider.close = AsyncMock()
    provider.authenticate = AsyncMock()
    provider.refresh_token = AsyncMock()
    provider.get_channels = AsyncMock(return_value=[
        {"id": 1, "name": "BBC One", "logo": "http://logo.example.com/bbc1.png",
         "tv_genre_id": 10, "number": 1},
        {"id": 2, "name": "ITV", "logo": "", "tv_genre_id": 10, "number": 2},
    ])
    provider.get_vod = AsyncMock(return_value=[])
    provider.get_series = AsyncMock(return_value=[])
    provider.get_epg = AsyncMock(return_value={
        1: [
            {
                "name": "News at Six",
                "descr": "Evening news programme.",
                "start_timestamp": 1700000000,
                "stop_timestamp":  1700003600,
            }
        ]
    })
    provider.get_stream_url = AsyncMock(return_value="http://stream.example.com/live/1.m3u8")
    return provider


@pytest.fixture
def adapter(meta, mock_context, mock_legacy) -> MagProviderAdapter:
    return MagProviderAdapter(
        metadata=meta,
        context=mock_context,
        legacy_provider=mock_legacy,
    )


# ──────────────────────────────────── Authentication

class TestAuthentication:
    @pytest.mark.asyncio
    async def test_authenticate_returns_response_with_token(
        self, adapter: MagProviderAdapter, mock_legacy: MagicMock
    ) -> None:
        req = AuthenticateRequest(portal_url="http://portal.example.com", mac_address="AA:BB:CC")
        resp = await adapter.authenticate(req)
        mock_legacy.connect.assert_called_once()
        assert resp.token == "test-token-abc"
        assert resp.success is True

    @pytest.mark.asyncio
    async def test_is_authenticated_true_after_success(
        self, adapter: MagProviderAdapter
    ) -> None:
        req = AuthenticateRequest(portal_url="http://portal.example.com", mac_address="AA:BB:CC")
        await adapter.authenticate(req)
        assert adapter.is_authenticated is True

    @pytest.mark.asyncio
    async def test_authentication_error_translated(
        self, meta: InfraProviderMetadata, mock_context: ProviderContext
    ) -> None:
        """An AuthError from the legacy provider must become AuthenticationError."""
        from providers.base.errors import AuthError as LegacyAuthError
        legacy = MagicMock()
        legacy._session = MagicMock(token="")
        legacy.connect = AsyncMock(side_effect=LegacyAuthError("bad mac"))

        adapter = MagProviderAdapter(
            metadata=meta, context=mock_context, legacy_provider=legacy
        )
        req = AuthenticateRequest(portal_url="http://p.example.com", mac_address="XX")
        with pytest.raises(AuthenticationError):
            await adapter.authenticate(req)
        assert adapter.is_authenticated is False


# ──────────────────────────────────── Catalog

class TestCatalog:
    @pytest.mark.asyncio
    async def test_load_channels_returns_dtos(
        self, adapter: MagProviderAdapter
    ) -> None:
        resp = await adapter.load_channels(LoadChannelsRequest())
        assert resp.total == 2
        assert resp.channels[0].name == "BBC One"
        assert resp.channels[1].name == "ITV"

    @pytest.mark.asyncio
    async def test_load_channels_dto_fields(
        self, adapter: MagProviderAdapter
    ) -> None:
        resp = await adapter.load_channels(LoadChannelsRequest())
        bbc = resp.channels[0]
        assert bbc.id == "1"
        assert bbc.logo_url == "http://logo.example.com/bbc1.png"
        assert bbc.number == 1

    @pytest.mark.asyncio
    async def test_load_categories_returns_empty_list(
        self, adapter: MagProviderAdapter
    ) -> None:
        cats = await adapter.load_categories()
        assert cats == []

    @pytest.mark.asyncio
    async def test_channel_network_error_translated(
        self, meta: InfraProviderMetadata, mock_context: ProviderContext
    ) -> None:
        from providers.base.errors import NetworkError as LegacyNetworkError
        legacy = MagicMock()
        legacy.get_channels = AsyncMock(
            side_effect=LegacyNetworkError("DNS failure")
        )
        adapter = MagProviderAdapter(
            metadata=meta, context=mock_context, legacy_provider=legacy
        )
        with pytest.raises(NetworkError):
            await adapter.load_channels(LoadChannelsRequest())


# ──────────────────────────────────── EPG

class TestEPG:
    @pytest.mark.asyncio
    async def test_load_epg_returns_entries(
        self, adapter: MagProviderAdapter
    ) -> None:
        req = LoadEPGRequest(channel_ids=["1"], period_days=3)
        resp = await adapter.load_epg(req)
        assert "1" in resp.entries_by_channel
        entries = resp.entries_by_channel["1"]
        assert len(entries) == 1
        assert entries[0].title == "News at Six"

    @pytest.mark.asyncio
    async def test_load_epg_empty_channel_ids_passes_none(
        self, adapter: MagProviderAdapter, mock_legacy: MagicMock
    ) -> None:
        req = LoadEPGRequest(channel_ids=[], period_days=1)
        await adapter.load_epg(req)
        mock_legacy.get_epg.assert_called_once_with(channel_ids=None, period=1)

    @pytest.mark.asyncio
    async def test_load_epg_error_translated(
        self, meta: InfraProviderMetadata, mock_context: ProviderContext
    ) -> None:
        from providers.base.errors import NetworkError as LegacyNetworkError
        legacy = MagicMock()
        legacy.get_epg = AsyncMock(side_effect=LegacyNetworkError("timeout"))
        adapter = MagProviderAdapter(
            metadata=meta, context=mock_context, legacy_provider=legacy
        )
        with pytest.raises(NetworkError):
            await adapter.load_epg(LoadEPGRequest(channel_ids=None, period_days=3))


# ──────────────────────────────────── Search

class TestSearch:
    @pytest.mark.asyncio
    async def test_search_filters_by_name(
        self, adapter: MagProviderAdapter
    ) -> None:
        from samotech_iptv.application.dtos.channels import ChannelDTO
        channels = [
            ChannelDTO(id="1", name="BBC One", logo_url="", category_id="",
                       stream_id="1", number=1, is_favorite=False),
            ChannelDTO(id="2", name="ITV", logo_url="", category_id="",
                       stream_id="2", number=2, is_favorite=False),
            ChannelDTO(id="3", name="BBC Two", logo_url="", category_id="",
                       stream_id="3", number=3, is_favorite=False),
        ]
        results = await adapter.search_channels("bbc", channels=channels)
        assert len(results) == 2
        assert all("bbc" in ch.name.lower() for ch in results)

    @pytest.mark.asyncio
    async def test_search_empty_query_returns_all(
        self, adapter: MagProviderAdapter, mock_legacy: MagicMock
    ) -> None:
        from samotech_iptv.application.dtos.channels import ChannelDTO
        channels = [
            ChannelDTO(id="1", name="BBC One", logo_url="", category_id="",
                       stream_id="1", number=1, is_favorite=False),
        ]
        results = await adapter.search_channels("", channels=channels)
        assert len(results) == 1


# ──────────────────────────────────── Stream resolution

class TestStreamResolution:
    @pytest.mark.asyncio
    async def test_resolve_stream_returns_url(
        self, adapter: MagProviderAdapter
    ) -> None:
        req = ResolveStreamRequest(stream_id="1", stream_type="live")
        resp = await adapter.resolve_stream(req)
        assert resp.url == "http://stream.example.com/live/1.m3u8"
        assert resp.stream_id == "1"

    @pytest.mark.asyncio
    async def test_resolve_stream_invalid_id_raises_validation_error(
        self, adapter: MagProviderAdapter
    ) -> None:
        req = ResolveStreamRequest(stream_id="not-an-int", stream_type="live")
        with pytest.raises(ValidationError):
            await adapter.resolve_stream(req)

    @pytest.mark.asyncio
    async def test_resolve_stream_error_translated(
        self, meta: InfraProviderMetadata, mock_context: ProviderContext
    ) -> None:
        from providers.base.errors import ProviderError as LegacyProviderError
        legacy = MagicMock()
        legacy.get_stream_url = AsyncMock(
            side_effect=LegacyProviderError("stream unavailable")
        )
        adapter = MagProviderAdapter(
            metadata=meta, context=mock_context, legacy_provider=legacy
        )
        req = ResolveStreamRequest(stream_id="42", stream_type="live")
        with pytest.raises(ProviderError):
            await adapter.resolve_stream(req)


# ──────────────────────────────────── Token refresh

class TestTokenRefresh:
    @pytest.mark.asyncio
    async def test_refresh_session_calls_legacy(
        self, adapter: MagProviderAdapter, mock_legacy: MagicMock
    ) -> None:
        await adapter.refresh_session()
        mock_legacy.refresh_token.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_session_calls_legacy_close(
        self, adapter: MagProviderAdapter, mock_legacy: MagicMock
    ) -> None:
        await adapter.close_session()
        mock_legacy.close.assert_called_once()


# ──────────────────────────────────── Registry / Factory

class TestRegistryAndFactory:
    def test_register_with_factory_adds_mag_type(self) -> None:
        factory = ProviderFactory()
        register_with_factory(factory)
        assert factory.is_registered("mag") is True

    def test_factory_creates_adapter(
        self, meta: InfraProviderMetadata, mock_context: ProviderContext
    ) -> None:
        factory = ProviderFactory()
        register_with_factory(factory)
        mock_legacy = MagicMock()
        adapter = factory.create(meta, context=mock_context, legacy_provider=mock_legacy)
        assert isinstance(adapter, MagProviderAdapter)

    def test_registry_accepts_adapter(
        self, meta: InfraProviderMetadata
    ) -> None:
        registry = ProviderRegistry()
        registry.register(meta)
        assert "mag-test" in registry

    def test_capabilities_contains_all_six(
        self, adapter: MagProviderAdapter
    ) -> None:
        caps = adapter.capabilities()
        for cap in ("authentication", "catalog", "epg", "search", "playback", "session"):
            assert cap in caps

    def test_supports_known_capability(
        self, adapter: MagProviderAdapter
    ) -> None:
        assert adapter.supports("authentication") is True
        assert adapter.supports("nonexistent") is False


# ──────────────────────────────────── DTO translation

class TestDtoTranslation:
    def test_channel_dto_mapping(self) -> None:
        raw = {"id": 42, "name": "Sky News", "logo": "http://sky.com/logo.png",
               "tv_genre_id": 5, "number": 100, "fav": 1}
        dto = MagDtoTranslator.channel(raw)
        assert dto.id == "42"
        assert dto.name == "Sky News"
        assert dto.logo_url == "http://sky.com/logo.png"
        assert dto.category_id == "5"
        assert dto.number == 100
        assert dto.is_favorite is True

    def test_channel_dto_missing_name_defaults_empty(self) -> None:
        dto = MagDtoTranslator.channel({"id": 1})
        assert dto.name == ""

    def test_epg_entry_timestamps_converted(self) -> None:
        raw = {
            "name": "Film Tonight",
            "descr": "A great film.",
            "start_timestamp": 1700000000,
            "stop_timestamp": 1700007200,
        }
        entry = MagDtoTranslator.epg_entry(raw, channel_id=10)
        assert entry.title == "Film Tonight"
        assert entry.start is not None
        assert entry.end is not None
        assert entry.channel_id == "10"

    def test_epg_entry_zero_timestamps_yields_none(self) -> None:
        raw = {"name": "Unknown", "start_timestamp": 0, "stop_timestamp": 0}
        entry = MagDtoTranslator.epg_entry(raw, channel_id=1)
        assert entry.start is None
        assert entry.end is None

    def test_auth_response_has_token(self) -> None:
        resp = MagDtoTranslator.auth_response("http://p.com", "mytoken")
        assert resp.token == "mytoken"
        assert resp.success is True

    def test_stream_response_has_url(self) -> None:
        resp = MagDtoTranslator.stream_response("http://stream.com/live.m3u8", "7")
        assert resp.url == "http://stream.com/live.m3u8"
        assert resp.stream_id == "7"


# ──────────────────────────────────── Error translation

class TestMagErrorTranslation:
    def test_legacy_auth_error_translated(self) -> None:
        from providers.base.errors import AuthError
        result = translate_mag_error(AuthError("bad credentials"))
        assert isinstance(result, AuthenticationError)

    def test_legacy_network_error_translated(self) -> None:
        from providers.base.errors import NetworkError as LegacyNetworkError
        result = translate_mag_error(LegacyNetworkError("connection refused"))
        assert isinstance(result, NetworkError)

    def test_legacy_provider_error_translated(self) -> None:
        from providers.base.errors import ProviderError as LegacyProviderError
        result = translate_mag_error(LegacyProviderError("generic failure"))
        assert isinstance(result, ProviderError)

    def test_domain_error_passes_through(self) -> None:
        original = ProviderError("already domain")
        result = translate_mag_error(original)
        assert result is original

    def test_arbitrary_exception_becomes_provider_error(self) -> None:
        result = translate_mag_error(RuntimeError("something wild"))
        assert isinstance(result, ProviderError)
