from providers.mag.protocol_profile import (
    MAGOperation,
    StalkerClientCompatibilityProfile,
)

_EXPECTED_VALUE = "fixture-capital-token"


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
