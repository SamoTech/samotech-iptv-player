"""Public-testing documentation must preserve honest scope and diagnostic privacy guidance."""

from __future__ import annotations

from pathlib import Path


def test_public_testing_guide_covers_setup_diagnostics_and_privacy() -> None:
    guide = Path("docs/testing/PUBLIC_TESTING_GUIDE.md").read_text(encoding="utf-8").casefold()

    for required in (
        "m3u / m3u8",
        "xtream",
        "mag / stalker",
        "fullscreen",
        "playback diagnostics",
        "copy diagnostic report",
        "never post passwords",
        "not_available",
        "no screenshots are included",
    ):
        assert required in guide
    assert "universal" in guide


def test_release_notes_explicitly_position_the_release_as_public_testing() -> None:
    notes = Path("packaging/release_notes_template.md").read_text(encoding="utf-8").casefold()

    for required in (
        "this is a public testing release",
        "commercial iptv compatibility is not universally certified",
        "use your own legitimate iptv source",
        "real-world provider compatibility is still being validated",
        "no credentials are collected by samotech",
        "samotech-debug.bat",
    ):
        assert required in notes
