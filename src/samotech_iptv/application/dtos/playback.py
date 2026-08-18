from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from samotech_iptv.application.dtos.content import ContentType
from samotech_iptv.core.exceptions import ValidationError
from samotech_iptv.domain.value_objects.url import URL

if TYPE_CHECKING:
    from samotech_iptv.domain.value_objects.stream_protocol import StreamTransport

__all__ = [
    "PlaybackAttempt",
    "PlaybackOutcome",
    "PlaybackResource",
    "PlaybackResult",
    "PlaybackTarget",
    "ResolvedPlayback",
    "TransportHeader",
    "TransportMetadata",
]


class PlaybackOutcome(StrEnum):
    """Safe application result states for one explicit playback attempt."""

    PLAYED = "played"
    STALE = "stale"
    UNSUPPORTED = "unsupported"
    FAILED = "failed"


@dataclass(frozen=True)
class TransportHeader:
    """One explicit, ephemeral HTTP header used only at the player boundary."""

    name: str
    value: str

    def __post_init__(self) -> None:
        if not self.name.strip() or any(char in self.name for char in "\r\n:"):
            raise ValidationError("header.name", "must be a valid non-blank header name")
        if any(char in self.value for char in "\r\n"):
            raise ValidationError("header.value", "must not contain line breaks")


@dataclass(frozen=True)
class TransportMetadata:
    """Typed, non-persistent transport requirements for one resolved stream."""

    headers: tuple[TransportHeader, ...] = ()
    user_agent: str | None = None
    referrer: str | None = None
    protocol_hint: StreamTransport | None = None
    container_hint: str | None = None

    def __post_init__(self) -> None:
        if self.user_agent is not None and not self.user_agent.strip():
            raise ValidationError("user_agent", "must not be blank when supplied")
        if self.referrer is not None and not self.referrer.strip():
            raise ValidationError("referrer", "must not be blank when supplied")
        if self.container_hint is not None and not self.container_hint.strip():
            raise ValidationError("container_hint", "must not be blank when supplied")
        names = [header.name.casefold() for header in self.headers]
        if len(names) != len(set(names)):
            raise ValidationError("headers", "must not contain duplicate names")


@dataclass(frozen=True)
class PlaybackResource:
    """Immutable logical playback identity, independent of provider transport."""

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
        if self.content_type not in {ContentType.LIVE, ContentType.MOVIE, ContentType.EPISODE}:
            raise ValidationError("content_type", "must be live, movie, or episode")
        if self.content_type is ContentType.EPISODE:
            if not (self.parent_series_id or "").strip():
                raise ValidationError("parent_series_id", "is required for episode playback")
            if self.season is None or self.season < 1:
                raise ValidationError("season", "must be >= 1 for episode playback")
            if self.episode_number is None or self.episode_number < 1:
                raise ValidationError("episode_number", "must be >= 1 for episode playback")
        if not (self.resource_id or "").strip():
            raise ValidationError("resource_id", "is required for playback")
        if self.resource_id is not None and "://" in self.resource_id:
            raise ValidationError("resource_id", "must not contain a resolved stream URL")

    @classmethod
    def live(
        cls, provider_id: str, channel_id: str, stream_id: str | None = None
    ) -> PlaybackResource:
        return cls(provider_id, ContentType.LIVE, channel_id, stream_id or channel_id)

    @classmethod
    def movie(cls, provider_id: str, movie_id: str, resource_id: str) -> PlaybackResource:
        return cls(provider_id, ContentType.MOVIE, movie_id, resource_id)

    @classmethod
    def episode(
        cls,
        provider_id: str,
        episode_id: str,
        resource_id: str,
        parent_series_id: str,
        season: int,
        episode_number: int,
    ) -> PlaybackResource:
        return cls(
            provider_id,
            ContentType.EPISODE,
            episode_id,
            resource_id,
            parent_series_id,
            season,
            episode_number,
        )


# Compatibility name for existing Phase 1 callers; the conceptual model is PlaybackResource.
PlaybackTarget = PlaybackResource


@dataclass(frozen=True, eq=False)
class ResolvedPlayback:
    """Ephemeral final playable target produced by a provider resolver."""

    url: URL
    transport: TransportMetadata = TransportMetadata()
    resource: PlaybackResource | None = None

    def __post_init__(self) -> None:
        if not self.url.value.strip():
            raise ValidationError("url", "must not be blank")

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ResolvedPlayback):
            return (
                self.url == other.url
                and self.transport == other.transport
                and self.resource == other.resource
            )
        if isinstance(other, URL):
            return self.url == other
        return NotImplemented

    def __str__(self) -> str:
        return self.url.value

    @property
    def value(self) -> str:
        """Compatibility accessor for legacy infrastructure assertions; not used by UI models."""
        return self.url.value

    @classmethod
    def from_url(
        cls,
        url: URL,
        *,
        transport: TransportMetadata | None = None,
        resource: PlaybackResource | None = None,
    ) -> ResolvedPlayback:
        return cls(
            url=url,
            transport=transport if transport is not None else TransportMetadata(),
            resource=resource,
        )


@dataclass(frozen=True)
class PlaybackAttempt:
    """One monotonically ordered request to play an immutable resource."""

    generation: int
    target: PlaybackResource


@dataclass(frozen=True)
class PlaybackResult:
    """Safe result of a playback attempt with no logging or persistence of transport secrets."""

    attempt: PlaybackAttempt
    outcome: PlaybackOutcome
    error: str | None = None
