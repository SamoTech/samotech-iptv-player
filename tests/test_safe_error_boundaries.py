from __future__ import annotations

import logging

import pytest

from samotech_iptv.application.dtos import (
    AuthenticateRequest,
    LoadChannelsRequest,
    LoadEPGRequest,
    ResolveStreamRequest,
    SaveFavoriteRequest,
)
from samotech_iptv.application.use_cases.authenticate_provider import AuthenticateProvider
from samotech_iptv.application.use_cases.load_channels import LoadChannels
from samotech_iptv.application.use_cases.load_epg import LoadEPG
from samotech_iptv.application.use_cases.refresh_provider import (
    RefreshProvider,
    RefreshProviderRequest,
)
from samotech_iptv.application.use_cases.resolve_stream import ResolveStream
from samotech_iptv.application.use_cases.save_favorite import SaveFavorite
from samotech_iptv.core.exceptions import ValidationError
from samotech_iptv.domain.value_objects.provider_id import ProviderId
from samotech_iptv.domain.value_objects.stream_uri import StreamURI
from samotech_iptv.domain.value_objects.url import URL

_CANARY = "SAMOSAFE_APPLICATION_EXCEPTION_4f2a9d"


class _FailingProvider:
    provider_id = ProviderId("provider-safe")

    async def authenticate(self, _credential: object) -> bool:
        raise RuntimeError(_CANARY)

    async def load_channels(self) -> list[object]:
        raise RuntimeError(_CANARY)

    async def load_epg(self, _channel_id: object) -> list[object]:
        raise RuntimeError(_CANARY)

    async def refresh_session(self) -> bool:
        raise RuntimeError(_CANARY)

    async def resolve_stream(self, _channel_id: object) -> object:
        raise RuntimeError(_CANARY)


class _FailingCredentialStore:
    async def store(self, _provider_id: object, _credential: object) -> None:
        raise AssertionError("credential store should not run after authentication failure")


class _FailingFavoriteRepository:
    async def save(self, _favorite: object) -> None:
        raise RuntimeError(_CANARY)


def test_invalid_url_errors_do_not_expose_embedded_credentials() -> None:
    secret_parts = (
        "SAMOSAFE_URL_USER",
        "SAMOSAFE_URL_PASSWORD",
        "SAMOSAFE_URL_TOKEN",
    )
    for constructor in (URL, StreamURI):
        with pytest.raises(ValidationError) as caught:
            constructor(
                "file://SAMOSAFE_URL_USER:SAMOSAFE_URL_PASSWORD@host/path?token="
                "SAMOSAFE_URL_TOKEN"
            )
        message = str(caught.value)
        assert all(secret not in message for secret in secret_parts)


@pytest.mark.asyncio
async def test_application_error_boundaries_do_not_expose_exception_text(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
    provider = _FailingProvider()

    auth = await AuthenticateProvider(provider, _FailingCredentialStore()).execute(
        AuthenticateRequest("provider-safe", "user", "password")
    )
    channels = await LoadChannels(provider).execute(LoadChannelsRequest("provider-safe"))
    epg = await LoadEPG(provider).execute(LoadEPGRequest("channel-safe"))
    refreshed = await RefreshProvider(provider).execute(RefreshProviderRequest("provider-safe"))
    stream = await ResolveStream(provider).execute(
        ResolveStreamRequest("channel-safe", "provider-safe")
    )
    favorite = await SaveFavorite(_FailingFavoriteRepository()).execute(
        SaveFavoriteRequest("item-safe", "movie", "provider-safe")
    )

    responses = [
        auth.error,
        channels.error,
        epg.error,
        refreshed.error,
        stream.error,
        favorite.error,
    ]
    assert all(response for response in responses)
    assert all(_CANARY not in response for response in responses if response is not None)
    assert _CANARY not in " ".join(record.getMessage() for record in caplog.records)
