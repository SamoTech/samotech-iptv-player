"""Tests for generic application-level playback controls."""

from __future__ import annotations

import pytest

from samotech_iptv.application.use_cases.playback_controls import (
    PausePlayback,
    ResumePlayback,
    StopPlayback,
)


class FakePlayer:
    """Player-port double retaining generic playback control requests."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    async def pause(self) -> None:
        self.calls.append("pause")

    async def resume(self) -> None:
        self.calls.append("resume")

    async def stop(self) -> None:
        self.calls.append("stop")


@pytest.mark.asyncio
async def test_playback_controls_delegate_without_provider_or_stream_data() -> None:
    """Every generic control forwards to the sole player boundary only."""
    player = FakePlayer()

    await PausePlayback(player).execute()  # type: ignore[arg-type]
    await ResumePlayback(player).execute()  # type: ignore[arg-type]
    await StopPlayback(player).execute()  # type: ignore[arg-type]

    assert player.calls == ["pause", "resume", "stop"]
