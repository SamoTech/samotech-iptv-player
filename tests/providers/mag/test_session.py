"""Unit tests for MAGSession authentication logic."""

from unittest.mock import AsyncMock

import pytest
from providers.base.errors import AuthError
from providers.mag.credentials import MAGCredentials
from providers.mag.session import MAGSession

_FIRST_SESSION_VALUE = "initial-session-value"
_REFRESHED_SESSION_VALUE = "refreshed-session-value"


def _make_session(
    token_in_response: bool = True,
) -> tuple[MAGSession, AsyncMock, MAGCredentials]:
    creds = MAGCredentials(portal_url="https://portal.example.com", mac_address="AA:BB:CC:DD:EE:FF")
    conn = AsyncMock()
    payload = (
        {"js": {"token": _FIRST_SESSION_VALUE, "token_TTL": 3600}}
        if token_in_response
        else {"js": {}}
    )
    conn.get = AsyncMock(return_value=payload)
    sess = MAGSession(conn, creds)
    return sess, conn, creds


@pytest.mark.asyncio
async def test_authenticate_stores_token() -> None:
    sess, _, creds = _make_session()
    await sess.authenticate()
    assert creds.token == _FIRST_SESSION_VALUE
    assert sess.is_authenticated


@pytest.mark.asyncio
async def test_authenticate_raises_on_missing_token() -> None:
    sess, _, _ = _make_session(token_in_response=False)
    with pytest.raises(AuthError):
        await sess.authenticate()


@pytest.mark.asyncio
async def test_refresh_updates_token() -> None:
    sess, conn, creds = _make_session()
    await sess.authenticate()
    conn.get.return_value = {"js": {"token": _REFRESHED_SESSION_VALUE, "token_TTL": 3600}}
    await sess.refresh()
    assert creds.token == _REFRESHED_SESSION_VALUE
