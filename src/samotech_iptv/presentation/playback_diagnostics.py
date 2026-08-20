"""Safe, copyable user-facing playback diagnostic reports."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from samotech_iptv.core.safe_logging import safe_label

if TYPE_CHECKING:
    from samotech_iptv.application.dtos.player import PlayerDiagnostics

__all__ = ["PlaybackDiagnosticContext", "format_playback_diagnostic_report"]


@dataclass(frozen=True)
class PlaybackDiagnosticContext:
    """Presentation-owned context that contains no source URL or provider credential."""

    application_version: str
    platform: str
    provider_type: str | None = None
    content_type: str | None = None


def _display(value: object | None) -> str:
    if value is None:
        return "NOT_AVAILABLE"
    if isinstance(value, bool):
        return "RECEIVED" if value else "NOT_RECEIVED"
    rendered = safe_label(value, limit=120)
    return rendered if rendered and rendered != "<none>" else "NOT_AVAILABLE"


def _milliseconds(value: float | int | None) -> str:
    return "NOT_AVAILABLE" if value is None else f"{float(value):.0f} ms"


def format_playback_diagnostic_report(
    context: PlaybackDiagnosticContext,
    diagnostics: PlayerDiagnostics,
) -> str:
    """Render a deterministic report with only allow-listed, redacted values."""
    return "\n".join(
        (
            "SamoTech IPTV Player — Safe Playback Diagnostic Report",
            f"Version: {_display(context.application_version)}",
            f"Platform: {_display(context.platform)}",
            "Backend: libVLC",
            f"VLC version: {_display(diagnostics.vlc_version)}",
            f"Provider: {_display(context.provider_type)}",
            f"Content: {_display(context.content_type)}",
            f"Playback state: {_display(diagnostics.playback_state.value)}",
            f"Media protocol: {_display(diagnostics.media_protocol)}",
            f"Container: {_display(diagnostics.container)}",
            f"Video: {_display(diagnostics.video_codec)}",
            f"Audio: {_display(diagnostics.audio_codec)}",
            f"Resolution: {_display(diagnostics.resolution)}",
            f"FPS: {_display(diagnostics.fps)}",
            f"First frame: {_display(diagnostics.first_frame_received)}",
            f"Playback position: {_milliseconds(diagnostics.position_ms)}",
            f"Duration: {_milliseconds(diagnostics.duration_ms)}",
            f"Startup latency: {_milliseconds(diagnostics.startup_latency_ms)}",
            f"Buffering duration: {_milliseconds(diagnostics.buffering_duration_ms)}",
            f"Recovery attempts: {max(0, diagnostics.recovery_attempts)}",
            f"Last error: {_display(diagnostics.terminal_failure_reason)}",
            (
                "Privacy: credentials, private URLs, tokens, cookies, headers, "
                "and MAC addresses are excluded."
            ),
        )
    )
