"""Tests for bounded MPEG-DASH MPD manifest parsing."""

from __future__ import annotations

import pytest

from samotech_iptv.infrastructure.parsing.dash_manifest_parser import (
    DASHManifestError,
    DASHManifestParser,
)


def test_parse_vod_mpd_preserves_representations() -> None:
    manifest = DASHManifestParser().parse(
        '<MPD type="static"><Period><AdaptationSet><Representation id="low" bandwidth="500000" />'
        '<Representation id="high" bandwidth="1500000" /></AdaptationSet></Period></MPD>'
    )

    assert manifest.is_live is False
    assert manifest.representations[1].bandwidth == 1500000


def test_parse_live_mpd_detects_dynamic_type() -> None:
    manifest = DASHManifestParser().parse(
        '<MPD type="dynamic"><Period><AdaptationSet><Representation id="live" />'
        "</AdaptationSet></Period></MPD>"
    )

    assert manifest.is_live is True


@pytest.mark.parametrize("text", ["", "<Playlist />", "<MPD />", "<MPD>"])
def test_parse_rejects_malformed_or_unrepresentable_mpd(text: str) -> None:
    with pytest.raises(DASHManifestError):
        DASHManifestParser().parse(text)
