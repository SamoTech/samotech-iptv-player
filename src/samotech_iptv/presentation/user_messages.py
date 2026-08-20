"""Bounded user-facing messages derived from untrusted playback failure text."""

from __future__ import annotations

from samotech_iptv.application.dtos.playback import PlaybackOutcome

__all__ = ["playback_failure_message"]


def playback_failure_message(outcome: PlaybackOutcome | object, detail: object = None) -> str:
    """Return actionable copy without displaying untrusted provider or transport detail."""
    if outcome is PlaybackOutcome.UNSUPPORTED:
        return "Playback is unavailable for this selected media."

    text = str(detail or "").casefold()
    if any(marker in text for marker in ("401", "403", "unauthor", "forbidden", "denied")):
        return (
            "Provider rejected the request. Check the server address, account status, "
            "or provider access restrictions."
        )
    if any(marker in text for marker in ("timeout", "timed out", "connection", "network")):
        return "Provider did not respond in time. Check your network connection and try again."
    if any(marker in text for marker in ("404", "not found", "server")):
        return (
            "Provider could not supply this stream. Check the selected channel and provider "
            "service."
        )
    return (
        "Playback could not start. Retry, check the provider connection, or open Info for "
        "safe diagnostics."
    )
