from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from providers.base.errors import AuthError
from providers.mag.credentials import MAGCredentials
from providers.mag.protocol_profile import MAGAuthState
from providers.mag.session import MAGSession

_SESSION_VALUE = "fixture-token"
_CREDENTIAL_VALUE = "fixture-password"


def _session(
    *,
    profile_required: bool = False,
    auth_mode: str = "mac_only",
    login: str = "",
    credential_value: str = "",
    authorization_key: str = "",
    device_id: str = "",
    device_id2: str = "",
) -> tuple[MAGSession, AsyncMock, MAGCredentials]:
    credentials = MAGCredentials(
        portal_url="http://fixture.test/c/",
        mac_address="00:11:22:33:44:55",
        profile_required=profile_required,
        auth_mode=auth_mode,
        login=login,
        password=credential_value,
        authorization_key=authorization_key,
        device_id=device_id,
        device_id2=device_id2,
    )
    connection = AsyncMock()
    connection.get = AsyncMock(
        side_effect=[
            {"js": {"token": _SESSION_VALUE, "token_TTL": "120"}},
            {"js": {"id": "fixture-profile", "stb_type": "MAG250"}},
        ]
    )
    connection.post = AsyncMock(return_value={"js": True})
    return MAGSession(connection, credentials), connection, credentials


@pytest.mark.asyncio
async def test_handshake_only_reaches_session_validated() -> None:
    session, connection, credentials = _session()

    await session.authenticate()

    assert session.auth_state is MAGAuthState.SESSION_VALIDATED
    assert credentials.token == _SESSION_VALUE
    connection.post.assert_not_awaited()
    assert connection.get.await_count == 1


@pytest.mark.asyncio
async def test_handshake_get_profile_and_do_auth_are_explicit_stages() -> None:
    session, connection, credentials = _session(
        profile_required=True,
        auth_mode="mac_plus_login",
        login="fixture-login",
        credential_value=_CREDENTIAL_VALUE,
        device_id="fixture-device-id",
        device_id2="fixture-device-id2",
    )

    await session.authenticate()

    assert session.auth_state is MAGAuthState.SESSION_VALIDATED
    assert session.last_profile_classification == "PROFILE_SUCCESS"
    assert connection.get.await_count == 2
    connection.post.assert_awaited_once()
    form = connection.post.await_args.kwargs["data"]
    assert form["action"] == "do_auth"
    assert form["login"] == "fixture-login"
    assert form["password"] == _CREDENTIAL_VALUE
    assert form["device_id"] == "fixture-device-id"
    assert form["device_id2"] == "fixture-device-id2"
    assert "fixture-password" not in repr(session.credentials)


@pytest.mark.asyncio
async def test_mac_plus_login_without_credentials_is_login_required() -> None:
    session, connection, _ = _session(auth_mode="mac_plus_login")

    with pytest.raises(AuthError, match="LOGIN_REQUIRED"):
        await session.authenticate()

    connection.post.assert_not_awaited()


@pytest.mark.asyncio
async def test_authorization_key_without_key_is_explicitly_blocked() -> None:
    session, connection, _ = _session(auth_mode="authorization_key")

    with pytest.raises(AuthError, match="AUTH_KEY_REQUIRED"):
        await session.authenticate()

    connection.post.assert_not_awaited()


@pytest.mark.asyncio
async def test_profile_stage_can_be_called_with_empty_identity_fields() -> None:
    session, connection, _ = _session()

    await session.authenticate()
    await session.get_profile()

    profile_params = connection.get.await_args_list[-1].kwargs["params"]
    assert profile_params == {"type": "stb", "action": "get_profile", "JsHttpRequest": "1-xml"}


@pytest.mark.asyncio
async def test_explicit_identity_fields_are_sent_only_when_present() -> None:
    session, connection, _ = _session(
        profile_required=True, device_id="device-a", device_id2="device-b"
    )

    await session.authenticate()

    profile_params = connection.get.await_args_list[-1].kwargs["params"]
    assert profile_params["device_id"] == "device-a"
    assert profile_params["device_id2"] == "device-b"
    assert "serial_number" not in profile_params


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("marker", "expected"),
    [
        ("stb_type is not allowed", "STB_MODEL_REJECTED"),
        ("device_id required", "DEVICE_ID_REQUIRED"),
        ("stb is not authorized", "STB_NOT_AUTHORIZED"),
    ],
)
async def test_profile_policy_markers_are_normalized_safely(marker: str, expected: str) -> None:
    session, connection, _ = _session(profile_required=True)
    connection.get.side_effect = [
        {"js": {"token": _SESSION_VALUE}},
        {"js": {"error": marker}},
    ]

    with pytest.raises(AuthError, match=expected):
        await session.authenticate()

    assert session.last_profile_classification == expected


@pytest.mark.asyncio
async def test_do_auth_rejection_is_not_success() -> None:
    session, connection, _ = _session(
        auth_mode="mac_plus_login",
        login="fixture-login",
        credential_value=_CREDENTIAL_VALUE,
    )
    connection.post.return_value = {"js": False, "text": "invalid credentials"}

    with pytest.raises(AuthError, match="LOGIN_REQUIRED"):
        await session.authenticate()

    assert session.auth_state is MAGAuthState.DO_AUTH
