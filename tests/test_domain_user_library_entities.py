"""Tests for Favorite and History user-library domain invariants."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from samotech_iptv.core.exceptions import ValidationError
from samotech_iptv.domain.entities.favorite import Favorite
from samotech_iptv.domain.entities.history import History

_RECORDED_AT = datetime(2026, 8, 11, tzinfo=UTC)


def _favorite(
    *,
    record_id: str = "favorite-1",
    item_id: str = "item-1",
    item_type: str = "channel",
) -> Favorite:
    return Favorite(
        id=record_id,
        item_id=item_id,
        item_type=item_type,
        added_at=_RECORDED_AT,
    )


def _history(
    *,
    record_id: str = "history-1",
    item_id: str = "item-1",
    item_type: str = "channel",
    duration_seconds: int = 0,
    position_seconds: int = 0,
) -> History:
    return History(
        id=record_id,
        item_id=item_id,
        item_type=item_type,
        watched_at=_RECORDED_AT,
        duration_seconds=duration_seconds,
        position_seconds=position_seconds,
    )


@pytest.mark.parametrize("item_type", ["channel", "movie", "series"])
def test_favorite_accepts_each_supported_item_type(item_type: str) -> None:
    favorite = _favorite(item_type=item_type)

    assert favorite.item_type == item_type


def test_favorite_is_value_equal_and_hashable() -> None:
    first = _favorite()
    second = _favorite()

    assert first == second
    assert hash(first) == hash(second)


@pytest.mark.parametrize(
    ("record_id", "item_id", "item_type", "message"),
    [
        (" ", "item-1", "channel", "Record ID"),
        ("favorite-1", " ", "channel", "Item ID"),
        ("favorite-1", "item-1", "episode", "Favorite item type"),
    ],
)
def test_favorite_rejects_invalid_metadata(
    record_id: str,
    item_id: str,
    item_type: str,
    message: str,
) -> None:
    with pytest.raises(ValidationError, match=message):
        _favorite(record_id=record_id, item_id=item_id, item_type=item_type)


@pytest.mark.parametrize("item_type", ["channel", "movie", "episode"])
def test_history_accepts_each_supported_item_type(item_type: str) -> None:
    history = _history(item_type=item_type)

    assert history.item_type == item_type


def test_history_accepts_zero_positive_and_exact_known_playback_positions() -> None:
    zero_position = _history()
    positive_position = _history(item_type="movie", duration_seconds=120, position_seconds=60)
    completed = _history(item_type="episode", duration_seconds=120, position_seconds=120)

    assert zero_position.position_seconds == 0
    assert positive_position.position_seconds == 60
    assert completed.position_seconds == completed.duration_seconds


def test_history_allows_a_position_when_duration_is_unknown() -> None:
    live_history = _history(item_type="channel", duration_seconds=0, position_seconds=3600)

    assert live_history.duration_seconds == 0
    assert live_history.position_seconds == 3600


@pytest.mark.parametrize(
    ("record_id", "item_id", "item_type", "duration_seconds", "position_seconds", "message"),
    [
        (" ", "item-1", "channel", 0, 0, "Record ID"),
        ("history-1", " ", "channel", 0, 0, "Item ID"),
        ("history-1", "item-1", "series", 0, 0, "History item type"),
        ("history-1", "item-1", "channel", -1, 0, "Duration"),
        ("history-1", "item-1", "channel", 0, -1, "Playback position"),
        ("history-1", "item-1", "movie", 120, 121, "must not exceed"),
    ],
)
def test_history_rejects_invalid_metadata_or_playback_state(
    record_id: str,
    item_id: str,
    item_type: str,
    duration_seconds: int,
    position_seconds: int,
    message: str,
) -> None:
    with pytest.raises(ValidationError, match=message):
        _history(
            record_id=record_id,
            item_id=item_id,
            item_type=item_type,
            duration_seconds=duration_seconds,
            position_seconds=position_seconds,
        )
