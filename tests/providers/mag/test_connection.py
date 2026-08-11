"""Unit tests for MAGConnection."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from providers.mag.connection import MAGConnection, _sanitise_url


def test_sanitise_url_basic() -> None:
    result = _sanitise_url("https://portal.example.com", "/server/load.php")
    assert result == "https://portal.example.com/server/load.php"


def test_sanitise_url_rejects_non_http() -> None:
    with pytest.raises(ValueError, match="http or https"):
        _sanitise_url("ftp://example.com", "/path")


@pytest.mark.asyncio
async def test_open_creates_session() -> None:
    conn = MAGConnection("https://example.com")
    with patch("aiohttp.ClientSession") as mock_session, \
         patch("aiohttp.TCPConnector"):
        mock_sess = MagicMock()
        mock_sess.closed = False
        mock_session.return_value = mock_sess
        await conn.open()
        assert conn._session is mock_sess


@pytest.mark.asyncio
async def test_close_calls_session_close() -> None:
    conn = MAGConnection("https://example.com")
    mock_sess = AsyncMock()
    mock_sess.closed = False
    conn._session = mock_sess
    await conn.close()
    mock_sess.close.assert_awaited_once()
