"""Contract and behaviour tests for the MAG provider adapter."""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from samotech_iptv.infrastructure.providers.provider_factory import ProviderFactory
from samotech_iptv.core.exceptions import AuthenticationError, ProviderError, ValidationError
from samotech_iptv.domain.value_objects.channel_id import ChannelId
from samotech_iptv.domain.value_objects.credential import Credential
from samotech_iptv.infrastructure.providers.mag_adapter import (
    MagProviderAdapter,
    register_with_factory,
)
from samotech_iptv.infrastructure.providers.mag_credential import MagCredential
from samotech_iptv.infrastructure.providers.mag_domain_translator import MagDomainTranslator
from samotech_iptv.infrastructure.providers.provider_context import ProviderContext
from samotech_iptv.infrastructure.providers.provider_metadata import InfraProviderMetadata


class FakeMagProvider:
    """Protocol-faithful in-memory MAG provider used to isolate network I/O."""

    def __init__(self) -> None:
        self._session = SimpleNamespace(token="")
        self.connect_calls = 0
        self.refresh_calls = 0
        self.close_calls = 0
        self.epg_calls: list[tuple[list[int] | None, int]] = []
        self.stream_calls: list[tuple[int, str]] = []
        self.channels: list[dict[str, Any]] = [
            {
                "id": 1,
                "name": "BBC One",
                "logo": "https://logo.example.test/bbc1.png",
                "tv_genre_id": 10,
                "number": 1,
            },
            {"id": 2, "name": "ITV", "tv_genre_id": 10, "number": 2},
        ]
        self.epg: dict[int, list[dict[str, Any]]] = {
            1: [
                {
                    "id": 101,
                    "name": "News at Six",
                    "descr": "Evening news programme.",
                    "start_timestamp": 1700000000,
                    "stop_timestamp": 1700003600,
                }
            ]
        }

    async def connect(self) -> None:
        self.connect_calls += 1
        self._session.token = "session-token-for-test-only"

    async def close(self) -> None:
        self.close_calls += 1

    async def refresh_token(self) -> None:
        self.refresh_calls += 1
        self._session.token = "refreshed-session-token-for-test-only"

    async def get_channels(self) -> list[dict[str, Any]]:
        return self.channels

    async def get_epg(
        self, channel_ids: list[int] | None = None, period: int = 3
    ) -> dict[int, list[dict[str, Any]]]:
        self.epg_calls.append((channel_ids, period))
        if channel_ids is None:
            return self.epg
        return {channel_id: self.epg.get(channel_id, []) for channel_id in channel_ids}

    async def get_stream_url(self, stream_id: int, stream_type: str = "live") -> str:
        self.stream_calls.append((stream_id, stream_type))
        return f"https://stream.example.test/live/{stream_id}.m3u8"


@pytest.fixture
def metadata() -> InfraProviderMetadata:
    return InfraProviderMetadata(
        provider_id="mag-test",
        provider_type="mag",
        base_url="https://portal.example.test",
    )


@pytest.fixture
def context() -> ProviderContext:
    return ProviderContext.build(overrides={"connect_timeout": 10, "read_timeout": 30})


@pytest.fixture
def legacy() -> FakeMagProvider:
    return FakeMagProvider()


@pytest.fixture
def adapter(
    metadata: InfraProviderMetadata, context: ProviderContext, legacy: FakeMagProvider
) -> MagProviderAdapter:
    return MagProviderAdapter(metadata=metadata, context=context, legacy_provider=legacy)


@pytest.fixture
def credential() -> Credential:
    return Credential(username="00:11:22:33:44:55", _password="test-only-secret")


class TestAuthentication:
    @pytest.mark.asyncio
    async def test_authentication_consumes_mac_identity(
        self, adapter: MagProviderAdapter, credential: Credential, legacy: FakeMagProvider
    ) -> None:
        assert await adapter.authenticate(credential) is True
        assert legacy.connect_calls == 1
        assert adapter.is_authenticated is True
        assert adapter._credential is not None
        assert adapter._credential.mac_address == credential.username
        assert adapter._credential.portal_url == "https://portal.example.test"

    @pytest.mark.asyncio
    async def test_authentication_keeps_session_token_out_of_metadata(
        self,
        adapter: MagProviderAdapter,
        credential: Credential,
        metadata: InfraProviderMetadata,
    ) -> None:
        await adapter.authenticate(credential)
        assert adapter._session_token == "session-token-for-test-only"
        assert not hasattr(metadata, "auth_token")

    @pytest.mark.asyncio
    async def test_authentication_translates_legacy_failure(
        self, metadata: InfraProviderMetadata, context: ProviderContext, credential: Credential
    ) -> None:
        from providers.base.errors import AuthError

        class FailingMagProvider(FakeMagProvider):
            async def connect(self) -> None:
                raise AuthError("invalid subscription")

        failing_adapter = MagProviderAdapter(metadata, context, FailingMagProvider())
        with pytest.raises(AuthenticationError):
            await failing_adapter.authenticate(credential)
        assert failing_adapter.is_authenticated is False


class TestProviderCapabilities:
    def test_adapter_is_concrete_and_has_canonical_capabilities(
        self, adapter: MagProviderAdapter
    ) -> None:
        assert adapter.provider_id.value == "mag-test"
        assert adapter.supported_capabilities() == {
            "authentication", "catalog", "epg", "search", "playback", "session"
        }

    def test_factory_creates_a_concrete_adapter(
        self, metadata: InfraProviderMetadata, context: ProviderContext, legacy: FakeMagProvider
    ) -> None:
        factory = ProviderFactory()
        register_with_factory(factory)
        result = factory.create(metadata, context=context, legacy_provider=legacy)
        assert isinstance(result, MagProviderAdapter)
        assert result.provider_id.value == metadata.provider_id


class TestCatalogAndSearch:
    @pytest.mark.asyncio
    async def test_load_channels_returns_domain_entities(
        self, adapter: MagProviderAdapter, credential: Credential
    ) -> None:
        await adapter.authenticate(credential)
        channels = await adapter.load_channels()
        assert [channel.name for channel in channels] == ["BBC One", "ITV"]
        assert channels[0].provider_id == adapter.provider_id
        assert str(channels[0].stream_id) == "1"

    @pytest.mark.asyncio
    async def test_search_channels_filters_and_limits(
        self, adapter: MagProviderAdapter, credential: Credential
    ) -> None:
        await adapter.authenticate(credential)
        results = await adapter.search_channels("bbc", limit=1)
        assert [channel.name for channel in results] == ["BBC One"]
        assert await adapter.search_channels("", limit=0) == []


class TestEpgAndPlayback:
    @pytest.mark.asyncio
    async def test_load_epg_returns_domain_entries(
        self, adapter: MagProviderAdapter, credential: Credential, legacy: FakeMagProvider
    ) -> None:
        await adapter.authenticate(credential)
        entries = await adapter.load_epg(ChannelId("1"))
        assert legacy.epg_calls == [([1], 3)]
        assert entries[0].id == "101"
        assert entries[0].title == "News at Six"
        assert str(entries[0].channel_id) == "1"

    @pytest.mark.asyncio
    async def test_resolve_stream_returns_validated_url(
        self, adapter: MagProviderAdapter, credential: Credential, legacy: FakeMagProvider
    ) -> None:
        await adapter.authenticate(credential)
        url = await adapter.resolve_stream(ChannelId("1"))
        assert str(url) == "https://stream.example.test/live/1.m3u8"
        assert legacy.stream_calls == [(1, "live")]

    @pytest.mark.asyncio
    async def test_non_numeric_mag_channel_id_is_rejected(
        self, adapter: MagProviderAdapter, credential: Credential
    ) -> None:
        await adapter.authenticate(credential)
        with pytest.raises(ValidationError):
            await adapter.resolve_stream(ChannelId("not-a-number"))


class TestSessionLifecycle:
    @pytest.mark.asyncio
    async def test_refresh_and_close_manage_volatile_session_state(
        self, adapter: MagProviderAdapter, credential: Credential, legacy: FakeMagProvider
    ) -> None:
        await adapter.authenticate(credential)
        assert await adapter.refresh_session() is True
        assert legacy.refresh_calls == 1
        assert adapter._session_token == "refreshed-session-token-for-test-only"
        await adapter.close_session()
        assert legacy.close_calls == 1
        assert adapter.is_authenticated is False
        assert adapter._session_token is None


class TestDomainTranslation:
    def test_channel_translation_requires_canonical_domain_fields(self, adapter: MagProviderAdapter) -> None:
        channel = MagDomainTranslator.channel(
            {"id": 42, "name": "Sky News", "number": "100"}, adapter.provider_id
        )
        assert channel.id.value == "42"
        assert channel.stream_id.value == "42"
        assert channel.number == 100

    def test_epg_translation_requires_valid_time_range(self) -> None:
        entry = MagDomainTranslator.epg_entry(
            {
                "id": "e1",
                "name": "Film Tonight",
                "start_timestamp": 1700000000,
                "stop_timestamp": 1700007200,
            },
            ChannelId("10"),
        )
        assert entry.id == "e1"
        assert entry.end > entry.start

    def test_invalid_epg_timestamp_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            MagDomainTranslator.epg_entry(
                {"name": "Unknown", "start_timestamp": 0, "stop_timestamp": 0},
                ChannelId("1"),
            )


class TestRealLegacyConstruction:
    def test_real_legacy_provider_receives_mag_identity(
        self, metadata: InfraProviderMetadata, context: ProviderContext, credential: Credential
    ) -> None:
        adapter = MagProviderAdapter(metadata, context)
        adapter._set_credential(
            MagCredential.from_application_credential(credential, metadata.base_url)
        )
        legacy = adapter._ensure_provider()
        legacy_credentials = legacy._session._creds  # type: ignore[attr-defined]
        assert legacy_credentials.portal_url == metadata.base_url
        assert legacy_credentials.mac_address == credential.username
        assert not hasattr(metadata, "auth_token")
