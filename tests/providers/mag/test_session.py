"""Unit tests for MAGSession authentication logic."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from providers.mag.session import MAGSession
from providers.mag.credentials import MAGCredentials
from providers.base.errors import AuthError


def _make_session(token_in_response=True):
    creds = MAGCredentials(portal_url="https://portal.example.com", mac_address="AA:BB:CC:DD:EE:FF")
    conn = AsyncMock()
    payload = {"js": {"token": "tok123", "token_TTL": 3600}} if token_in_response else {"js": {}}
    conn.get = AsyncMock(return_value=payload)
    sess = MAGSession(conn, creds)
    return sess, conn, creds


@pytest.mark.asyncio
async def test_authenticate_stores_token():
    sess, _, creds = _make_session()
    await sess.authenticate()
    assert creds.token == "tok123"
    assert sess.is_authenticated


@pytest.mark.asyncio
async def test_authenticate_raises_on_missing_token():
    sess, _, _ = _make_session(token_in_response=False)
    with pytest.raises(AuthError):
        await sess.authenticate()


@pytest.mark.asyncio
async def test_refresh_updates_token():
    sess, conn, creds = _make_session()
    await sess.authenticate()
    conn.get.return_value = {"js": {"token": "tok456", "token_TTL": 3600}}
    await sess.refresh()
    assert creds.token == "tok456"
