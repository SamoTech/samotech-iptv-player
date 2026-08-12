from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from samotech_iptv.application.use_cases.start_recording import StartRecording
from samotech_iptv.application.use_cases.stop_recording import StopRecording

if TYPE_CHECKING:
    from pathlib import Path


class FakePlayer:
    """Player-port double retaining only recording control requests."""

    def __init__(self) -> None:
        self.destinations: list[Path] = []
        self.stop_calls = 0

    async def start_recording(self, destination: Path) -> None:
        self.destinations.append(destination)

    async def stop_recording(self) -> None:
        self.stop_calls += 1


@pytest.mark.asyncio
async def test_start_recording_uses_a_safe_utc_timestamped_transport_stream_path(
    tmp_path: Path,
) -> None:
    player = FakePlayer()
    start_recording = StartRecording(
        player,  # type: ignore[arg-type]
        tmp_path,
        clock=lambda: datetime(2026, 8, 12, 10, 30, 45, tzinfo=UTC),
    )

    await start_recording.execute()

    assert player.destinations == [tmp_path / "recording-20260812T103045Z.ts"]


@pytest.mark.asyncio
async def test_stop_recording_delegates_without_receiving_stream_or_provider_data() -> None:
    player = FakePlayer()

    await StopRecording(player).execute()  # type: ignore[arg-type]

    assert player.stop_calls == 1
