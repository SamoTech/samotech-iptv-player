"""Unit tests for MAGConnection."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from providers.mag.connection import MAGConnection, _sanitise_url
from providers.base.errors import NetworkError


def test_sanitise_url_basic():
    result = _sanitise_url("https://portal.example.com", "/server/load.php")
    assert result == "https://portal.example.com/server/load.php"


def test_sanitise_url_rejects_non_http():
    with pytest.raises(ValueError, match="http or https"):
        _sanitise_url("ftp://example.com", "/path")


@pytest.mark.asyncio
async def test_open_creates_session():
    conn = MAGConnection("https://example.com")
    with patch("aiohttp.ClientSession") as MockSession, \
         patch("aiohttp.TCPConnector"):
        mock_sess = MagicMock()
        mock_sess.closed = False
        MockSession.return_value = mock_sess
        await conn.open()
        assert conn._session is mock_sess


@pytest.mark.asyncio
async def test_close_calls_session_close():
    conn = MAGConnection("https://example.com")
    mock_sess = AsyncMock()
    mock_sess.closed = False
    conn._session = mock_sess
    await conn.close()
    mock_sess.close.assert_awaited_once()
