from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "LOCAL_SUBTITLE_SUFFIXES",
    "MAX_LOCAL_SUBTITLE_BYTES",
    "LocalSubtitleFile",
    "LocalSubtitleError",
    "inspect_local_subtitle",
]

LOCAL_SUBTITLE_SUFFIXES = frozenset({".srt", ".ass", ".ssa", ".vtt"})
MAX_LOCAL_SUBTITLE_BYTES = 16 * 1024 * 1024
_SAMPLE_BYTES = 128 * 1024


class LocalSubtitleError(ValueError):
    """Safe user-facing local subtitle validation failure."""


@dataclass(frozen=True)
class LocalSubtitleFile:
    """Validated local subtitle metadata; subtitle contents never leave the file boundary."""

    path: Path
    display_name: str
    suffix: str
    size_bytes: int
    encoding: str


def _decode_probe(data: bytes) -> str:
    """Decode only a bounded probe to validate text without retaining subtitle contents."""
    for encoding in ("utf-8-sig", "utf-16", "cp1256", "cp1252"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise LocalSubtitleError("Subtitle text encoding is not supported")


def _validate_structure(suffix: str, text: str) -> None:
    """Reject obviously malformed subtitle containers without retaining their text."""
    normalized = text.casefold()
    if suffix == ".srt" and not re.search(
        r"\d{2}:\d{2}:\d{2}[,.]\d{3}\s+-->\s+\d{2}:\d{2}:\d{2}[,.]\d{3}",
        text,
    ):
        raise LocalSubtitleError("Subtitle timestamps are invalid")
    if suffix == ".vtt" and not normalized.lstrip("\ufeff \t\r\n").startswith("webvtt"):
        raise LocalSubtitleError("VTT subtitle header is missing")
    if suffix in {".ass", ".ssa"} and "[events]" not in normalized:
        raise LocalSubtitleError("ASS/SSA subtitle events are missing")


def inspect_local_subtitle(path: str | Path) -> LocalSubtitleFile:
    """Validate a local subtitle path without uploading, logging, or returning its contents."""
    candidate = Path(path).expanduser()
    suffix = candidate.suffix.casefold()
    if suffix not in LOCAL_SUBTITLE_SUFFIXES:
        raise LocalSubtitleError("Choose an SRT, ASS, SSA, or VTT subtitle file")
    try:
        resolved = candidate.resolve(strict=True)
        stat = resolved.stat()
        if not resolved.is_file():
            raise LocalSubtitleError("The selected subtitle is not a file")
        if stat.st_size <= 0:
            raise LocalSubtitleError("The selected subtitle file is empty")
        if stat.st_size > MAX_LOCAL_SUBTITLE_BYTES:
            raise LocalSubtitleError("The selected subtitle file is too large")
        with resolved.open("rb") as stream:
            probe = stream.read(min(_SAMPLE_BYTES, stat.st_size))
    except LocalSubtitleError:
        raise
    except (OSError, UnicodeError) as exc:
        raise LocalSubtitleError("The selected subtitle file cannot be read") from exc
    decoded = _decode_probe(probe)
    _validate_structure(suffix, decoded)
    return LocalSubtitleFile(
        path=resolved,
        display_name=resolved.name,
        suffix=suffix,
        size_bytes=stat.st_size,
        encoding="utf-8-or-safe-legacy",
    )
