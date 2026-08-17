"""Generate a release body from current build metadata and project status."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

_METADATA_KEY = re.compile(r"^[a-z][a-z0-9_]*$")
_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")
_VERSION = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
_STALE_VERSION = re.compile(r"\bv\d+\.\d+\.\d+\b")
_STALE_ARTIFACT = re.compile(r"SamoTech-IPTV-Player-Windows-x64-v\d+\.\d+\.\d+\.exe")
_STALE_HASH = re.compile(r"(?<![0-9a-fA-F])[0-9a-fA-F]{64}(?![0-9a-fA-F])")
_BEGIN_MARKER = "<!-- ZERO_TOUCH_RELEASE_LIMITATIONS_BEGIN -->"
_END_MARKER = "<!-- ZERO_TOUCH_RELEASE_LIMITATIONS_END -->"
_REQUIRED_METADATA = {
    "version",
    "release_tag",
    "commit",
    "workflow_run",
    "workflow_url",
    "artifact",
    "sha256",
    "size_bytes",
    "build_timestamp_utc",
    "architecture",
    "python",
    "pyinstaller",
    "pyside6",
    "python_vlc",
    "vlc",
    "validation_summary",
}


class ReleaseNotesError(ValueError):
    """Raised when release-note inputs are incomplete or inconsistent."""


def _parse_metadata(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw_line.strip():
            continue
        if "=" not in raw_line:
            raise ReleaseNotesError(f"metadata line {line_number} is not key=value")
        key, value = raw_line.split("=", 1)
        if not _METADATA_KEY.fullmatch(key):
            raise ReleaseNotesError(f"invalid metadata key: {key!r}")
        values[key] = value
    missing = sorted(_REQUIRED_METADATA - values.keys())
    if missing:
        raise ReleaseNotesError(f"missing metadata keys: {', '.join(missing)}")
    return values


def _extract_limitations(path: Path) -> str:
    content = path.read_text(encoding="utf-8")
    try:
        body = content.split(_BEGIN_MARKER, 1)[1].split(_END_MARKER, 1)[0].strip()
    except (IndexError, ValueError) as exc:
        raise ReleaseNotesError(
            "project status is missing zero-touch release limitation markers"
        ) from exc
    if not body:
        raise ReleaseNotesError("project status contains empty zero-touch release limitations")
    return body


def _validate_template(template: str) -> None:
    if _STALE_ARTIFACT.search(template) or _STALE_VERSION.search(template):
        raise ReleaseNotesError("release template contains a hard-coded version")
    if _STALE_HASH.search(template):
        raise ReleaseNotesError("release template contains a hard-coded SHA256")


def _validate_metadata(values: dict[str, str]) -> None:
    version = values["version"]
    release_tag = values["release_tag"]
    if not _VERSION.fullmatch(version):
        raise ReleaseNotesError(f"invalid application version: {version!r}")
    if release_tag != f"v{version}":
        raise ReleaseNotesError(
            f"release tag {release_tag!r} does not match application version {version!r}"
        )
    if not _SHA256.fullmatch(values["sha256"]):
        raise ReleaseNotesError("invalid artifact SHA256")
    try:
        size = int(values["size_bytes"])
    except ValueError as exc:
        raise ReleaseNotesError("artifact size_bytes must be an integer") from exc
    if size <= 0:
        raise ReleaseNotesError("artifact size_bytes must be positive")
    if not values["commit"]:
        raise ReleaseNotesError("commit metadata is empty")
    if not values["artifact"].endswith(".exe"):
        raise ReleaseNotesError("artifact metadata must name an EXE")


def generate_release_notes(
    *, template_path: Path, metadata_path: Path, limitations_path: Path, output_path: Path
) -> None:
    template = template_path.read_text(encoding="utf-8")
    _validate_template(template)
    values = _parse_metadata(metadata_path)
    _validate_metadata(values)
    values["known_limitations"] = _extract_limitations(limitations_path)

    rendered = template
    for key, value in values.items():
        rendered = rendered.replace(f"{{{{{key.upper()}}}}}", value)
    if "{{" in rendered or "}}" in rendered:
        unresolved = sorted(set(re.findall(r"\{\{[^{}]+\}\}", rendered)))
        raise ReleaseNotesError(f"unresolved release-note placeholders: {', '.join(unresolved)}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered.rstrip() + "\n", encoding="utf-8")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--metadata-file", type=Path, required=True)
    parser.add_argument("--limitations-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        generate_release_notes(
            template_path=args.template,
            metadata_path=args.metadata_file,
            limitations_path=args.limitations_file,
            output_path=args.output,
        )
    except (OSError, ReleaseNotesError) as exc:
        print(f"release-notes generation failed: {exc}")
        return 1
    print(f"release-notes generated: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
