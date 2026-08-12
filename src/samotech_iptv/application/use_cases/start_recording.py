"""Start a local recording through the sole player backend."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from samotech_iptv.application.ports.player_port import PlayerPort

__all__ = ["StartRecording"]


class StartRecording:
    """Create a deterministic local destination and start recording active playback."""

    def __init__(
        self,
        player: PlayerPort,
        recording_directory: Path,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._player = player
        self._recording_directory = recording_directory
        self._clock = clock or (lambda: datetime.now(UTC))

    async def execute(self) -> None:
        """Record the active stream to a timestamped MPEG transport-stream file."""
        timestamp = self._clock().astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
        destination = self._recording_directory / f"recording-{timestamp}.ts"
        await self._player.start_recording(destination)
