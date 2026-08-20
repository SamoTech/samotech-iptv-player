from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from samotech_iptv.core.exceptions import ValidationError
from samotech_iptv.domain.entities import (
    AccountInfo,
    CatchupEvent,
    ProviderSession,
    ServerInfo,
    SubscriptionStatus,
)
from samotech_iptv.domain.value_objects.channel_id import ChannelId
from samotech_iptv.domain.value_objects.provider_id import ProviderId

PROVIDER = ProviderId("provider-1")
CHANNEL = ChannelId("channel-1")
START = datetime(2026, 8, 16, 12, 0, tzinfo=UTC)


def test_provider_session_contains_status_only_and_validates_expiry() -> None:
    session = ProviderSession(
        provider_id=PROVIDER,
        state="authenticated",
        established_at=START,
        expires_at=START + timedelta(hours=1),
    )

    assert session.provider_id == PROVIDER
    assert session.state == "authenticated"

    with pytest.raises(ValidationError):
        ProviderSession(
            provider_id=PROVIDER,
            state="authenticated",
            established_at=START,
            expires_at=START,
        )


def test_account_info_tolerates_optional_provider_metadata() -> None:
    account = AccountInfo(
        provider_id=PROVIDER,
        status="active",
        expires_at=START + timedelta(days=30),
        active_connections=1,
        max_connections=2,
    )

    assert account.status == "active"
    assert account.message is None

    with pytest.raises(ValidationError):
        AccountInfo(provider_id=PROVIDER, status="active", active_connections=-1)


def test_account_info_exposes_typed_expiration_without_inferring_provider_values() -> None:
    account = AccountInfo(
        provider_id=PROVIDER,
        status="active",
        expires_at=START + timedelta(days=1, hours=3),
        expiration_timezone="UTC",
        is_trial=True,
    )

    assert account.subscription_status is SubscriptionStatus.TRIAL
    assert account.expiration.is_expired_at(START) is False
    assert account.expiration.days_remaining_at(START) == 1
    assert account.expiration.hours_remaining_at(START) == 27
    assert (
        AccountInfo(provider_id=PROVIDER, status="active").expiration.is_expired_at(START) is None
    )


def test_server_info_excludes_private_url_and_accepts_sparse_metadata() -> None:
    server = ServerInfo(provider_id=PROVIDER, version="1.0", timezone="UTC")

    assert server.name is None
    assert server.version == "1.0"
    assert not hasattr(server, "url")


def test_catchup_event_preserves_event_identity_without_resolved_private_url() -> None:
    event = CatchupEvent(
        id="catchup-1",
        provider_id=PROVIDER,
        channel_id=CHANNEL,
        title="Archived programme",
        start=START,
        end=START + timedelta(minutes=30),
        stream_id="stream-1",
    )

    assert event.channel_id == CHANNEL
    assert event.stream_id == "stream-1"
    assert not hasattr(event, "url")

    with pytest.raises(ValidationError):
        CatchupEvent(
            id="catchup-1",
            provider_id=PROVIDER,
            channel_id=CHANNEL,
            title="Archived programme",
            start=START,
            end=START,
        )
