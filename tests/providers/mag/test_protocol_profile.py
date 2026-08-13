from providers.mag.protocol_profile import (
    MAGOperation,
    StalkerClientCompatibilityProfile,
    StalkerPortalPhpLegacyProfile,
)

_EXPECTED_VALUE = "fixture-capital-token"
_SESSION_VALUE = "fixture-session-token"


def test_parse_handshake_accepts_source_observed_capital_token_key() -> None:
    profile = StalkerClientCompatibilityProfile()

    handshake = profile.parse_handshake({"js": {"Token": _EXPECTED_VALUE, "token_TTL": "45"}})

    assert handshake.token == _EXPECTED_VALUE
    assert handshake.ttl_seconds == 45


def test_profile_request_separates_explicit_post_form_from_query() -> None:
    profile = StalkerClientCompatibilityProfile(
        handshake_method="POST",
        handshake_form_params={"prehash": "false"},
    )

    request = profile.build_request(
        "http://portal.example/c/",
        MAGOperation.HANDSHAKE,
    )

    assert request.method == "POST"
    assert request.params["action"] == "handshake"
    assert request.form["action"] == "handshake"
    assert request.form["prehash"] == "false"


def test_profile_base_preserves_origin_vs_configured_path() -> None:
    profile = StalkerClientCompatibilityProfile()

    assert profile.request_base_url("http://host/") == "http://host"
    assert profile.request_base_url("http://host/c/") == "http://host"
    assert profile.request_base_url("http://host/c") == "http://host"
    assert profile.request_base_url("http://host/stalker_portal/") == "http://host"
    assert profile.request_base_url("http://host/portal.php") == "http://host"


def test_portal_php_legacy_profile_matches_working_client_fingerprint() -> None:
    profile = StalkerPortalPhpLegacyProfile()
    portal_url = "http://host/c/"
    mac_address = "00:11:22:33:44:55"

    request = profile.build_request(portal_url, MAGOperation.HANDSHAKE)
    headers = profile.request_headers(
        portal_url,
        mac_address=mac_address,
        serial_number="",
        device_id="",
        device_id2="",
        token="",
    )
    authenticated_headers = profile.request_headers(
        portal_url,
        mac_address=mac_address,
        serial_number="",
        device_id="",
        device_id2="",
        token=_SESSION_VALUE,
    )

    assert request.base_url == "http://host"
    assert request.endpoint == "portal.php"
    assert request.method == "GET"
    assert request.params == {
        "type": "stb",
        "action": "handshake",
        "token": "",
        "JsHttpRequest": "1-xml",
    }
    assert headers["Authorization"] == f"MAC {mac_address}"
    assert headers["Cookie"] == f"mac={mac_address}"
    assert headers["Referer"] == "http://host/c/"
    assert headers["Accept"] == "application/json, text/javascript, */*; q=0.01"
    assert headers["X-Requested-With"] == "XMLHttpRequest"
    assert headers["User-Agent"].startswith("Mozilla/5.0 (Windows NT 10.0")
    assert "X-User-Mac" not in headers
    assert authenticated_headers["Authorization"] == f"Bearer {_SESSION_VALUE}"
    assert profile.requires_account_info is True
    assert profile.uses_direct_live_catalogue is True
    assert profile.uses_direct_channel_urls is True
    assert profile.operation_params(MAGOperation.ACCOUNT_INFO)["JsHttpRequest"] == "1-xml"
    assert profile.operation_params(MAGOperation.CHANNELS)["JsHttpRequest"] == "1-xml"
    assert profile.build_request(portal_url, MAGOperation.ACCOUNT_INFO).endpoint == "portal.php"
    assert profile.build_request(portal_url, MAGOperation.CHANNELS).endpoint == "portal.php"
    assert profile.build_request(portal_url, MAGOperation.LIVE_GENRES).endpoint == "server/load.php"
