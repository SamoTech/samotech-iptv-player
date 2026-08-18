"""libVLC-backed implementation of playback and active-stream recording."""

from __future__ import annotations

import asyncio
import sys
import time
from enum import StrEnum
from itertools import count
from pathlib import Path
from threading import Lock, current_thread
from typing import Literal, Protocol
from urllib.parse import urlsplit

import vlc  # type: ignore[import-untyped]

from samotech_iptv.application.dtos.content import ContentType
from samotech_iptv.application.dtos.playback import ResolvedPlayback
from samotech_iptv.application.dtos.player import (
    AudioTrack,
    PlaybackState,
    PlayerCapabilities,
    SubtitleTrack,
)
from samotech_iptv.application.player_state_machine import PlaybackStateMachine
from samotech_iptv.application.ports.player_port import PlayerPort
from samotech_iptv.core.logging import get_logger
from samotech_iptv.core.safe_logging import safe_label
from samotech_iptv.domain.value_objects.url import URL

__all__ = ["VlcPlayerAdapter"]

_LOG = get_logger(__name__)
PlaybackMode = Literal["auto", "hardware", "software"]
_CommandAction = Literal["play", "stop", "pause", "release"]
_CommandCause = Literal[
    "initial_start",
    "channel_switch",
    "explicit_stop",
    "immediate_play_failure",
    "shutdown",
    "recording_restart",
    "explicit_pause",
    "explicit_resume",
    "live_recovery",
]
_RecoveryReason = Literal[
    "EOF",
    "STOPPED",
    "BUFFERING_TIMEOUT",
    "START_TIMEOUT",
    "ENCOUNTERED_ERROR",
    "STALLED",
]
_PLAYER_IDS = count(1)


class _PlaybackState(StrEnum):
    """Internal live-input lifecycle; no UI state contract is exposed."""

    IDLE = "IDLE"
    STARTING = "STARTING"
    PLAYING = "PLAYING"
    BUFFERING = "BUFFERING"
    RECOVERING = "RECOVERING"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    FAILED = "FAILED"
    ENDED = "ENDED"


class _VlcMedia(Protocol):
    def add_option(self, option: str) -> None: ...

    def slaves_clear(self) -> object: ...


class _VlcInstance(Protocol):
    def media_player_new(self) -> _VlcPlayer: ...

    def media_new(self, url: str) -> _VlcMedia: ...


class _VlcPlayer(Protocol):
    def is_playing(self) -> int: ...

    def set_media(self, media: _VlcMedia) -> None: ...

    def play(self) -> int: ...

    def stop(self) -> None: ...

    def pause(self) -> None: ...

    def get_time(self) -> int: ...

    def get_length(self) -> int: ...

    def set_time(self, i_time: int) -> object: ...

    def get_position(self) -> float: ...

    def set_position(self, f_pos: float) -> object: ...

    def audio_get_volume(self) -> int: ...

    def audio_set_volume(self, i_volume: int) -> int: ...

    def audio_get_mute(self) -> int: ...

    def audio_toggle_mute(self) -> object: ...

    def audio_get_track_description(self) -> object: ...

    def audio_get_track(self) -> int: ...

    def audio_set_track(self, track_id: int) -> object: ...

    def video_get_spu_description(self) -> object: ...

    def video_get_spu(self) -> int: ...

    def video_set_spu(self, track_id: int) -> object: ...

    def video_get_spu_delay(self) -> int: ...

    def video_set_spu_delay(self, delay_us: int) -> int: ...

    def add_slave(self, i_type: object, psz_uri: str, b_select: bool) -> int: ...

    def video_get_aspect_ratio(self) -> object: ...

    def video_set_aspect_ratio(self, aspect_ratio: str | None) -> object: ...

    def set_xwindow(self, native_window_id: int) -> None: ...

    def set_hwnd(self, native_window_id: int) -> None: ...

    def set_nsobject(self, native_window_id: int) -> None: ...


class VlcPlayerAdapter(PlayerPort):
    """Adapt the sole libVLC media player to application playback and recording operations."""

    def __init__(
        self,
        instance: _VlcInstance | None = None,
        player: _VlcPlayer | None = None,
        *,
        playback_mode: PlaybackMode = "auto",
        network_caching_ms: int = 1000,
        play_retry_count: int = 1,
        live_recovery_max_attempts: int = 5,
        live_recovery_window_s: float = 45.0,
        live_recovery_initial_delay_s: float = 1.0,
        live_recovery_max_delay_s: float = 8.0,
        live_buffering_timeout_s: float = 10.0,
        live_recovery_stability_s: float = 5.0,
        live_stall_timeout_s: float = 15.0,
    ) -> None:
        if playback_mode not in {"auto", "hardware", "software"}:
            raise ValueError("playback_mode must be auto, hardware, or software")
        if network_caching_ms < 0:
            raise ValueError("network_caching_ms must not be negative")
        if play_retry_count < 0:
            raise ValueError("play_retry_count must not be negative")
        if live_recovery_max_attempts < 0:
            raise ValueError("live_recovery_max_attempts must not be negative")
        if (
            min(
                live_recovery_window_s,
                live_recovery_initial_delay_s,
                live_recovery_max_delay_s,
                live_buffering_timeout_s,
                live_recovery_stability_s,
                live_stall_timeout_s,
            )
            < 0
        ):
            raise ValueError("live recovery durations must not be negative")
        self._instance = instance or vlc.Instance()
        self._player = player or self._instance.media_player_new()
        self._current_playback: ResolvedPlayback | None = None
        self._current_media: _VlcMedia | None = None
        self._recording_destination: Path | None = None
        self._playback_mode = playback_mode
        self._network_caching_ms = network_caching_ms
        self._play_retry_count = play_retry_count
        self._live_recovery_max_attempts = live_recovery_max_attempts
        self._live_recovery_window_s = live_recovery_window_s
        self._live_recovery_initial_delay_s = live_recovery_initial_delay_s
        self._live_recovery_max_delay_s = live_recovery_max_delay_s
        self._live_buffering_timeout_s = live_buffering_timeout_s
        self._live_recovery_stability_s = live_recovery_stability_s
        self._live_stall_timeout_s = live_stall_timeout_s
        self._live_liveness_poll_s = max(0.05, min(2.0, live_stall_timeout_s / 3))
        self._play_lock = asyncio.Lock()
        self._closed = False
        self._player_id = next(_PLAYER_IDS)
        self._created_at = time.perf_counter()
        self._diagnostic_lock = Lock()
        self._media_generation = 0
        self._media_created_at: float | None = None
        self._event_sequence = 0
        self._event_subscription_count = 0
        self._last_command_cause: _CommandCause | None = None
        self._state = _PlaybackState.IDLE
        self._state_machine = PlaybackStateMachine()
        self._session_token = 0
        self._intentional_action = False
        self._event_loop: asyncio.AbstractEventLoop | None = None
        self._event_manager: object | None = None
        self._event_subscriptions: list[tuple[object, object]] = []
        self._recovery_task: asyncio.Task[None] | None = None
        self._watchdog_task: asyncio.Task[None] | None = None
        self._stability_task: asyncio.Task[None] | None = None
        self._liveness_task: asyncio.Task[None] | None = None
        self._last_media_position_ms = -1
        self._last_position_advance_at: float | None = None
        self._recovery_attempts = 0
        self._recovery_started_at: float | None = None
        self._subscribe_events()
        _LOG.info(
            "[IPTV] PLAYBACK_DIAGNOSTIC CONSTRUCT player_id=%d instance_args=none "
            "playback_mode=%s network_cache_ms=%d event_subscriptions=%d",
            self._player_id,
            self._playback_mode,
            self._network_caching_ms,
            self._event_subscription_count,
        )

    def _subscribe_events(self) -> None:
        """Attach best-effort libVLC lifecycle events when the backend exposes them."""
        event_manager_factory = getattr(self._player, "event_manager", None)
        event_types = getattr(vlc, "EventType", None)
        if not callable(event_manager_factory) or event_types is None:
            return
        try:
            event_manager = event_manager_factory()
            self._event_manager = event_manager
            event_names = {
                "MediaPlayerOpening": "CONNECTING",
                "MediaPlayerBuffering": "BUFFERING",
                "MediaPlayerPlaying": "PLAYING",
                "MediaPlayerEncounteredError": "ERROR",
                "MediaPlayerEndReached": "END",
                "MediaPlayerStopped": "STOPPED",
            }
            for event_name, label in event_names.items():
                event_type = getattr(event_types, event_name, None)
                if event_type is not None:

                    def callback(_event: object, event_label: str = label) -> None:
                        self._on_native_event(event_label)

                    event_manager.event_attach(event_type, callback)
                    self._event_subscriptions.append((event_type, callback))
                    self._event_subscription_count += 1
                    _LOG.info(
                        "[IPTV] PLAYBACK_DIAGNOSTIC SUBSCRIBE player_id=%d event=%s "
                        "subscription_ordinal=%d event_subscriptions=%d",
                        self._player_id,
                        event_name,
                        self._event_subscription_count,
                        self._event_subscription_count,
                    )
        except Exception:  # noqa: BLE001
            _LOG.debug("[IPTV] PLAYBACK event subscription unavailable", exc_info=True)

    def _on_native_event(self, event_name: str) -> None:
        """Log one libVLC callback and route recovery work to the owning event loop."""
        media_generation, session_token = self._log_event(event_name)
        event_loop = self._event_loop
        if event_loop is None or event_loop.is_closed():
            return
        event_loop.call_soon_threadsafe(
            self._schedule_native_event,
            event_name,
            media_generation,
            session_token,
        )

    def _schedule_native_event(
        self,
        event_name: str,
        media_generation: int,
        session_token: int,
    ) -> None:
        """Create recovery handling work only after the native callback returns."""
        if self._closed:
            return
        asyncio.create_task(
            self._handle_native_event(event_name, media_generation, session_token),
            name=f"iptv-vlc-event-{self._player_id}-{media_generation}-{event_name.lower()}",
        )

    @property
    def state(self) -> PlaybackState:
        """Return the current public playback state snapshot value."""
        return self._state_machine.snapshot.state

    @property
    def capabilities(self) -> PlayerCapabilities:
        """Return capabilities implemented by this adapter without speculative features."""
        return PlayerCapabilities(
            current_position=True,
            duration=True,
            percentage=True,
            seek_forward=True,
            seek_backward=True,
            absolute_seek=True,
            volume=True,
            mute=True,
            audio_tracks=True,
            subtitle_tracks=True,
            local_subtitles=True,
            subtitle_delay=True,
            explicit_state=True,
            diagnostics=True,
        )

    @property
    def media_generation(self) -> int:
        """Return the current opaque media generation for session-safe UI operations."""
        return self._media_generation

    @property
    def is_playing(self) -> bool:
        """Return whether libVLC reports active playback."""
        return bool(self._player.is_playing())

    @property
    def is_recording(self) -> bool:
        """Return whether the active libVLC media contains a recording output."""
        return self._recording_destination is not None

    async def play(self, playback: ResolvedPlayback) -> None:
        """Stop prior media, then start one stream with bounded retry and diagnostics."""
        if isinstance(playback, URL):
            playback = ResolvedPlayback.from_url(playback)
        started = time.perf_counter()
        async with self._play_lock:
            self._event_loop = asyncio.get_running_loop()
            await self._invalidate_recovery(_PlaybackState.STARTING)
            if self._current_playback is not None or self.is_playing:
                _LOG.info("[IPTV] PLAYBACK STOPPED reason=channel_switch")
                await self._stop_and_release_media("channel_switch")
            _LOG.info("[IPTV] PLAYBACK START")
            self._current_playback = playback
            last_error: Exception | None = None
            for attempt in range(self._play_retry_count + 1):
                try:
                    await self._set_media_and_play(
                        playback,
                        software_fallback=attempt > 0,
                        cause=("initial_start" if attempt == 0 else "immediate_play_failure"),
                    )
                    self._recording_destination = None
                    self._intentional_action = False
                    provider_id, media_type, content_id, transport_type = self._playback_context()
                    _LOG.info(
                        "[IPTV] PLAYBACK PLAYING elapsed=%.3fs retry=%d "
                        "provider_id=%s media_type=%s content_id=%s "
                        "transport_type=%s",
                        time.perf_counter() - started,
                        attempt,
                        provider_id,
                        media_type,
                        content_id,
                        transport_type,
                    )
                    return
                except Exception as exc:  # noqa: BLE001
                    last_error = exc
                    _LOG.warning(
                        "[IPTV] PLAYBACK ERROR error_type=%s retry=%d",
                        type(exc).__name__,
                        attempt,
                    )
                    await self._stop_and_release_media("immediate_play_failure")
                    if attempt < self._play_retry_count:
                        _LOG.info("[IPTV] PLAYBACK RETRY retry=%d mode=software", attempt + 1)
            self._current_playback = None
            self._current_media = None
            self._publish_state(_PlaybackState.FAILED, reason="playback_failed")
            if last_error is None:
                raise RuntimeError("Unable to start playback")
            raise RuntimeError("Unable to start playback") from last_error

    async def restart(self) -> None:
        """Restart the current media through the existing serialized lifecycle path."""
        async with self._play_lock:
            if self._current_playback is None:
                raise RuntimeError("Cannot restart without active playback")
            playback = self._current_playback
            await self._invalidate_recovery(_PlaybackState.STARTING, intentional=True)
            await self._stop_and_release_media("channel_switch")
            await self._set_media_and_play(playback, cause="channel_switch")
            self._recording_destination = None
            self._intentional_action = False

    async def stop(self) -> None:
        """Stop libVLC playback and terminate any active recording output."""
        async with self._play_lock:
            await self._invalidate_recovery(_PlaybackState.STOPPING, intentional=True)
            await self._stop_and_release_media("explicit_stop")
            self._current_playback = None
            self._recording_destination = None
            self._publish_state(_PlaybackState.STOPPED, reason="explicit_stop")
            _LOG.info("[IPTV] PLAYBACK STOPPED")

    async def close(self) -> None:
        """Stop playback and release the owned libVLC player and instance exactly once."""
        async with self._play_lock:
            if self._closed:
                return
            self._closed = True
            await self._invalidate_recovery(_PlaybackState.STOPPING, intentional=True)
            self._current_playback = None
            self._recording_destination = None
            self._unsubscribe_events()
            try:
                await self._stop_and_release_media("shutdown")
                self._publish_state(_PlaybackState.STOPPED, reason="shutdown")
            except Exception:  # noqa: BLE001
                _LOG.debug("[IPTV] PLAYBACK stop during shutdown failed", exc_info=True)
            try:
                await self._release(self._player, "player")
            finally:
                await self._release(self._instance, "instance")
            _LOG.info(
                "[IPTV] PLAYBACK_DIAGNOSTIC RELEASED player_id=%d media_generation=%d "
                "last_command_cause=%s elapsed_ms=%.3f",
                self._player_id,
                self._media_generation,
                self._diagnostic_cause(),
                (time.perf_counter() - self._created_at) * 1_000,
            )
            _LOG.info("[IPTV] PLAYBACK RELEASED")

    async def get_position_ms(self) -> int | None:
        """Read current libVLC media time without exposing backend objects."""
        value = await asyncio.to_thread(self._player.get_time)
        return None if value < 0 else int(value)

    async def get_duration_ms(self) -> int | None:
        """Read current libVLC media duration without conflating no-media with zero."""
        value = await asyncio.to_thread(self._player.get_length)
        return None if value < 0 else int(value)

    async def seek_ms(self, position_ms: int) -> None:
        """Seek to an absolute millisecond position when the active input supports it."""
        if position_ms < 0:
            raise ValueError("position_ms must not be negative")
        async with self._play_lock:
            result = await asyncio.to_thread(self._player.set_time, position_ms)
            if isinstance(result, int) and result < 0:
                raise RuntimeError("libVLC seek failed")

    async def seek_fraction(self, position: float) -> None:
        """Seek to an absolute fraction in the inclusive zero-to-one range."""
        if not 0.0 <= position <= 1.0:
            raise ValueError("position must be between zero and one")
        async with self._play_lock:
            result = await asyncio.to_thread(self._player.set_position, position)
            if isinstance(result, int) and result < 0:
                raise RuntimeError("libVLC seek failed")

    async def get_volume(self) -> int | None:
        """Read native software volume, returning None when libVLC has no value."""
        value = await asyncio.to_thread(self._player.audio_get_volume)
        return None if value < 0 else int(value)

    async def set_volume(self, volume: int) -> None:
        """Set native software volume in the documented zero-to-one-hundred range."""
        if not 0 <= volume <= 100:
            raise ValueError("volume must be between zero and one hundred")
        async with self._play_lock:
            result = await asyncio.to_thread(self._player.audio_set_volume, volume)
            if result < 0:
                raise RuntimeError("libVLC volume change failed")

    async def is_muted(self) -> bool | None:
        """Read native mute state when available."""
        value = await asyncio.to_thread(self._player.audio_get_mute)
        return None if value < 0 else bool(value)

    async def set_muted(self, muted: bool) -> None:
        """Set mute state by toggling only when the native state differs."""
        async with self._play_lock:
            current = await asyncio.to_thread(self._player.audio_get_mute)
            if current < 0:
                raise RuntimeError("libVLC mute state unavailable")
            if bool(current) == muted:
                return
            await asyncio.to_thread(self._player.audio_toggle_mute)

    @staticmethod
    def _parse_track_descriptions(raw: object) -> tuple[tuple[int, str | None], ...]:
        """Convert python-vlc's list[(id, name)] safely, skipping malformed records."""
        if not isinstance(raw, (list, tuple)):
            return ()
        parsed: list[tuple[int, str | None]] = []
        for entry in raw:
            if not isinstance(entry, (list, tuple)) or len(entry) < 2:
                continue
            raw_id, raw_name = entry[0], entry[1]
            if isinstance(raw_id, bool):
                continue
            try:
                track_id = int(raw_id)
            except (TypeError, ValueError):
                continue
            if track_id < 0:
                continue
            if raw_name is None:
                description = None
            elif isinstance(raw_name, bytes):
                description = raw_name.decode("utf-8", errors="replace").strip() or None
            elif isinstance(raw_name, str):
                description = raw_name.strip() or None
            else:
                description = str(raw_name).strip() or None
            parsed.append((track_id, description))
        return tuple(parsed)

    async def get_audio_tracks(self) -> tuple[AudioTrack, ...]:
        """Enumerate native audio tracks and mark the native active track."""
        raw, active_id = await asyncio.gather(
            asyncio.to_thread(self._player.audio_get_track_description),
            asyncio.to_thread(self._player.audio_get_track),
        )
        active = active_id if isinstance(active_id, int) else -1
        return tuple(
            AudioTrack(id=track_id, description=description, active=track_id == active)
            for track_id, description in self._parse_track_descriptions(raw)
        )

    async def select_audio_track(self, track_id: int) -> None:
        """Select only an audio track reported by the current native media input."""
        if isinstance(track_id, bool) or track_id < 0:
            raise ValueError("track_id must be a non-negative integer")
        async with self._play_lock:
            available = self._parse_track_descriptions(
                await asyncio.to_thread(self._player.audio_get_track_description)
            )
            if track_id not in {item[0] for item in available}:
                raise ValueError("audio track is unavailable")
            result = await asyncio.to_thread(self._player.audio_set_track, track_id)
            if isinstance(result, int) and result < 0:
                raise RuntimeError("libVLC audio track selection failed")

    async def get_subtitle_tracks(self) -> tuple[SubtitleTrack, ...]:
        """Enumerate native subtitle tracks and mark the native active track."""
        raw, active_id = await asyncio.gather(
            asyncio.to_thread(self._player.video_get_spu_description),
            asyncio.to_thread(self._player.video_get_spu),
        )
        active = active_id if isinstance(active_id, int) else -1
        return tuple(
            SubtitleTrack(id=track_id, description=description, active=track_id == active)
            for track_id, description in self._parse_track_descriptions(raw)
        )

    async def select_subtitle_track(self, track_id: int | None) -> None:
        """Select a reported subtitle track or disable subtitles with native ID -1."""
        if track_id is not None and (isinstance(track_id, bool) or track_id < 0):
            raise ValueError("track_id must be None or a non-negative integer")
        async with self._play_lock:
            native_id = -1 if track_id is None else track_id
            if track_id is not None:
                available = self._parse_track_descriptions(
                    await asyncio.to_thread(self._player.video_get_spu_description)
                )
                if track_id not in {item[0] for item in available}:
                    raise ValueError("subtitle track is unavailable")
            result = await asyncio.to_thread(self._player.video_set_spu, native_id)
            if isinstance(result, int) and result < 0:
                raise RuntimeError("libVLC subtitle track selection failed")

    async def clear_local_subtitles(self) -> None:
        """Remove locally attached subtitle slaves from the current media."""
        async with self._play_lock:
            if self._closed or self._current_media is None:
                raise RuntimeError("No active media for local subtitle removal")
            await asyncio.to_thread(self._current_media.slaves_clear)

    async def get_subtitle_delay_ms(self) -> int | None:
        """Read native subtitle delay in milliseconds when libVLC reports it."""
        value = await asyncio.to_thread(self._player.video_get_spu_delay)
        return None if not isinstance(value, int) else int(value / 1_000)

    async def set_subtitle_delay_ms(self, delay_ms: int) -> None:
        """Set native subtitle delay in the bounded commercial control range."""
        if isinstance(delay_ms, bool) or not -5_000 <= delay_ms <= 5_000:
            raise ValueError("subtitle delay must be between -5000 and 5000 milliseconds")
        async with self._play_lock:
            result = await asyncio.to_thread(
                self._player.video_set_spu_delay,
                delay_ms * 1_000,
            )
            if isinstance(result, int) and result < 0:
                raise RuntimeError("libVLC subtitle delay change failed")

    async def attach_local_subtitle(
        self,
        path: Path,
        *,
        expected_generation: int | None = None,
    ) -> None:
        """Attach a local subtitle to current media without restarting or crossing generations."""
        allowed_suffixes = {".srt", ".ass", ".ssa", ".vtt"}
        candidate = Path(path).expanduser()
        if candidate.suffix.casefold() not in allowed_suffixes:
            raise ValueError("Unsupported local subtitle format")
        try:
            resolved = candidate.resolve(strict=True)
            stat = resolved.stat()
        except OSError as exc:
            raise ValueError("Local subtitle file is unavailable") from exc
        if not resolved.is_file() or stat.st_size <= 0:
            raise ValueError("Local subtitle file is unavailable")
        if stat.st_size > 16 * 1024 * 1024:
            raise ValueError("Local subtitle file is too large")
        async with self._play_lock:
            if self._closed or self._current_playback is None:
                raise RuntimeError("No active media for local subtitle")
            if expected_generation is not None and expected_generation != self._media_generation:
                raise RuntimeError("Playback session changed before subtitle attachment")
            media_slave_type = getattr(vlc, "MediaSlaveType", None)
            subtitle_type = getattr(media_slave_type, "subtitle", None)
            if subtitle_type is None:
                raise RuntimeError("libVLC local subtitle support is unavailable")
            result = await asyncio.to_thread(
                self._player.add_slave,
                subtitle_type,
                resolved.as_uri(),
                True,
            )
            if isinstance(result, int) and result < 0:
                raise RuntimeError("libVLC local subtitle attachment failed")

    async def get_aspect_ratio(self) -> str | None:
        """Read the native aspect-ratio override, decoding bytes without leaking raw data."""
        raw = await asyncio.to_thread(self._player.video_get_aspect_ratio)
        if raw is None:
            return None
        if isinstance(raw, bytes):
            value = raw.decode("ascii", errors="ignore").strip()
        elif isinstance(raw, str):
            value = raw.strip()
        else:
            value = str(raw).strip()
        return value or None

    async def set_aspect_ratio(self, aspect_ratio: str | None) -> None:
        """Set or clear one of the fixed, presentation-approved aspect-ratio values."""
        allowed = {None, "1:1", "4:3", "5:4", "16:9", "16:10", "221:100", "4:5"}
        if aspect_ratio not in allowed:
            raise ValueError("unsupported aspect ratio")
        async with self._play_lock:
            result = await asyncio.to_thread(
                self._player.video_set_aspect_ratio,
                aspect_ratio,
            )
            if isinstance(result, int) and result < 0:
                raise RuntimeError("libVLC aspect ratio change failed")

    async def pause(self) -> None:
        """Pause libVLC playback while preserving an active recording configuration."""
        async with self._play_lock:
            await self._invalidate_recovery(_PlaybackState.STOPPED, intentional=True)
            await self._invoke("pause", "explicit_pause")
            self._state_machine.reset_context(
                media_generation=self._media_generation,
                session_token=self._session_token,
                state=PlaybackState.PAUSED,
                reason="explicit_pause",
            )
            _LOG.info("[IPTV] PLAYBACK PAUSED")

    async def resume(self) -> None:
        """Resume libVLC playback while preserving an active recording configuration."""
        async with self._play_lock:
            self._event_loop = asyncio.get_running_loop()
            self._intentional_action = False
            self._publish_state(
                _PlaybackState.STARTING, reason="explicit_resume", reset_context=True
            )
            await self._invoke("play", "explicit_resume")
            _LOG.info("[IPTV] PLAYBACK PLAYING state=resumed")

    async def start_recording(self, destination: Path) -> None:
        """Restart active media with one libVLC display/file duplicate stream output."""
        async with self._play_lock:
            if self._current_playback is None or not self.is_playing:
                raise RuntimeError("Cannot record without active playback")
            if self._recording_destination is not None:
                raise RuntimeError("Recording is already active")
            output_path = destination.expanduser().resolve()
            if output_path.suffix.lower() != ".ts":
                raise ValueError("Recording destination must use the .ts extension")
            if output_path.exists():
                raise FileExistsError("Recording destination already exists")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            await self._invalidate_recovery(_PlaybackState.STARTING, intentional=True)
            await self._stop_and_release_media("recording_restart")
            media = self._new_media(self._current_playback, software_fallback=False)
            media.add_option(self._recording_option(output_path))
            self._current_media = media
            try:
                self._player.set_media(media)
                await self._invoke("play", "recording_restart")
            except Exception:
                await self._release_current_media()
                raise
            self._recording_destination = output_path

    async def stop_recording(self) -> None:
        """Restart active media without stream output while continuing normal playback."""
        async with self._play_lock:
            if self._recording_destination is None or self._current_playback is None:
                raise RuntimeError("No active recording")
            await self._invalidate_recovery(_PlaybackState.STARTING, intentional=True)
            await self._stop_and_release_media("recording_restart")
            await self._set_media_and_play(
                self._current_playback,
                software_fallback=False,
                cause="recording_restart",
            )
            self._recording_destination = None

    def attach_video_output(self, native_window_id: int) -> None:
        """Attach libVLC rendering to a Qt-owned native video surface."""
        if native_window_id <= 0:
            raise ValueError("native_window_id must be positive")
        if sys.platform.startswith("linux"):
            self._player.set_xwindow(native_window_id)
        elif sys.platform == "win32":
            self._player.set_hwnd(native_window_id)
        elif sys.platform == "darwin":
            self._player.set_nsobject(native_window_id)
        else:
            raise RuntimeError(f"Unsupported libVLC video-output platform: {sys.platform}")

    async def _set_media_and_play(
        self,
        playback: ResolvedPlayback,
        *,
        software_fallback: bool = False,
        cause: _CommandCause,
    ) -> None:
        media = self._new_media(playback, software_fallback=software_fallback)
        if self._network_caching_ms:
            media.add_option(f":network-caching={self._network_caching_ms}")
        if self._playback_mode == "software" or (
            software_fallback and self._playback_mode == "auto"
        ):
            media.add_option(":avcodec-hw=none")
        self._current_media = media
        try:
            self._player.set_media(media)
            await self._invoke("play", cause)
        except Exception:
            await self._release_current_media()
            raise

    async def _invalidate_recovery(
        self,
        state: _PlaybackState,
        *,
        intentional: bool = False,
    ) -> None:
        """Invalidate one live session before an intentional player lifecycle action."""
        self._session_token += 1
        self._intentional_action = intentional
        self._publish_state(state, reason="intentional_action", reset_context=True)
        self._recovery_attempts = 0
        self._recovery_started_at = None
        await self._cancel_recovery_tasks()

    async def _cancel_recovery_tasks(self) -> None:
        """Cancel timers without awaiting the task that invoked this helper."""
        current_task = asyncio.current_task()
        tasks: list[asyncio.Task[None]] = []
        for attribute in (
            "_recovery_task",
            "_watchdog_task",
            "_stability_task",
            "_liveness_task",
        ):
            task = getattr(self, attribute)
            if task is not None and task is not current_task:
                task.cancel()
                tasks.append(task)
            setattr(self, attribute, None)
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def _is_current_live_session(self, media_generation: int, session_token: int) -> bool:
        return (
            not self._closed
            and self._current_playback is not None
            and media_generation == self._media_generation
            and session_token == self._session_token
            and not self._intentional_action
        )

    def _is_current_session(self, media_generation: int, session_token: int) -> bool:
        return (
            not self._closed
            and self._current_playback is not None
            and media_generation == self._media_generation
            and session_token == self._session_token
        )

    async def _handle_native_event(
        self,
        event_name: str,
        media_generation: int,
        session_token: int,
    ) -> None:
        """Interpret a current live callback without running libVLC work in its callback thread."""
        async with self._play_lock:
            if event_name == "PLAYING" and self._is_current_session(
                media_generation, session_token
            ):
                self._intentional_action = False
                self._publish_state(_PlaybackState.PLAYING, reason="native_playing")
                self._cancel_task("_watchdog_task")
                self._schedule_stability_window(media_generation, session_token)
                return
            if not self._is_current_live_session(media_generation, session_token):
                return
            if event_name == "BUFFERING":
                self._publish_state(_PlaybackState.BUFFERING, reason="native_buffering")
                self._schedule_watchdog(media_generation, session_token, "BUFFERING_TIMEOUT")
                return
            if event_name == "END":
                if self._is_live_recovery_target():
                    await self._request_recovery("EOF", media_generation, session_token)
                else:
                    self._cancel_task("_watchdog_task")
                    self._publish_state(_PlaybackState.ENDED, reason="NATURAL_END")
            elif event_name == "STOPPED":
                if self._is_live_recovery_target():
                    await self._request_recovery("STOPPED", media_generation, session_token)
                else:
                    self._cancel_task("_watchdog_task")
                    self._publish_state(_PlaybackState.STOPPED, reason="STOPPED")
            elif event_name == "ERROR":
                if self._is_live_recovery_target():
                    await self._request_recovery(
                        "ENCOUNTERED_ERROR", media_generation, session_token
                    )
                else:
                    self._cancel_task("_watchdog_task")
                    self._publish_state(_PlaybackState.FAILED, reason="ENCOUNTERED_ERROR")

    def _schedule_watchdog(
        self,
        media_generation: int,
        session_token: int,
        reason: _RecoveryReason,
    ) -> None:
        """Start one non-blocking timer; BUFFERING itself never restarts playback."""
        self._cancel_task("_watchdog_task")
        self._watchdog_task = asyncio.create_task(
            self._watchdog_after_timeout(media_generation, session_token, reason),
            name=f"iptv-vlc-watchdog-{self._player_id}-{media_generation}",
        )

    async def _watchdog_after_timeout(
        self,
        media_generation: int,
        session_token: int,
        reason: _RecoveryReason,
    ) -> None:
        try:
            await asyncio.sleep(self._live_buffering_timeout_s)
            async with self._play_lock:
                if not self._is_current_live_session(media_generation, session_token):
                    return
                if self._state not in {_PlaybackState.STARTING, _PlaybackState.BUFFERING}:
                    return
                await self._request_recovery(reason, media_generation, session_token)
        except asyncio.CancelledError:
            return

    async def _request_recovery(
        self,
        reason: _RecoveryReason,
        media_generation: int,
        session_token: int,
    ) -> None:
        """Schedule one bounded media rebuild for a current unexpected live-input failure."""
        if not self._is_current_live_session(media_generation, session_token):
            return
        if self._recovery_task is not None and not self._recovery_task.done():
            return
        now = time.perf_counter()
        if self._recovery_started_at is None:
            self._recovery_started_at = now
        elapsed_s = now - self._recovery_started_at
        if (
            self._recovery_attempts >= self._live_recovery_max_attempts
            or elapsed_s >= self._live_recovery_window_s
        ):
            self._publish_state(_PlaybackState.FAILED, reason=reason)
            provider_id, media_type, content_id, transport_type = self._playback_context()
            _LOG.warning(
                "[IPTV] PLAYBACK_RECOVERY_ABANDONED player_id=%d media_generation=%d "
                "reason=%s attempts=%d elapsed_ms=%.3f provider_id=%s "
                "media_type=%s content_id=%s transport_type=%s",
                self._player_id,
                media_generation,
                reason,
                self._recovery_attempts,
                elapsed_s * 1_000,
                provider_id,
                media_type,
                content_id,
                transport_type,
            )
            return
        self._publish_state(_PlaybackState.RECOVERING, reason=reason)
        self._cancel_task("_watchdog_task")
        self._recovery_attempts += 1
        attempt = self._recovery_attempts
        delay_s = self._recovery_delay_s(attempt)
        provider_id, media_type, content_id, transport_type = self._playback_context()
        _LOG.info(
            "[IPTV] PLAYBACK_RECOVERY player_id=%d media_generation=%d reason=%s "
            "attempt=%d delay_ms=%.3f provider_id=%s media_type=%s content_id=%s "
            "transport_type=%s",
            self._player_id,
            media_generation,
            reason,
            attempt,
            delay_s * 1_000,
            provider_id,
            media_type,
            content_id,
            transport_type,
        )
        self._recovery_task = asyncio.create_task(
            self._recover_after_delay(reason, media_generation, session_token, attempt, delay_s),
            name=f"iptv-vlc-recovery-{self._player_id}-{media_generation}-{attempt}",
        )

    async def _recover_after_delay(
        self,
        reason: _RecoveryReason,
        failed_generation: int,
        session_token: int,
        attempt: int,
        delay_s: float,
    ) -> None:
        """Rebuild media through the existing path; a dead libVLC input is never reused."""
        try:
            await asyncio.sleep(delay_s)
            async with self._play_lock:
                if not self._is_current_live_session(failed_generation, session_token):
                    return
                current_playback = self._current_playback
                if current_playback is None:
                    return
                try:
                    self._publish_state(_PlaybackState.STARTING, reason="live_recovery")
                    await self._stop_and_release_media("live_recovery")
                    await self._set_media_and_play(
                        current_playback,
                        software_fallback=False,
                        cause="live_recovery",
                    )
                except Exception as exc:  # noqa: BLE001
                    self._recovery_task = None
                    _LOG.warning(
                        "[IPTV] PLAYBACK_RECOVERY_RESULT player_id=%d media_generation=%d "
                        "reason=%s attempt=%d result=PLAY_FAILURE error_type=%s",
                        self._player_id,
                        failed_generation,
                        reason,
                        attempt,
                        type(exc).__name__,
                    )
                    await self._request_recovery(reason, self._media_generation, session_token)
                    return
                _LOG.info(
                    "[IPTV] PLAYBACK_RECOVERY_RESULT player_id=%d media_generation=%d "
                    "reason=%s attempt=%d result=STARTED",
                    self._player_id,
                    self._media_generation,
                    reason,
                    attempt,
                )
        except asyncio.CancelledError:
            return
        finally:
            if self._recovery_task is asyncio.current_task():
                self._recovery_task = None

    def _schedule_stability_window(self, media_generation: int, session_token: int) -> None:
        """Reset the recovery budget only after sustained native PLAYING state."""
        self._cancel_task("_stability_task")
        self._stability_task = asyncio.create_task(
            self._confirm_stable_playback(media_generation, session_token),
            name=f"iptv-vlc-stability-{self._player_id}-{media_generation}",
        )

    async def _confirm_stable_playback(self, media_generation: int, session_token: int) -> None:
        try:
            await asyncio.sleep(self._live_recovery_stability_s)
            async with self._play_lock:
                if not self._is_current_live_session(media_generation, session_token):
                    return
                if self._state is not _PlaybackState.PLAYING:
                    return
                self._recovery_attempts = 0
                self._recovery_started_at = None
                _LOG.info(
                    "[IPTV] PLAYBACK_RECOVERY_RESULT player_id=%d media_generation=%d "
                    "result=STABLE",
                    self._player_id,
                    media_generation,
                )
        except asyncio.CancelledError:
            return

    def _cancel_task(self, attribute: str) -> None:
        task = getattr(self, attribute)
        current_task = asyncio.current_task()
        if task is not None and task is not current_task and not task.done():
            task.cancel()
        setattr(self, attribute, None)

    def _is_live_resource(self, playback: ResolvedPlayback | None = None) -> bool:
        active_playback = playback or self._current_playback
        resource = active_playback.resource if active_playback is not None else None
        return resource is not None and resource.content_type is ContentType.LIVE

    def _is_live_recovery_target(self) -> bool:
        """Preserve legacy URL-only live recovery while respecting typed VOD identity."""
        playback = self._current_playback
        if playback is None or playback.resource is None:
            return True
        return playback.resource.content_type is ContentType.LIVE

    def _start_liveness_task(self, media_generation: int, session_token: int) -> None:
        self._cancel_task("_liveness_task")
        self._last_media_position_ms = -1
        self._last_position_advance_at = time.perf_counter()
        self._liveness_task = asyncio.create_task(
            self._monitor_live_liveness(media_generation, session_token),
            name=f"iptv-vlc-liveness-{self._player_id}-{media_generation}",
        )

    async def _monitor_live_liveness(self, media_generation: int, session_token: int) -> None:
        """Detect a current live stream that remains PLAYING without media progress."""
        try:
            while True:
                await asyncio.sleep(self._live_liveness_poll_s)
                async with self._play_lock:
                    if not self._is_current_live_session(media_generation, session_token):
                        return
                    if self._state is not _PlaybackState.PLAYING:
                        return
                    try:
                        position_ms = await asyncio.to_thread(self._player.get_time)
                    except Exception as exc:  # noqa: BLE001
                        _LOG.debug(
                            "[IPTV] PLAYBACK liveness sample unavailable error_type=%s",
                            type(exc).__name__,
                        )
                        continue
                    if not isinstance(position_ms, int) or position_ms < 0:
                        continue
                    now = time.perf_counter()
                    if position_ms > self._last_media_position_ms:
                        self._last_media_position_ms = position_ms
                        self._last_position_advance_at = now
                        provider_id, media_type, content_id, transport_type = (
                            self._playback_context()
                        )
                        _LOG.info(
                            "[IPTV] PLAYBACK_DIAGNOSTIC MEDIA_PROGRESS "
                            "player_id=%d media_generation=%d position_ms=%d "
                            "provider_id=%s media_type=%s content_id=%s transport_type=%s",
                            self._player_id,
                            media_generation,
                            position_ms,
                            provider_id,
                            media_type,
                            content_id,
                            transport_type,
                        )
                        continue
                    last_advance = self._last_position_advance_at
                    if (
                        last_advance is not None
                        and now - last_advance >= self._live_stall_timeout_s
                    ):
                        await self._request_recovery("STALLED", media_generation, session_token)
                        return
        except asyncio.CancelledError:
            return

    def _recovery_delay_s(self, attempt: int) -> float:
        multiplier = float(2 ** max(0, attempt - 1))
        return float(
            min(
                self._live_recovery_initial_delay_s * multiplier,
                self._live_recovery_max_delay_s,
            )
        )

    @staticmethod
    def _recording_option(destination: Path) -> str:
        value = str(destination)
        if any(character in value for character in ("\x00", "\n", "\r")):
            raise ValueError("Recording destination contains unsupported characters")
        escaped = value.replace("\\", "\\\\").replace("'", "\\'")
        return f":sout=#duplicate{{dst=display,dst=std{{access=file,mux=ts,dst='{escaped}'}}}}"

    async def _stop_and_release_media(self, cause: _CommandCause) -> None:
        """Stop the native player and release the media it currently owns."""
        try:
            await self._invoke("stop", cause)
        finally:
            await self._release_current_media()

    async def _release_current_media(self) -> None:
        """Release and forget the current media object, even after stop failure."""
        media = self._current_media
        self._current_media = None
        if media is not None:
            await self._release(media, "media")

    def _unsubscribe_events(self) -> None:
        """Detach all native event subscriptions when the player is closed."""
        manager = self._event_manager
        detach = getattr(manager, "event_detach", None)
        if callable(detach):
            for event_type, _callback in self._event_subscriptions:
                try:
                    detach(event_type)
                except Exception:  # noqa: BLE001
                    _LOG.debug("[IPTV] PLAYBACK event detachment unavailable", exc_info=True)
        self._event_subscriptions.clear()
        self._event_manager = None
        self._event_subscription_count = 0

    async def _release(self, target: object, target_name: str) -> None:
        """Release a libVLC object when its binding exposes the expected method."""
        release = getattr(target, "release", None)
        if not callable(release):
            return
        self._log_command("release", "shutdown", target=target_name)
        try:
            await asyncio.to_thread(release)
        except Exception:  # noqa: BLE001
            _LOG.debug("[IPTV] PLAYBACK release during shutdown failed", exc_info=True)

    async def _invoke(self, operation: _CommandAction, cause: _CommandCause) -> None:
        self._log_command(operation, cause)
        result = await asyncio.to_thread(getattr(self._player, operation))
        if isinstance(result, int) and result < 0:
            raise RuntimeError(f"libVLC {operation} failed")

    def _new_media(self, playback: ResolvedPlayback, *, software_fallback: bool) -> _VlcMedia:
        """Create media while recording only aggregate playback configuration metadata."""
        media = self._instance.media_new(playback.url.value)
        with self._diagnostic_lock:
            self._media_generation += 1
            self._media_created_at = time.perf_counter()
            media_generation = self._media_generation
        self._publish_state(_PlaybackState.STARTING, reason="media_created", reset_context=True)
        for header in playback.transport.headers:
            media.add_option(f":http-header={header.name}: {header.value}")
        if playback.transport.user_agent is not None:
            media.add_option(f":http-user-agent={playback.transport.user_agent}")
        if playback.transport.referrer is not None:
            media.add_option(f":http-referrer={playback.transport.referrer}")
        hardware_option = (
            "disabled"
            if self._playback_mode == "software"
            or (software_fallback and self._playback_mode == "auto")
            else "enabled"
        )
        provider_id, media_type, content_id, transport_type = self._playback_context(playback)
        _LOG.info(
            "[IPTV] PLAYBACK_DIAGNOSTIC MEDIA player_id=%d media_generation=%d "
            "playback_mode=%s network_cache_ms=%d hardware_option=%s "
            "provider_id=%s media_type=%s content_id=%s transport_type=%s",
            self._player_id,
            media_generation,
            self._playback_mode,
            self._network_caching_ms,
            hardware_option,
            provider_id,
            media_type,
            content_id,
            transport_type,
        )
        return media

    def _publish_state(
        self,
        state: _PlaybackState,
        *,
        reason: str | None = None,
        reset_context: bool = False,
    ) -> None:
        """Synchronize private recovery state with the public typed state machine."""
        previous_state = self._state
        self._state = state
        public_state = {
            _PlaybackState.IDLE: PlaybackState.IDLE,
            _PlaybackState.STARTING: PlaybackState.LOADING,
            _PlaybackState.PLAYING: PlaybackState.PLAYING,
            _PlaybackState.BUFFERING: PlaybackState.BUFFERING,
            _PlaybackState.RECOVERING: PlaybackState.RECOVERING,
            _PlaybackState.STOPPING: PlaybackState.STOPPING,
            _PlaybackState.STOPPED: PlaybackState.STOPPED,
            _PlaybackState.FAILED: PlaybackState.ERROR,
            _PlaybackState.ENDED: PlaybackState.ENDED,
        }[state]
        if reset_context:
            self._state_machine.reset_context(
                media_generation=self._media_generation,
                session_token=self._session_token,
                state=public_state,
                reason=reason,
            )
        else:
            self._state_machine.transition(
                public_state,
                media_generation=self._media_generation,
                session_token=self._session_token,
                reason=reason,
            )
        provider_id, media_type, content_id, transport_type = self._playback_context()
        error_classification = (
            reason
            if reason in {"EOF", "STOPPED", "BUFFERING_TIMEOUT", "ENCOUNTERED_ERROR", "STALLED"}
            else "<none>"
        )
        if state is _PlaybackState.PLAYING and self._is_live_resource():
            self._start_liveness_task(self._media_generation, self._session_token)
        elif state is not _PlaybackState.PLAYING:
            self._cancel_task("_liveness_task")
            self._last_media_position_ms = -1
            self._last_position_advance_at = None
        _LOG.info(
            "[IPTV] PLAYBACK_DIAGNOSTIC STATE player_id=%d media_generation=%d "
            "from_state=%s to_state=%s reason=%s error_classification=%s "
            "provider_id=%s media_type=%s content_id=%s transport_type=%s",
            self._player_id,
            self._media_generation,
            previous_state,
            state,
            reason or "<none>",
            error_classification,
            provider_id,
            media_type,
            content_id,
            transport_type,
        )

    def _log_command(
        self,
        action: _CommandAction,
        cause: _CommandCause,
        *,
        target: str = "player",
    ) -> None:
        with self._diagnostic_lock:
            self._last_command_cause = cause
            media_generation = self._media_generation
        _LOG.info(
            "[IPTV] PLAYBACK_DIAGNOSTIC COMMAND player_id=%d media_generation=%d "
            "action=%s cause=%s target=%s",
            self._player_id,
            media_generation,
            action,
            cause,
            target,
        )

    def _log_event(self, event_name: str) -> tuple[int, int]:
        with self._diagnostic_lock:
            self._event_sequence += 1
            event_sequence = self._event_sequence
            media_generation = self._media_generation
            session_token = self._session_token
            media_created_at = self._media_created_at
            last_command_cause = self._diagnostic_cause_locked()
        elapsed_ms = (
            "<none>"
            if media_created_at is None
            else f"{(time.perf_counter() - media_created_at) * 1_000:.3f}"
        )
        callback_thread = current_thread()
        provider_id, media_type, content_id, transport_type = self._playback_context()
        _LOG.info(
            "[IPTV] PLAYBACK_DIAGNOSTIC EVENT player_id=%d media_generation=%d "
            "event_sequence=%d event=%s media_delta_ms=%s thread_id=%d thread_name=%s "
            "closed=%s last_command_cause=%s provider_id=%s media_type=%s "
            "content_id=%s transport_type=%s",
            self._player_id,
            media_generation,
            event_sequence,
            event_name,
            elapsed_ms,
            callback_thread.ident or 0,
            callback_thread.name,
            self._closed,
            last_command_cause,
            provider_id,
            media_type,
            content_id,
            transport_type,
        )
        _LOG.info("[IPTV] PLAYBACK %s", event_name)
        return media_generation, session_token

    def _playback_context(
        self, playback: ResolvedPlayback | None = None
    ) -> tuple[str, str, str, str]:
        """Return bounded non-secret context labels for playback telemetry."""
        active_playback = playback or self._current_playback
        resource = active_playback.resource if active_playback is not None else None
        if resource is None:
            provider_id = media_type = content_id = "<unknown>"
        else:
            provider_id = safe_label(resource.provider_id, limit=64)
            media_type = safe_label(resource.content_type.value, limit=32)
            content_id = safe_label(resource.canonical_content_id, limit=64)
        if active_playback is None:
            return provider_id, media_type, content_id, "<unknown>"
        transport = active_playback.transport.protocol_hint
        if transport is not None:
            transport_type = safe_label(transport.value, limit=32)
        else:
            scheme = urlsplit(active_playback.url.value).scheme.casefold()
            transport_type = safe_label(scheme or "<unknown>", limit=32)
        return provider_id, media_type, content_id, transport_type

    def _diagnostic_cause(self) -> str:
        with self._diagnostic_lock:
            return self._diagnostic_cause_locked()

    def _diagnostic_cause_locked(self) -> str:
        return self._last_command_cause or "<none>"
