"""Tests for HLS manifest parsing distinct from IPTV M3U content parsing."""

from __future__ import annotations

import pytest

from samotech_iptv.infrastructure.parsing.hls_manifest_parser import (
    HLSManifestError,
    HLSManifestParser,
)


def test_parse_master_manifest_preserves_variants() -> None:
    parser = HLSManifestParser()

    manifest = parser.parse(
        "#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=800000\nlow.m3u8\n"
        "#EXT-X-STREAM-INF:BANDWIDTH=1600000\nhigh.m3u8\n"
    )

    assert manifest.kind == "master"
    assert manifest.variants[1].bandwidth == 1600000


def test_parse_live_media_manifest_preserves_segments() -> None:
    manifest = HLSManifestParser().parse(
        "#EXTM3U\n#EXT-X-TARGETDURATION:6\n#EXTINF:6,\nsegment-1.ts\n"
    )

    assert manifest.kind == "media"
    assert manifest.is_live is True
    assert manifest.segments == ("segment-1.ts",)


def test_parse_vod_media_manifest_detects_endlist() -> None:
    manifest = HLSManifestParser().parse("#EXTM3U\n#EXTINF:6,\nsegment-1.ts\n#EXT-X-ENDLIST\n")

    assert manifest.is_live is False


@pytest.mark.parametrize(
    "text",
    ["", "#EXTINF:6,\nsegment.ts", "#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=1"],
)
def test_parse_rejects_malformed_manifest(text: str) -> None:
    with pytest.raises(HLSManifestError):
        HLSManifestParser().parse(text)
