from __future__ import annotations

import tomllib
from pathlib import Path

import pytest
from scripts.generate_release_notes import ReleaseNotesError, generate_release_notes

_ROOT = Path(__file__).resolve().parents[1]

_METADATA = """version=0.1.1
release_tag=v0.1.1
commit=abc123def456
workflow_run=123456789
workflow_url=https://github.com/SamoTech/samotech-iptv-player/actions/runs/123456789
artifact=SamoTech-IPTV-Player-Windows-x64-v0.1.1.exe
sha256=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
size_bytes=135490319
build_timestamp_utc=2026-08-17T10:00:00Z
architecture=Windows x64
python=3.13
pyinstaller=6.22.1
pyside6=6.11.1
python_vlc=3.0.21203
vlc=3.0.23
validation_summary=PASS: all blocking gates
"""
_LIMITATIONS = """before
<!-- ZERO_TOUCH_RELEASE_LIMITATIONS_BEGIN -->
- Current limitation from project status.
<!-- ZERO_TOUCH_RELEASE_LIMITATIONS_END -->
after
"""


def _write_inputs(tmp_path: Path, metadata: str = _METADATA) -> tuple[Path, Path, Path, Path]:
    template = tmp_path / "template.md"
    metadata_file = tmp_path / "metadata.txt"
    limitations = tmp_path / "PROJECT_STATUS.md"
    output = tmp_path / "release-notes.md"
    template.write_text(
        (_ROOT / "packaging/release_notes_template.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    metadata_file.write_text(metadata, encoding="utf-8")
    limitations.write_text(_LIMITATIONS, encoding="utf-8")
    return template, metadata_file, limitations, output


def test_generate_release_notes_substitutes_current_build_metadata(tmp_path: Path) -> None:
    template, metadata, limitations, output = _write_inputs(tmp_path)

    generate_release_notes(
        template_path=template,
        metadata_path=metadata,
        limitations_path=limitations,
        output_path=output,
    )

    body = output.read_text(encoding="utf-8")
    assert "SamoTech IPTV Player v0.1.1" in body
    assert "SamoTech-IPTV-Player-Windows-x64-v0.1.1.exe" in body
    assert "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef" in body
    assert "abc123def456" in body
    assert "123456789" in body
    assert "Current limitation from project status." in body
    assert "{{" not in body


def test_generate_release_notes_rejects_stale_hard_coded_template_data(tmp_path: Path) -> None:
    template, metadata, limitations, output = _write_inputs(tmp_path)
    template.write_text("v0.1.0 deadbeef\n", encoding="utf-8")

    with pytest.raises(ReleaseNotesError, match="hard-coded version"):
        generate_release_notes(
            template_path=template,
            metadata_path=metadata,
            limitations_path=limitations,
            output_path=output,
        )


def test_generate_release_notes_rejects_stale_hard_coded_hash(tmp_path: Path) -> None:
    template, metadata, limitations, output = _write_inputs(tmp_path)
    template.write_text(
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef", encoding="utf-8"
    )

    with pytest.raises(ReleaseNotesError, match="hard-coded SHA256"):
        generate_release_notes(
            template_path=template,
            metadata_path=metadata,
            limitations_path=limitations,
            output_path=output,
        )


def test_generate_release_notes_rejects_missing_metadata(tmp_path: Path) -> None:
    template, metadata, limitations, output = _write_inputs(tmp_path, "version=0.1.1\n")

    with pytest.raises(ReleaseNotesError, match="missing metadata keys"):
        generate_release_notes(
            template_path=template,
            metadata_path=metadata,
            limitations_path=limitations,
            output_path=output,
        )


def test_generate_release_notes_rejects_tag_version_mismatch(tmp_path: Path) -> None:
    mismatched = _METADATA.replace("release_tag=v0.1.1", "release_tag=v0.1.2")
    template, metadata, limitations, output = _write_inputs(tmp_path, mismatched)

    with pytest.raises(ReleaseNotesError, match="does not match application version"):
        generate_release_notes(
            template_path=template,
            metadata_path=metadata,
            limitations_path=limitations,
            output_path=output,
        )


def test_runtime_application_version_matches_pyproject() -> None:
    with (_ROOT / "pyproject.toml").open("rb") as file:
        expected = tomllib.load(file)["project"]["version"]

    from samotech_iptv.core.constants import APP_VERSION

    assert APP_VERSION == expected


def test_generate_release_notes_requires_authoritative_limitations(tmp_path: Path) -> None:
    template, metadata, limitations, output = _write_inputs(tmp_path)
    limitations.write_text("No markers", encoding="utf-8")

    with pytest.raises(ReleaseNotesError, match="missing zero-touch release limitation markers"):
        generate_release_notes(
            template_path=template,
            metadata_path=metadata,
            limitations_path=limitations,
            output_path=output,
        )
