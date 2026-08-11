"""Tests for live-channel, episode, and EPG programme-record invariants."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from samotech_iptv.core.exceptions import ValidationError
from samotech_iptv.domain.entities.channel import Channel
from samotech_iptv.domain.entities.epg_entry import EPGEntry
from samotech_iptv.domain.entities.episode import Episode
from samotech_iptv.domain.value_objects.channel_id import ChannelId
from samotech_iptv.domain.value_objects.provider_id import ProviderId
from samotech_iptv.domain.value_objects.stream_id import StreamId


@pytest.fixture
def provider_id() -> ProviderId:
    """Return a reusable valid provider identity."""
    return ProviderId("programme-provider")


@pytest.fixture
def stream_id() -> StreamId:
    """Return a reusable valid stream identity."""
    return StreamId("programme-stream")


def test_channel_accepts_valid_catalogue_and_epg_metadata(
    provider_id: ProviderId, stream_id: StreamId
) -> None:
    """Channels retain valid optional catalogue and EPG reference metadata."""
    channel = Channel(
        id=ChannelId("news-24"),
        name="News 24",
        provider_id=provider_id,
        stream_id=stream_id,
        category_id="news",
        epg_channel_id="news.24",
        number=24,
    )

    assert channel.epg_channel_id == "news.24"


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("name", " ", "Channel name"),
        ("category_id", " ", "Category ID"),
        ("epg_channel_id", " ", "EPG channel ID"),
    ],
)
def test_channel_rejects_blank_required_or_supplied_text(
    provider_id: ProviderId,
    stream_id: StreamId,
    field: str,
    value: str,
    message: str,
) -> None:
    """A channel cannot carry blank labels or supplied foreign identifiers."""
    values: dict[str, object] = {
        "id": ChannelId("news-24"),
        "name": "News 24",
        "provider_id": provider_id,
        "stream_id": stream_id,
        "category_id": "news",
        "epg_channel_id": "news.24",
    }
    values[field] = value

    with pytest.raises(ValidationError, match=message):
        Channel(**values)  # type: ignore[arg-type]


def test_channel_uses_value_semantics(provider_id: ProviderId, stream_id: StreamId) -> None:
    """Equivalent immutable Channel records compare and hash equally."""
    first = Channel(
        id=ChannelId("news-24"),
        name="News 24",
        provider_id=provider_id,
        stream_id=stream_id,
    )
    second = Channel(
        id=ChannelId("news-24"),
        name="News 24",
        provider_id=provider_id,
        stream_id=stream_id,
    )

    assert first == second
    assert hash(first) == hash(second)


def test_episode_accepts_complete_valid_metadata(stream_id: StreamId) -> None:
    """Episodes accept valid identity, series linkage, numbering, and duration."""
    episode = Episode(
        id="pilot",
        series_id="example-series",
        title="Pilot",
        stream_id=stream_id,
        season=1,
        episode_number=1,
        duration_seconds=2700,
    )

    assert episode.duration_seconds == 2700


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("id", " ", "Episode ID"),
        ("series_id", " ", "Series ID"),
        ("title", " ", "Episode title"),
        ("duration_seconds", -1, "Episode duration"),
        ("season", 0, "Season number"),
        ("episode_number", 0, "Episode number"),
    ],
)
def test_episode_rejects_invalid_metadata(
    stream_id: StreamId, field: str, value: str | int, message: str
) -> None:
    """Episodes reject blank identity metadata and invalid numeric boundaries."""
    values: dict[str, object] = {
        "id": "pilot",
        "series_id": "example-series",
        "title": "Pilot",
        "stream_id": stream_id,
        "season": 1,
        "episode_number": 1,
        "duration_seconds": 2700,
    }
    values[field] = value

    with pytest.raises(ValidationError, match=message):
        Episode(**values)  # type: ignore[arg-type]


def test_episode_uses_value_semantics(stream_id: StreamId) -> None:
    """Equivalent immutable Episode records compare and hash equally."""
    first = Episode(
        id="pilot",
        series_id="example-series",
        title="Pilot",
        stream_id=stream_id,
        season=1,
        episode_number=1,
    )
    second = Episode(
        id="pilot",
        series_id="example-series",
        title="Pilot",
        stream_id=stream_id,
        season=1,
        episode_number=1,
    )

    assert first == second
    assert hash(first) == hash(second)


def test_epg_entry_accepts_valid_programme_metadata() -> None:
    """An EPG entry accepts valid identity, title, and ordered timestamps."""
    start = datetime(2026, 8, 11, 18, 0, tzinfo=UTC)
    entry = EPGEntry(
        id="news-24:1800",
        channel_id=ChannelId("news-24"),
        title="Evening news",
        start=start,
        end=start + timedelta(minutes=30),
        description="A daily round-up.",
        category="News",
    )

    assert entry.category == "News"


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("id", " ", "EPG entry ID"),
        ("title", " ", "EPG entry title"),
    ],
)
def test_epg_entry_rejects_blank_required_text(field: str, value: str, message: str) -> None:
    """EPG entries cannot use blank programme identifiers or titles."""
    start = datetime(2026, 8, 11, 18, 0, tzinfo=UTC)
    values: dict[str, object] = {
        "id": "news-24:1800",
        "channel_id": ChannelId("news-24"),
        "title": "Evening news",
        "start": start,
        "end": start + timedelta(minutes=30),
    }
    values[field] = value

    with pytest.raises(ValidationError, match=message):
        EPGEntry(**values)  # type: ignore[arg-type]


def test_epg_entry_rejects_nonpositive_time_range() -> None:
    """Programme end time must strictly follow the programme start time."""
    start = datetime(2026, 8, 11, 18, 0, tzinfo=UTC)

    with pytest.raises(ValidationError, match="EPG end time"):
        EPGEntry(
            id="news-24:1800",
            channel_id=ChannelId("news-24"),
            title="Evening news",
            start=start,
            end=start,
        )


def test_epg_entry_uses_value_semantics() -> None:
    """Equivalent immutable EPGEntry records compare and hash equally."""
    start = datetime(2026, 8, 11, 18, 0, tzinfo=UTC)
    first = EPGEntry(
        id="news-24:1800",
        channel_id=ChannelId("news-24"),
        title="Evening news",
        start=start,
        end=start + timedelta(minutes=30),
    )
    second = EPGEntry(
        id="news-24:1800",
        channel_id=ChannelId("news-24"),
        title="Evening news",
        start=start,
        end=start + timedelta(minutes=30),
    )

    assert first == second
    assert hash(first) == hash(second)
