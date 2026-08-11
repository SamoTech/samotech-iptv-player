"""Integration coverage for the canonical MAG provider execution path."""
from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

import pytest

from samotech_iptv.application.dtos import (
    AuthenticateRequest,
    LoadChannelsRequest,
    LoadEPGRequest,
    ResolveStreamRequest,
)
from samotech_iptv.application.use_cases.authenticate_provider import AuthenticateProvider
from samotech_iptv.application.use_cases.load_channels import LoadChannels
from samotech_iptv.application.use_cases.load_epg import LoadEPG
from samotech_iptv.application.use_cases.resolve_stream import ResolveStream
from samotech_iptv.domain.value_objects.provider_id import ProviderId
from samotech_iptv.infrastructure.configuration.configuration_provider import ConfigurationProvider
from samotech_iptv.infrastructure.providers.mag_adapter import register_with_factory
from samotech_iptv.infrastructure.providers.provider_context import ProviderContext
from samotech_iptv.infrastructure.providers.provider_factory import ProviderFactory
from samotech_iptv.infrastructure.providers.provider_metadata import InfraProviderMetadata
from samotech_iptv.infrastructure.providers.provider_registry import ProviderRegistry

if TYPE_CHECKING:
    from samotech_iptv.application.ports.provider_port import ProviderPort
    from samotech_iptv.domain.value_objects.credential import Credential

_AUTH_VALUE = "test-auth-value"
_SESSION_VALUE = "initial-session-value"
_REFRESHED_VALUE = "refreshed-session-value"


class InMemoryCredentialStore:
    """Minimal credential-store test double retaining the port's real semantics."""

    def __init__(self) -> None:
        self._credentials: dict[ProviderId, Credential] = {}

    async def store(self, provider_id: ProviderId, credential: Credential) -> None:
        self._credentials[provider_id] = credential

    async def retrieve(self, provider_id: ProviderId) -> Credential | None:
        return self._credentials.get(provider_id)

    async def delete(self, provider_id: ProviderId) -> None:
        self._credentials.pop(provider_id, None)


class ScenarioMagProvider:
    """A deterministic legacy-provider implementation with no network access."""

    def __init__(self, fail_authentication: bool = False) -> None:
        self._session = SimpleNamespace(token="")
        self._fail_authentication = fail_authentication
        self.connected = False
        self.received_epg_ids: list[int] | None = None

    async def connect(self) -> None:
        if self._fail_authentication:
            from providers.base.errors import AuthError

            raise AuthError("test subscription rejected")
        self.connected = True
        self._session.token = _SESSION_VALUE

    async def close(self) -> None:
        self.connected = False

    async def refresh_token(self) -> None:
        self._session.token = _REFRESHED_VALUE

    async def get_channels(self) -> list[dict[str, object]]:
        return [
            {
                "id": 7,
                "name": "Integration TV",
                "tv_genre_id": 3,
                "number": 7,
                "logo": "https://assets.example.test/integration-tv.png",
            }
        ]

    async def get_epg(
        self, channel_ids: list[int] | None = None, period: int = 3
    ) -> dict[int, list[dict[str, object]]]:
        self.received_epg_ids = channel_ids
        return {
            7: [
                {
                    "id": "integration-programme",
                    "name": "Integration Bulletin",
                    "start_timestamp": 1700000000,
                    "stop_timestamp": 1700003600,
                }
            ]
        }

    async def get_stream_url(self, stream_id: int, stream_type: str = "live") -> str:
        return f"https://stream.example.test/{stream_type}/{stream_id}.m3u8"


@pytest.fixture
def provider_path() -> tuple[ProviderPort, ScenarioMagProvider, InMemoryCredentialStore]:
    registry = ProviderRegistry()
    metadata = InfraProviderMetadata(
        provider_id="mag-integration",
        provider_type="mag",
        base_url="https://portal.example.test",
    )
    registry.register(metadata)
    context = ProviderContext.build(
        overrides={"connect_timeout": 5.0, "read_timeout": 10.0}, registry=registry
    )
    factory = ProviderFactory()
    register_with_factory(factory)
    legacy = ScenarioMagProvider()
    adapter = cast(
        "ProviderPort",
        factory.create(
            registry.get(metadata.provider_id), context=context, legacy_provider=legacy
        ),
    )
    return adapter, legacy, InMemoryCredentialStore()


@pytest.mark.asyncio
async def test_factory_to_use_case_path_translates_mag_to_application_dtos(
    provider_path: tuple[ProviderPort, ScenarioMagProvider, InMemoryCredentialStore],
) -> None:
    adapter, legacy, credential_store = provider_path
    auth = await AuthenticateProvider(adapter, credential_store).execute(
        AuthenticateRequest(
            provider_id="mag-integration",
            username="00:11:22:33:44:55",
            password=_AUTH_VALUE,
        )
    )
    assert auth.success is True
    assert legacy.connected is True
    assert (await credential_store.retrieve(ProviderId("mag-integration"))) is not None

    channels = await LoadChannels(adapter).execute(
        LoadChannelsRequest(provider_id="mag-integration")
    )
    assert channels.error is None
    assert channels.total == 1
    assert channels.channels[0].provider_id == "mag-integration"
    assert channels.channels[0].stream_id == "7"

    epg = await LoadEPG(adapter).execute(LoadEPGRequest(channel_id="7"))
    assert epg.error is None
    assert epg.entries[0].id == "integration-programme"
    assert legacy.received_epg_ids == [7]

    stream = await ResolveStream(adapter).execute(
        ResolveStreamRequest(channel_id="7", provider_id="mag-integration")
    )
    assert stream.error is None
    assert stream.url == "https://stream.example.test/live/7.m3u8"


@pytest.mark.asyncio
async def test_authentication_failure_stays_at_application_boundary() -> None:
    metadata = InfraProviderMetadata(
        provider_id="mag-failing", provider_type="mag", base_url="https://portal.example.test"
    )
    context = ProviderContext.build()
    factory = ProviderFactory()
    register_with_factory(factory)
    adapter = cast(
        "ProviderPort",
        factory.create(
            metadata, context=context, legacy_provider=ScenarioMagProvider(True)
        ),
    )
    response = await AuthenticateProvider(adapter, InMemoryCredentialStore()).execute(
        AuthenticateRequest(
            provider_id="mag-failing",
            username="00:11:22:33:44:55",
            password=_AUTH_VALUE,
        )
    )
    assert response.success is False
    assert response.error is not None


@pytest.mark.asyncio
async def test_invalid_application_credential_returns_a_failed_auth_response(
    provider_path: tuple[ProviderPort, ScenarioMagProvider, InMemoryCredentialStore],
) -> None:
    adapter, _, credential_store = provider_path
    response = await AuthenticateProvider(adapter, credential_store).execute(
        AuthenticateRequest(
            provider_id="mag-integration", username="", password=_AUTH_VALUE
        )
    )
    assert response.success is False
    assert response.error is not None


def test_configuration_is_the_single_composition_boundary() -> None:
    config = ConfigurationProvider(overrides={"log_level": "debug"}).app_config()
    assert config.log_level == "DEBUG"
