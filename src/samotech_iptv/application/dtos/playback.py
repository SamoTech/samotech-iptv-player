from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from samotech_iptv.application.dtos.content import ContentType
from samotech_iptv.core.exceptions import ValidationError

__all__ = [
    "PlaybackAttempt",
    "PlaybackOutcome",
    "PlaybackResult",
    "PlaybackTarget",
]


class PlaybackOutcome(StrEnum):
    """Safe application result states for one explicit playback attempt."""

    PLAYED = "played"
    STALE = "stale"
    UNSUPPORTED = "unsupported"
    FAILED = "failed"


@dataclass(frozen=True)
class PlaybackTarget:
    """Immutable, provider-scoped identity for one requested media item."""

    provider_id: str
    content_type: ContentType
    canonical_content_id: str
    resource_id: str | None = None
    parent_series_id: str | None = None
    season: int | None = None
    episode_number: int | None = None

    def __post_init__(self) -> None:
        for field_name, value in (
            ("provider_id", self.provider_id),
            ("canonical_content_id", self.canonical_content_id),
        ):
            if not value.strip():
                raise ValidationError(field_name, "must not be blank")
        if self.content_type not in {
            ContentType.LIVE,
            ContentType.MOVIE,
            ContentType.EPISODE,
        }:
            raise ValidationError("content_type", "must be live, movie, or episode")
        if self.content_type is ContentType.EPISODE:
            if not (self.parent_series_id or "").strip():
                raise ValidationError("parent_series_id", "is required for episode playback")
            if self.season is None or self.season < 1:
                raise ValidationError("season", "must be >= 1 for episode playback")
            if self.episode_number is None or self.episode_number < 1:
                raise ValidationError("episode_number", "must be >= 1 for episode playback")
        if (
            self.content_type in {ContentType.LIVE, ContentType.MOVIE, ContentType.EPISODE}
            and not (self.resource_id or "").strip()
        ):
            raise ValidationError("resource_id", "is required for playback")
        if self.resource_id is not None and "://" in self.resource_id:
            raise ValidationError("resource_id", "must not contain a resolved stream URL")

    @classmethod
    def live(
        cls, provider_id: str, channel_id: str, stream_id: str | None = None
    ) -> PlaybackTarget:
        """Build a Live target without exposing a resolved stream URL."""
        return cls(
            provider_id=provider_id,
            content_type=ContentType.LIVE,
            canonical_content_id=channel_id,
            resource_id=stream_id or channel_id,
        )

    @classmethod
    def movie(cls, provider_id: str, movie_id: str, resource_id: str) -> PlaybackTarget:
        """Build a safe Movie target without exposing a resolved stream URL."""
        return cls(
            provider_id=provider_id,
            content_type=ContentType.MOVIE,
            canonical_content_id=movie_id,
            resource_id=resource_id,
        )

    @classmethod
    def episode(
        cls,
        provider_id: str,
        episode_id: str,
        resource_id: str,
        parent_series_id: str,
        season: int,
        episode_number: int,
    ) -> PlaybackTarget:
        """Build a safe Episode target without exposing a resolved stream URL."""
        return cls(
            provider_id=provider_id,
            content_type=ContentType.EPISODE,
            canonical_content_id=episode_id,
            resource_id=resource_id,
            parent_series_id=parent_series_id,
            season=season,
            episode_number=episode_number,
        )


@dataclass(frozen=True)
class PlaybackAttempt:
    """One monotonically ordered request to play an immutable target."""

    generation: int
    target: PlaybackTarget


@dataclass(frozen=True)
class PlaybackResult:
    """Safe result of a playback attempt with no resolved URL disclosure."""

    attempt: PlaybackAttempt
    outcome: PlaybackOutcome
    error: str | None = None
