from __future__ import annotations

from samotech_iptv.application.smart_import import (
    DetectedProviderInput,
    ImportProtocol,
    detect_provider_input,
    mask_mac,
    mask_password,
    suggest_provider_id,
)


def test_xtream_raw_url_and_query_fields() -> None:
    result = detect_provider_input(
        "http://stream.example:8080/get.php?password=pw123&username=user1&type=m3u_plus&output=ts"
    )
    assert result.protocol is ImportProtocol.XTREAM
    assert result.server_url == "http://stream.example:8080"
    assert result.username == "user1"
    assert result.password == "pw123"  # noqa: S105
    assert result.output_format == "ts"
    assert result.is_complete


def test_xtream_authority_credentials_are_normalized_without_credentials_in_server() -> None:
    result = detect_provider_input("http://user1:pw123@stream.example:8080/player_api.php")
    assert result.protocol is ImportProtocol.XTREAM
    assert result.server_url == "http://stream.example:8080"
    assert result.username == "user1"
    assert result.password == "pw123"  # noqa: S105


def test_xtream_server_username_password_labels() -> None:
    result = detect_provider_input(
        "Server: http://stream.example:8080/\nUsername = user1\nPassword: pw123"
    )
    assert result.protocol is ImportProtocol.XTREAM
    assert result.server_url == "http://stream.example:8080"
    assert result.username == "user1"
    assert result.password == "pw123"  # noqa: S105


def test_m3u_url_and_content_are_detected_locally() -> None:
    url_result = detect_provider_input("M3U URL: https://example.test/playlist.m3u")
    assert url_result.protocol is ImportProtocol.M3U
    assert url_result.playlist_url == "https://example.test/playlist.m3u"
    content_result = detect_provider_input("#EXTM3U\n#EXTINF:-1,News\nhttps://example.test/live")
    assert content_result.protocol is ImportProtocol.M3U
    assert content_result.missing_required_fields == ("playlist URL",)


def test_mag_portal_and_mac_are_detected_and_masked() -> None:
    result = detect_provider_input("Portal: http://portal.example/c/\nMAC = 00:11:22:33:44:55")
    assert result.protocol is ImportProtocol.MAG
    assert result.portal_url == "http://portal.example/c/"
    assert result.mac_address == "00:11:22:33:44:55"
    assert mask_mac(result.mac_address) == "••:••:••:••:••:55"


def test_missing_xtream_password_requests_only_password() -> None:
    result = detect_provider_input("Xtream URL: http://stream.example:8080\nUsername: user1")
    assert result.protocol is ImportProtocol.XTREAM
    assert result.missing_required_fields == ("password",)
    assert result.warnings == ("Password is required.",)


def test_missing_mag_mac_requests_only_mac() -> None:
    result = detect_provider_input("MAG Portal: http://portal.example/c/")
    assert result.protocol is ImportProtocol.MAG
    assert result.missing_required_fields == ("MAC address",)


def test_ambiguous_input_does_not_silently_choose() -> None:
    result = detect_provider_input("http://stream.example/playlist.m3u\nhttp://portal.example/c/")
    assert result.protocol is ImportProtocol.AMBIGUOUS
    assert set(result.candidates) == {ImportProtocol.M3U, ImportProtocol.MAG}


def test_case_whitespace_and_surrounding_text_are_tolerated() -> None:
    result = detect_provider_input(
        "Copied from account\n  SERVER = https://stream.example:443/  \n"
        " USERNAME = User\n PASSWORD = Pass\n"
    )
    assert result.protocol is ImportProtocol.XTREAM
    assert result.server_url == "https://stream.example:443"
    assert result.username == "User"
    assert result.password == "Pass"  # noqa: S105


def test_invalid_input_is_safe_and_secret_masking_is_stable() -> None:
    result = detect_provider_input("hello this is not IPTV configuration")
    assert result.protocol is ImportProtocol.UNKNOWN
    assert not result.is_complete
    assert mask_password("secret") == "••••••••"
    assert mask_password(None) == "Not detected"
    synthetic_password = "secret"  # noqa: S105
    assert "secret" not in repr(
        DetectedProviderInput(ImportProtocol.XTREAM, password=synthetic_password)  # noqa: S106
    )


def test_provider_id_suggestion_never_uses_password() -> None:
    result = detect_provider_input(
        "Server: http://stream.example:8080\nUsername: user1\nPassword: secret-pass"
    )
    suggested = suggest_provider_id(result)
    assert suggested == "xtream-stream-example-user1"
    assert "secret" not in suggested
