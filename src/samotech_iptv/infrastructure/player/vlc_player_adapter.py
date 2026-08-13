"""libVLC-backed implementation of playback and active-stream recording."""

from __future__ import annotations

import asyncio
import sys
import time
from typing import TYPE_CHECKING, Literal, Protocol

import vlc  # type: ignore[import-untyped]

from samotech_iptv.application.ports.player_port import PlayerPort
from samotech_iptv.core.diagnostics import safe_label
from samotech_iptv.core.logging import get_logger

if TYPE_CHECKING:
    from pathlib import Path

    from samotech_iptv.domain.value_objects.url import URL

__all__ = ["VlcPlayerAdapter"]

_LOG = get_logger(__name__)
PlaybackMode = Literal["auto", "hardware", "software"]


class _VlcMedia(Protocol):
    def add_option(self, option: str) -> None: ...


class _VlcInstance(Protocol):
    def media_player_new(self) -> _VlcPlayer: ...

    def media_new(self, url: str) -> _VlcMedia: ...


class _VlcPlayer(Protocol):
    def is_playing(self) -> int: ...

    def set_media(self, media: _VlcMedia) -> None: ...

    def play(self) -> int: ...

    def stop(self) -> None: ...

    def pause(self) -> None: ...

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
    ) -> None:
        if playback_mode not in {"auto", "hardware", "software"}:
            raise ValueError("playback_mode must be auto, hardware, or software")
        if network_caching_ms < 0:
            raise ValueError("network_caching_ms must not be negative")
        if play_retry_count < 0:
            raise ValueError("play_retry_count must not be negative")
        self._instance = instance or vlc.Instance()
        self._player = player or self._instance.media_player_new()
        self._current_url: URL | None = None
        self._recording_destination: Path | None = None
        self._playback_mode = playback_mode
        self._network_caching_ms = network_caching_ms
        self._play_retry_count = play_retry_count
        self._play_lock = asyncio.Lock()
        self._closed = False
        self._subscribe_events()

    def _subscribe_events(self) -> None:
        """Attach best-effort libVLC lifecycle events when the backend exposes them."""
        event_manager_factory = getattr(self._player, "event_manager", None)
        event_types = getattr(vlc, "EventType", None)
        if not callable(event_manager_factory) or event_types is None:
            return
        try:
            event_manager = event_manager_factory()
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
                    event_manager.event_attach(
                        event_type,
                        lambda _event, event_label=label: _LOG.info(
                            "[IPTV] PLAYBACK %s", event_label
                        ),
                    )
        except Exception:  # noqa: BLE001
            _LOG.debug("[IPTV] PLAYBACK event subscription unavailable", exc_info=True)

    @property
    def is_playing(self) -> bool:
        """Return whether libVLC reports active playback."""
        return bool(self._player.is_playing())

    @property
    def is_recording(self) -> bool:
        """Return whether the active libVLC media contains a recording output."""
        return self._recording_destination is not None

    async def play(self, url: URL) -> None:
        """Stop prior media, then start one stream with bounded retry and diagnostics."""
        started = time.perf_counter()
        async with self._play_lock:
            if self._current_url is not None or self.is_playing:
                _LOG.info(
                    "[IPTV] PLAYBACK STOPPED reason=channel_switch previous=%s",
                    safe_label(self._current_url.value if self._current_url else "<unknown>"),
                )
                await self._invoke("stop")
            _LOG.info("[IPTV] PLAYBACK START host=%s", self._host(url.value))
            last_error: Exception | None = None
            for attempt in range(self._play_retry_count + 1):
                try:
                    await self._set_media_and_play(url, software_fallback=attempt > 0)
                    self._current_url = url
                    self._recording_destination = None
                    _LOG.info(
                        "[IPTV] PLAYBACK PLAYING elapsed=%.3fs retry=%d",
                        time.perf_counter() - started,
                        attempt,
                    )
                    return
                except Exception as exc:  # noqa: BLE001
                    last_error = exc
                    _LOG.warning(
                        "[IPTV] PLAYBACK ERROR error_type=%s retry=%d",
                        type(exc).__name__,
                        attempt,
                    )
                    await self._invoke("stop")
                    if attempt < self._play_retry_count:
                        _LOG.info("[IPTV] PLAYBACK RETRY retry=%d mode=software", attempt + 1)
            self._current_url = None
            if last_error is None:
                raise RuntimeError("Unable to start playback")
            raise RuntimeError("Unable to start playback") from last_error

    async def stop(self) -> None:
        """Stop libVLC playback and terminate any active recording output."""
        async with self._play_lock:
            await self._invoke("stop")
            self._current_url = None
            self._recording_destination = None
            _LOG.info("[IPTV] PLAYBACK STOPPED")

    async def close(self) -> None:
        """Stop playback and release the owned libVLC player and instance exactly once."""
        async with self._play_lock:
            if self._closed:
                return
            self._closed = True
            self._current_url = None
            self._recording_destination = None
            try:
                await self._invoke("stop")
            except Exception:  # noqa: BLE001
                _LOG.debug("[IPTV] PLAYBACK stop during shutdown failed", exc_info=True)
            try:
                await self._release(self._player)
            finally:
                await self._release(self._instance)
            _LOG.info("[IPTV] PLAYBACK RELEASED")

    async def pause(self) -> None:
        """Pause libVLC playback while preserving an active recording configuration."""
        async with self._play_lock:
            await self._invoke("pause")
            _LOG.info("[IPTV] PLAYBACK BUFFERING state=paused")

    async def resume(self) -> None:
        """Resume libVLC playback while preserving an active recording configuration."""
        async with self._play_lock:
            await self._invoke("play")
            _LOG.info("[IPTV] PLAYBACK PLAYING state=resumed")

    async def start_recording(self, destination: Path) -> None:
        """Restart active media with one libVLC display/file duplicate stream output."""
        if self._current_url is None or not self.is_playing:
            raise RuntimeError("Cannot record without active playback")
        if self._recording_destination is not None:
            raise RuntimeError("Recording is already active")
        output_path = destination.expanduser().resolve()
        if output_path.suffix.lower() != ".ts":
            raise ValueError("Recording destination must use the .ts extension")
        if output_path.exists():
            raise FileExistsError("Recording destination already exists")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        media = self._instance.media_new(self._current_url.value)
        media.add_option(self._recording_option(output_path))
        self._player.set_media(media)
        await self._invoke("play")
        self._recording_destination = output_path

    async def stop_recording(self) -> None:
        """Restart active media without stream output while continuing normal playback."""
        if self._recording_destination is None or self._current_url is None:
            raise RuntimeError("No active recording")
        await self._set_media_and_play(self._current_url)
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

    async def _set_media_and_play(self, url: URL, *, software_fallback: bool = False) -> None:
        media = self._instance.media_new(url.value)
        if self._network_caching_ms:
            media.add_option(f":network-caching={self._network_caching_ms}")
        if self._playback_mode == "software" or (
            software_fallback and self._playback_mode == "auto"
        ):
            media.add_option(":avcodec-hw=none")
        self._player.set_media(media)
        await self._invoke("play")

    @staticmethod
    def _host(value: str) -> str:
        from urllib.parse import urlsplit

        return urlsplit(value).hostname or "<unknown>"

    @staticmethod
    def _recording_option(destination: Path) -> str:
        value = str(destination)
        if any(character in value for character in ("\x00", "\n", "\r")):
            raise ValueError("Recording destination contains unsupported characters")
        escaped = value.replace("\\", "\\\\").replace("'", "\\'")
        return f":sout=#duplicate{{dst=display,dst=std{{access=file,mux=ts,dst='{escaped}'}}}}"

    @staticmethod
    async def _release(target: object) -> None:
        """Release a libVLC object when its binding exposes the expected method."""
        release = getattr(target, "release", None)
        if not callable(release):
            return
        try:
            await asyncio.to_thread(release)
        except Exception:  # noqa: BLE001
            _LOG.debug("[IPTV] PLAYBACK release during shutdown failed", exc_info=True)

    async def _invoke(self, operation: str) -> None:
        result = await asyncio.to_thread(getattr(self._player, operation))
        if isinstance(result, int) and result < 0:
            raise RuntimeError(f"libVLC {operation} failed")
