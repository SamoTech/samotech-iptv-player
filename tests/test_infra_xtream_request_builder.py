"""Tests for credential-safe Xtream request construction."""

from __future__ import annotations

from samotech_iptv.domain.value_objects.credential import Credential
from samotech_iptv.domain.value_objects.url import URL
from samotech_iptv.infrastructure.providers.xtream_request_builder import XtreamRequestBuilder


def test_player_api_builds_encoded_action_request() -> None:
    builder = XtreamRequestBuilder(
        URL("https://portal.example.test:8443/base"),
        Credential("user@example.test", "secret value"),
    )

    request_url = builder.player_api("get_live_streams", category_id="7")

    assert str(request_url) == (
        "https://portal.example.test:8443/player_api.php?username=user%40example.test"
        "&password=secret+value&action=get_live_streams&category_id=7"
    )
    assert "secret value" not in repr(builder.credential)


def test_stream_url_encodes_credential_and_identifier_path_segments() -> None:
    builder = XtreamRequestBuilder(
        URL("https://portal.example.test"), Credential("alice/admin", "secret?token#value")
    )

    request_url = builder.stream_url("live", "101/../../private", "m3u8?bad")

    assert str(request_url) == (
        "https://portal.example.test/live/alice%2Fadmin/secret%3Ftoken%23value/"
        "101%2F..%2F..%2Fprivate.m3u8%3Fbad"
    )


def test_stream_url_builds_live_vod_and_series_compatible_paths() -> None:
    builder = XtreamRequestBuilder(
        URL("https://portal.example.test"), Credential("alice", "not-for-logs")
    )

    assert str(builder.stream_url("live", "101", "m3u8")) == (
        "https://portal.example.test/live/alice/not-for-logs/101.m3u8"
    )
