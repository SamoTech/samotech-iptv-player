"""Shared validation for user-library domain records."""

from __future__ import annotations

from samotech_iptv.core.exceptions import ValidationError

FAVORITE_ITEM_TYPES = frozenset({"channel", "movie", "series"})
HISTORY_ITEM_TYPES = frozenset({"channel", "movie", "episode"})


def validate_favorite(*, record_id: str, item_id: str, item_type: str) -> None:
    """Validate a user-marked favourite against supported catalogue types."""
    _validate_identifiers(record_id=record_id, item_id=item_id)
    _validate_item_type(item_type, FAVORITE_ITEM_TYPES, "Favorite")


def validate_history(
    *,
    record_id: str,
    item_id: str,
    item_type: str,
    duration_seconds: int,
    position_seconds: int,
) -> None:
    """Validate a playback-history record and its known-duration semantics.

    A duration of zero represents an unknown duration. It intentionally does
    not impose an upper bound on the position, which preserves the current
    model for live streams and sources that cannot report a runtime.
    """
    _validate_identifiers(record_id=record_id, item_id=item_id)
    _validate_item_type(item_type, HISTORY_ITEM_TYPES, "History")
    if duration_seconds < 0:
        raise ValidationError("duration_seconds", "Duration must not be negative")
    if position_seconds < 0:
        raise ValidationError("position_seconds", "Playback position must not be negative")
    if duration_seconds > 0 and position_seconds > duration_seconds:
        raise ValidationError(
            "position_seconds",
            "Playback position must not exceed a known duration",
        )


def _validate_identifiers(*, record_id: str, item_id: str) -> None:
    if not record_id.strip():
        raise ValidationError("id", "Record ID must not be blank")
    if not item_id.strip():
        raise ValidationError("item_id", "Item ID must not be blank")


def _validate_item_type(item_type: str, allowed_types: frozenset[str], record_name: str) -> None:
    if item_type not in allowed_types:
        allowed = ", ".join(sorted(allowed_types))
        raise ValidationError(
            "item_type",
            f"{record_name} item type must be one of: {allowed}",
        )
