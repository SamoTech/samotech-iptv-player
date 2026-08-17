"""Application contract for the sole libVLC-backed media player."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from samotech_iptv.application.dtos.playback import ResolvedPlayback
    from samotech_iptv.application.dtos.player import AudioTrack, SubtitleTrack

__all__ = ["PlayerPort"]


class PlayerPort(ABC):
    """Contract for the libVLC media-player backend."""

    @abstractmethod
    async def play(self, playback: ResolvedPlayback) -> None: ...

    @abstractmethod
    async def stop(self) -> None: ...

    @abstractmethod
    async def restart(self) -> None:
        """Restart the current resolved playback when one exists."""
        ...

    @abstractmethod
    async def get_position_ms(self) -> int | None:
        """Return current media position in milliseconds when available."""
        ...

    @abstractmethod
    async def get_duration_ms(self) -> int | None:
        """Return current media duration in milliseconds when available."""
        ...

    @abstractmethod
    async def seek_ms(self, position_ms: int) -> None:
        """Seek to an absolute media position in milliseconds."""
        ...

    @abstractmethod
    async def seek_fraction(self, position: float) -> None:
        """Seek to an absolute media position between zero and one."""
        ...

    @abstractmethod
    async def get_volume(self) -> int | None:
        """Return software volume percentage when available."""
        ...

    @abstractmethod
    async def set_volume(self, volume: int) -> None:
        """Set software volume percentage between zero and one hundred."""
        ...

    @abstractmethod
    async def is_muted(self) -> bool | None:
        """Return mute state when available."""
        ...

    @abstractmethod
    async def set_muted(self, muted: bool) -> None:
        """Set mute state using the native player toggle when necessary."""
        ...

    @abstractmethod
    async def get_audio_tracks(self) -> tuple[AudioTrack, ...]:
        """Enumerate native audio tracks without fabricating metadata."""
        ...

    @abstractmethod
    async def select_audio_track(self, track_id: int) -> None:
        """Select one track returned by get_audio_tracks."""
        ...

    @abstractmethod
    async def get_subtitle_tracks(self) -> tuple[SubtitleTrack, ...]:
        """Enumerate native subtitle tracks without fabricating metadata."""
        ...

    @abstractmethod
    async def select_subtitle_track(self, track_id: int | None) -> None:
        """Select a native subtitle track, or None to disable subtitles."""
        ...

    @property
    def media_generation(self) -> int | None:
        """Return the current media generation when the backend exposes one."""
        return None

    async def attach_local_subtitle(
        self,
        path: Path,
        *,
        expected_generation: int | None = None,
    ) -> None:
        """Attach one local subtitle to the current media when the backend supports it."""
        del path, expected_generation
        raise NotImplementedError("Local subtitle attachment is unavailable")

    async def clear_local_subtitles(self) -> None:
        """Remove locally attached subtitle slaves when the backend supports it."""
        raise NotImplementedError("Local subtitle removal is unavailable")

    async def get_subtitle_delay_ms(self) -> int | None:
        """Return native subtitle delay in milliseconds when available."""
        return None

    async def set_subtitle_delay_ms(self, delay_ms: int) -> None:
        """Set native subtitle delay in milliseconds when available."""
        del delay_ms
        raise NotImplementedError("Subtitle delay is unavailable")

    @abstractmethod
    async def get_aspect_ratio(self) -> str | None:
        """Return the native aspect-ratio override when available."""
        ...

    @abstractmethod
    async def set_aspect_ratio(self, aspect_ratio: str | None) -> None:
        """Set or clear the native aspect-ratio override."""
        ...

    @abstractmethod
    async def pause(self) -> None: ...

    @abstractmethod
    async def resume(self) -> None: ...

    @abstractmethod
    async def start_recording(self, destination: Path) -> None:
        """Start recording the active stream to a local destination."""
        ...

    @abstractmethod
    async def stop_recording(self) -> None:
        """Stop recording while continuing active playback."""
        ...

    @abstractmethod
    def attach_video_output(self, native_window_id: int) -> None:
        """Attach video rendering to a presentation-owned native window."""
        ...

    @property
    @abstractmethod
    def is_playing(self) -> bool: ...

    @property
    @abstractmethod
    def is_recording(self) -> bool:
        """Return whether the active stream is currently being recorded."""
        ...
