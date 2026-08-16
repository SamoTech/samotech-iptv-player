"""Shared validation for user-library domain records."""

from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.core.exceptions import ValidationError

if TYPE_CHECKING:
    from datetime import datetime

FAVORITE_ITEM_TYPES = frozenset({"channel", "movie", "series"})
HISTORY_ITEM_TYPES = frozenset({"channel", "movie", "episode"})


def validate_favorite(
    *, record_id: str, item_id: str, item_type: str, provider_id: str | None = None
) -> None:
    """Validate a user-marked favourite against supported catalogue types."""
    _validate_identifiers(record_id=record_id, item_id=item_id)
    _validate_optional_provider_id(provider_id)
    _validate_item_type(item_type, FAVORITE_ITEM_TYPES, "Favorite")


def validate_history(
    *,
    record_id: str,
    item_id: str,
    item_type: str,
    duration_seconds: int,
    position_seconds: int,
    provider_id: str | None = None,
    watched_percentage: float = 0.0,
    completed: bool = False,
    started_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> None:
    """Validate a playback-history record and its known-duration semantics.

    A duration of zero represents an unknown duration. It intentionally does
    not impose an upper bound on the position, which preserves the current
    model for live streams and sources that cannot report a runtime.
    """
    _validate_identifiers(record_id=record_id, item_id=item_id)
    _validate_optional_provider_id(provider_id)
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
    if not 0.0 <= watched_percentage <= 100.0:
        raise ValidationError(
            "watched_percentage", "Watched percentage must be between zero and one hundred"
        )
    if completed and (duration_seconds <= 0 or watched_percentage < 100.0):
        raise ValidationError(
            "completed", "Only a fully watched known-duration item may be completed"
        )
    if started_at is not None and updated_at is not None and updated_at < started_at:
        raise ValidationError("updated_at", "Updated time must not precede started time")


def _validate_optional_provider_id(provider_id: str | None) -> None:
    if provider_id is not None and not provider_id.strip():
        raise ValidationError("provider_id", "Provider ID must not be blank")


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
