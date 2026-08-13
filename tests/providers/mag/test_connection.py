"""Unit tests for MAGConnection."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from providers.base.errors import NetworkError
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
    with patch("aiohttp.ClientSession") as mock_session, patch("aiohttp.TCPConnector"):
        mock_sess = MagicMock()
        mock_sess.closed = False
        mock_session.return_value = mock_sess
        await conn.open()
        assert conn._session is mock_sess


class _Response:
    def __init__(self, body: bytes, *, content_type: str = "text/javascript") -> None:
        self.status = 200
        self.headers = {"Content-Type": content_type}
        self._body = body

    async def __aenter__(self) -> "_Response":
        return self

    async def __aexit__(self, *_: object) -> None:
        return None

    async def read(self) -> bytes:
        return self._body

    def raise_for_status(self) -> None:
        return None


class _Session:
    def __init__(self, response: _Response) -> None:
        self.response = response
        self.closed = False

    def request(self, *_: object, **__: object) -> _Response:
        return self.response


@pytest.mark.asyncio
async def test_json_response_is_returned_without_logging_payload(
    caplog: pytest.LogCaptureFixture,
) -> None:
    conn = MAGConnection("https://portal.example.test/c/")
    conn._session = _Session(
        _Response(b'{"js":{"token":"secret-token"}}', content_type="application/json")
    )

    result = await conn.get("/server/load.php")

    assert result == {"js": {"token": "secret-token"}}
    messages = " ".join(record.getMessage() for record in caplog.records)
    assert "secret-token" not in messages
    assert "portal.example.test" not in messages


@pytest.mark.asyncio
async def test_empty_response_is_classified_and_redacted(caplog: pytest.LogCaptureFixture) -> None:
    conn = MAGConnection("https://portal.example.test/c/")
    conn._session = _Session(_Response(b""))

    with pytest.raises(NetworkError, match="response was empty"):
        await conn.get("/server/load.php?type=stb&action=handshake")

    messages = " ".join(record.getMessage() for record in caplog.records)
    assert "ERROR=EMPTY_SESSION_RESPONSE" in messages
    assert "RESPONSE_BYTES=0" in messages
    assert "portal.example.test" not in messages
    assert "Authorization" not in messages


@pytest.mark.asyncio
async def test_malformed_json_is_classified_without_body_leak(
    caplog: pytest.LogCaptureFixture,
) -> None:
    conn = MAGConnection("https://portal.example.test/c/")
    conn._session = _Session(_Response(b"not-json", content_type="text/javascript"))

    with pytest.raises(NetworkError, match="not valid JSON"):
        await conn.get("/server/load.php")

    messages = " ".join(record.getMessage() for record in caplog.records)
    assert "ERROR=MALFORMED_JSON" in messages
    assert "not-json" not in messages
    assert "portal.example.test" not in messages


@pytest.mark.asyncio
async def test_close_calls_session_close() -> None:
    conn = MAGConnection("https://example.com")
    mock_sess = AsyncMock()
    mock_sess.closed = False
    conn._session = mock_sess
    await conn.close()
    mock_sess.close.assert_awaited_once()
