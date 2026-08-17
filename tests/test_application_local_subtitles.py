from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from samotech_iptv.application.local_subtitles import (
    MAX_LOCAL_SUBTITLE_BYTES,
    LocalSubtitleError,
    inspect_local_subtitle,
)


@pytest.mark.parametrize(
    ("name", "content"),
    [
        (
            "english.srt",
            "1\n00:00:01,000 --> 00:00:02,000\nHello world\n",
        ),
        (
            "arabic.ass",
            "[Script Info]\n[Events]\nDialogue: 0,0:00:01.00,0:00:02.00,Default,مرحبا بالعالم\n",
        ),
        (
            "mixed.ssa",
            "[Script Info]\n[Events]\nDialogue: 0,0:00:01.00,0:00:02.00,Default,Hello مرحبا\n",
        ),
        ("caption.vtt", "WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nHello world\n"),
    ],
)
def test_supported_local_subtitle_formats_are_validated(
    tmp_path: Path, name: str, content: str
) -> None:
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")

    result = inspect_local_subtitle(path)

    assert result.path == path.resolve()
    assert result.suffix == path.suffix
    assert result.display_name == name
    assert result.size_bytes == path.stat().st_size


@pytest.mark.parametrize(
    ("name", "content"),
    [
        ("empty.srt", ""),
        ("malformed.srt", "1\nnot a timestamp\ntext\n"),
        ("malformed.vtt", "not a webvtt file"),
        ("malformed.ass", "[Script Info]\nno events\n"),
    ],
)
def test_malformed_or_empty_subtitles_fail_safely(tmp_path: Path, name: str, content: str) -> None:
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")

    with pytest.raises(LocalSubtitleError):
        inspect_local_subtitle(path)


def test_missing_and_unsupported_subtitle_files_fail_without_reading_content(
    tmp_path: Path,
) -> None:
    with pytest.raises(LocalSubtitleError):
        inspect_local_subtitle(tmp_path / "missing.srt")

    txt = tmp_path / "caption.txt"
    txt.write_text("not a subtitle", encoding="utf-8")
    with pytest.raises(LocalSubtitleError):
        inspect_local_subtitle(txt)


def test_huge_subtitle_file_is_rejected_before_full_read(tmp_path: Path) -> None:
    path = tmp_path / "huge.srt"
    with path.open("wb") as stream:
        stream.truncate(MAX_LOCAL_SUBTITLE_BYTES + 1)

    with pytest.raises(LocalSubtitleError, match="too large"):
        inspect_local_subtitle(path)
