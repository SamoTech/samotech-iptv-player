"""Regression coverage for safe playback failure copy."""

from __future__ import annotations

from samotech_iptv.application.dtos.playback import PlaybackOutcome
from samotech_iptv.presentation.user_messages import playback_failure_message


def test_provider_rejection_message_is_actionable_and_redacts_private_detail() -> None:
    message = playback_failure_message(
        PlaybackOutcome.FAILED,
        "HTTP 403 https://subscriber:private-password@example.invalid/live?token=secret",
    )

    assert message == (
        "Provider rejected the request. Check the server address, account status, "
        "or provider access restrictions."
    )
    assert "example.invalid" not in message
    assert "private-password" not in message
    assert "secret" not in message


def test_generic_and_unsupported_messages_do_not_echo_failure_detail() -> None:
    private_detail = "cookie=session-secret https://example.invalid/private"

    assert "session-secret" not in playback_failure_message(PlaybackOutcome.FAILED, private_detail)
    assert playback_failure_message(PlaybackOutcome.UNSUPPORTED, private_detail) == (
        "Playback is unavailable for this selected media."
    )
