"""Regression coverage for the public real-world playback feedback boundary."""

from __future__ import annotations

from pathlib import Path


def test_bug_template_requests_playback_evidence_and_prohibits_sensitive_source_data() -> None:
    template = Path(".github/ISSUE_TEMPLATE/bug_report.md").read_text(encoding="utf-8")
    normalized = template.casefold()

    for required in (
        "provider type",
        "content type",
        "catalogue load",
        "first video frame",
        "audio work",
        "buffering",
        "channel or episode switching",
        "safe diagnostic report",
    ):
        assert required in normalized
    for forbidden in (
        "passwords",
        "access tokens",
        "mac addresses",
        "private playlist urls",
        "cookies",
        "authorization headers",
    ):
        assert forbidden in normalized
