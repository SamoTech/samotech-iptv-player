from __future__ import annotations

import json
from typing import TYPE_CHECKING

from tools.phase26_real_playback_harness import (
    PUBLIC_FIXTURES,
    MockEndpointServer,
    run_synthetic,
    sanitized_url_identifier,
    write_evidence,
    write_generated_m3u,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_generated_m3u_contains_metadata_and_no_credentials(tmp_path: Path) -> None:
    output = tmp_path / "playlist.m3u"
    with MockEndpointServer() as server:
        write_generated_m3u(output, server.base_url)
    content = output.read_text(encoding="utf-8")
    assert content.startswith("#EXTM3U")
    assert 'group-title="News"' in content
    assert 'tvg-id="synthetic-news"' in content
    assert "username" not in content.casefold()
    assert "password" not in content.casefold()
    assert "token=" not in content.casefold()


def test_mock_endpoint_serves_m3u_xtream_and_mag_boundaries() -> None:
    with MockEndpointServer() as server:
        m3u = server.request_text("/m3u/playlist.m3u8")
        xtream = json.loads(server.request_text("/player_api.php?action=get_live_streams"))
        mag = json.loads(server.request_text("/stalker/create_link"))
    assert "#EXTM3U" in m3u
    assert xtream[0]["name"] == "Synthetic News"
    assert mag["js"]["cmd"].startswith("http://127.0.0.1:")


def test_mock_scenarios_produce_sanitized_evidence(tmp_path: Path) -> None:
    for scenario in ("progress", "stall", "interruption", "switching"):
        result = run_synthetic(scenario=scenario)
        assert result.result == "PASS"
        assert result.samples
        assert all(sample.stream_identifier_hash for sample in result.samples)
        assert all("://" not in sample.stream_identifier_hash for sample in result.samples)
        path = tmp_path / f"{scenario}.json"
        write_evidence([result], path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["security"]["raw_stream_urls_persisted"] is False


def test_public_fixture_manifest_is_credential_free() -> None:
    assert PUBLIC_FIXTURES
    for fixture in PUBLIC_FIXTURES.values():
        url = fixture["url"].casefold()
        assert "username" not in url
        assert "password" not in url
        assert "token=" not in url
        assert "cookie=" not in url
        assert "authorization" not in url


def test_stream_identifier_hash_does_not_expose_input() -> None:
    fixture_url = "https://example.test/stream.m3u8?auth=fixture"
    digest = sanitized_url_identifier(fixture_url)
    assert fixture_url not in digest
    assert len(digest) == 16
