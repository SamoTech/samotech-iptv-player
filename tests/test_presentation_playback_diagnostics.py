"""Regression coverage for the safe copyable playback diagnostic report."""

from __future__ import annotations

from samotech_iptv.application.dtos.player import PlaybackState, PlayerDiagnostics
from samotech_iptv.presentation.playback_diagnostics import (
    PlaybackDiagnosticContext,
    format_playback_diagnostic_report,
)


def test_playback_diagnostic_report_includes_only_sanitized_allowlisted_values() -> None:
    report = format_playback_diagnostic_report(
        PlaybackDiagnosticContext(
            application_version="0.1.6",
            platform="Windows 11",
            provider_type="Xtream",
            content_type="live",
        ),
        PlayerDiagnostics(
            playback_state=PlaybackState.BUFFERING,
            media_protocol="https",
            position_ms=12_000,
            duration_ms=0,
            recovery_attempts=2,
            terminal_failure_reason="NETWORK_TIMEOUT token=private-value",
        ),
    )

    assert "Version: 0.1.6" in report
    assert "Provider: Xtream" in report
    assert "Playback state: buffering" in report
    assert "Media protocol: https" in report
    assert "Container: NOT_AVAILABLE" in report
    assert "First frame: NOT_AVAILABLE" in report
    assert "Last error: NETWORK_TIMEOUT token=<REDACTED>" in report
    assert "private-value" not in report
    assert "password" not in report.casefold()


def test_playback_diagnostic_report_does_not_fabricate_unmeasured_media_fields() -> None:
    report = format_playback_diagnostic_report(
        PlaybackDiagnosticContext(application_version="0.1.6", platform="Windows 11"),
        PlayerDiagnostics(),
    )

    assert "Video: NOT_AVAILABLE" in report
    assert "Audio: NOT_AVAILABLE" in report
    assert "Resolution: NOT_AVAILABLE" in report
    assert "FPS: NOT_AVAILABLE" in report
    assert "VLC version: NOT_AVAILABLE" in report
