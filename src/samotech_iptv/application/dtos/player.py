"""Typed Player 2 capability, state, track, context, and diagnostic records."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from samotech_iptv.application.dtos.content import ContentType

__all__ = [
    "AudioTrack",
    "PlaybackContext",
    "PlaybackState",
    "PlayerCapabilities",
    "PlayerDiagnostics",
    "SubtitleTrack",
]


class PlaybackState(StrEnum):
    """Public lifecycle states emitted by the application-owned player service."""

    IDLE = "idle"
    LOADING = "loading"
    BUFFERING = "buffering"
    PLAYING = "playing"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ENDED = "ended"
    RECOVERING = "recovering"
    ERROR = "error"


@dataclass(frozen=True)
class AudioTrack:
    """One native audio-track description safe for presentation."""

    id: int
    language: str | None = None
    description: str | None = None
    active: bool = False


@dataclass(frozen=True)
class SubtitleTrack:
    """One native subtitle-track description safe for presentation."""

    id: int
    language: str | None = None
    description: str | None = None
    active: bool = False


@dataclass(frozen=True)
class PlaybackContext:
    """Provider-neutral identity associated with the current media generation."""

    title: str
    provider_id: str
    item_id: str
    content_type: ContentType
    media_generation: int


@dataclass(frozen=True)
class PlayerDiagnostics:
    """Aggregate diagnostics that never contain URLs, credentials, or raw payloads."""

    startup_latency_ms: float | None = None
    buffering_duration_ms: float | None = None
    recovery_attempts: int = 0
    terminal_failure_reason: str | None = None


@dataclass(frozen=True)
class PlayerCapabilities:
    """Explicit feature availability for the current PlayerPort implementation."""

    play: bool = True
    pause: bool = True
    resume: bool = True
    stop: bool = True
    restart: bool = False
    toggle_play_pause: bool = False
    current_position: bool = False
    duration: bool = False
    percentage: bool = False
    seek_forward: bool = False
    seek_backward: bool = False
    absolute_seek: bool = False
    volume: bool = False
    mute: bool = False
    audio_tracks: bool = False
    subtitle_tracks: bool = False
    fullscreen: bool = True
    aspect_ratio: bool = False
    video_output_attachment: bool = True
    recording: bool = True
    explicit_state: bool = False
    metadata: bool = False
    diagnostics: bool = True
