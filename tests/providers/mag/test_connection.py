"""Unit tests for MAGConnection."""

import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
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


class _BodyContent:
    def __init__(self, chunks: list[bytes], error: Exception | None = None) -> None:
        self._chunks = chunks
        self._error = error

    async def iter_chunked(self, _: int) -> object:
        for chunk in self._chunks:
            await asyncio.sleep(0)
            yield chunk
        if self._error is not None:
            raise self._error


class _Response:
    def __init__(
        self,
        body: bytes,
        *,
        content_type: str = "text/javascript",
        transfer_encoding: str = "",
        status: int = 200,
        error_message: str = "synthetic provider error",
    ) -> None:
        self.status = status
        self._error_message = error_message
        self.headers = {"Content-Type": content_type, "Transfer-Encoding": transfer_encoding}
        self.content_length = len(body)
        self._body = body
        self.content = _BodyContent([body] if body else [])

    async def __aenter__(self) -> "_Response":
        return self

    async def __aexit__(self, *_: object) -> None:
        return None

    async def read(self) -> bytes:
        return self._body

    def raise_for_status(self) -> None:
        if self.status >= 400:
            raise aiohttp.ClientResponseError(
                request_info=MagicMock(),
                history=(),
                status=self.status,
                message=self._error_message,
            )


class _TimedOutResponse(_Response):
    def __init__(self, body: bytes = b"") -> None:
        super().__init__(body)
        self.content = _BodyContent([body] if body else [], TimeoutError())


class _PartialTimedOutResponse(_Response):
    def __init__(self, body: bytes, declared_length: int) -> None:
        super().__init__(body)
        self.content_length = declared_length
        self.content = _BodyContent([body], TimeoutError())


class _PartialPayloadErrorResponse(_Response):
    def __init__(self, body: bytes) -> None:
        super().__init__(body)
        self.content = _BodyContent([body], aiohttp.ClientPayloadError("synthetic payload error"))


class _Session:
    def __init__(self, response: _Response) -> None:
        self.response = response
        self.closed = False
        self.request_count = 0

    def request(self, *_: object, **__: object) -> _Response:
        self.request_count += 1
        return self.response


class _NetworkErrorSession:
    closed = False

    def request(self, *_: object, **__: object) -> _Response:
        raise aiohttp.ClientConnectionError("synthetic network error")


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [401, 503])
async def test_http_status_exception_excludes_body_url_query_and_cause(
    status: int,
    caplog: pytest.LogCaptureFixture,
) -> None:
    body_canary = "SAMOSAFE_MAG_HTTP_RESPONSE_BODY"
    query_canary = "SAMOSAFE_MAG_QUERY_TOKEN"
    conn = MAGConnection("https://portal.example.test/c/", max_retries=1)
    conn._session = _Session(
        _Response(
            body_canary.encode(),
            status=status,
            error_message=f"body={body_canary} token={query_canary}",
        )
    )

    with pytest.raises(NetworkError) as caught:
        await conn.get(f"/server/load.php?token={query_canary}")

    error = caught.value
    assert body_canary not in str(error)
    assert query_canary not in str(error)
    assert error.__cause__ is None
    messages = " ".join(record.getMessage() for record in caplog.records)
    assert body_canary not in messages
    assert query_canary not in messages
    assert "portal.example.test" not in messages


@pytest.mark.asyncio
async def test_post_preserves_the_sanitised_request_url() -> None:
    conn = MAGConnection("https://portal.example.test/c/")
    request = AsyncMock(return_value={"js": {}})
    with patch.object(conn, "_request_with_retry", request):
        await conn.post("/portal.php", diagnostic_stage="CATALOGUE")

    request.assert_awaited_once_with(
        "POST",
        "https://portal.example.test/c/portal.php",
        params=None,
        data={},
        headers=None,
        diagnostic_stage="CATALOGUE",
    )


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
async def test_catalogue_response_logs_safe_completion_metadata(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="providers.mag.connection")
    conn = MAGConnection("https://portal.example.test/c/")
    conn._session = _Session(
        _Response(
            b'{"js":{"data":[]}}',
            content_type="application/json",
            transfer_encoding="chunked",
        )
    )

    result = await conn.get("/portal.php", diagnostic_stage="CATALOGUE")

    assert result == {"js": {"data": []}}
    messages = " ".join(record.getMessage() for record in caplog.records)
    assert "STAGE=CATALOGUE_HTTP_RESPONSE" in messages
    assert "ATTEMPT=1/3" in messages
    assert "TOTAL_TIMEOUT=30s" in messages
    assert "CONTENT_LENGTH=18" in messages
    assert "TRANSFER_ENCODING=chunked" in messages
    assert "STAGE=CATALOGUE_BODY_COMPLETE" in messages
    assert "RESPONSE_BYTES=18" in messages
    assert "CHUNKS=1" in messages
    assert "portal.example.test" not in messages


@pytest.mark.asyncio
async def test_catalogue_body_timeout_is_classified_without_sensitive_context(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.WARNING, logger="providers.mag.connection")
    conn = MAGConnection("https://portal.example.test/c/", max_retries=1)
    conn._session = _Session(_TimedOutResponse(b""))

    with pytest.raises(NetworkError, match="failed after 1 attempts"):
        await conn.get("/portal.php", diagnostic_stage="CATALOGUE")

    messages = " ".join(record.getMessage() for record in caplog.records)
    assert "STAGE=CATALOGUE_BODY_INCOMPLETE" in messages
    assert "ERROR=TIMEOUT" in messages
    assert "ATTEMPT=1/1" in messages
    assert "TOTAL_TIMEOUT=30s" in messages
    assert "RECEIVED_BYTES=0" in messages
    assert "portal.example.test" not in messages


@pytest.mark.asyncio
async def test_catalogue_partial_body_timeout_logs_aggregate_progress_without_payload(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.WARNING, logger="providers.mag.connection")
    conn = MAGConnection("https://portal.example.test/c/", max_retries=1)
    conn._session = _Session(_PartialTimedOutResponse(b"partial", declared_length=64))

    with pytest.raises(NetworkError, match="failed after 1 attempts"):
        await conn.get("/portal.php", diagnostic_stage="CATALOGUE")

    messages = " ".join(record.getMessage() for record in caplog.records)
    assert "STAGE=CATALOGUE_BODY_INCOMPLETE" in messages
    assert "CONTENT_LENGTH=64" in messages
    assert "ATTEMPT=1/1" in messages
    assert "TOTAL_TIMEOUT=30s" in messages
    assert "RECEIVED_BYTES=7" in messages
    assert "CHUNKS=1" in messages
    assert "FIRST_BODY_BYTE=" in messages
    assert "LAST_CHUNK_AGE=" in messages
    assert "partial" not in messages
    assert "portal.example.test" not in messages


@pytest.mark.asyncio
async def test_catalogue_payload_error_is_classified_without_sensitive_context(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.WARNING, logger="providers.mag.connection")
    conn = MAGConnection("https://portal.example.test/c/", max_retries=1)
    conn._session = _Session(_PartialPayloadErrorResponse(b"partial"))

    with pytest.raises(NetworkError, match="failed after 1 attempts"):
        await conn.get("/portal.php", diagnostic_stage="CATALOGUE")

    messages = " ".join(record.getMessage() for record in caplog.records)
    assert "STAGE=CATALOGUE_BODY_INCOMPLETE" in messages
    assert "ERROR=PAYLOAD_ERROR" in messages
    assert "RECEIVED_BYTES=7" in messages
    assert "partial" not in messages
    assert "portal.example.test" not in messages


@pytest.mark.asyncio
async def test_catalogue_pre_response_network_error_logs_safe_aggregate_placeholders(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.WARNING, logger="providers.mag.connection")
    conn = MAGConnection("https://portal.example.test/c/", max_retries=1)
    conn._session = _NetworkErrorSession()

    with pytest.raises(NetworkError, match="failed after 1 attempts"):
        await conn.get("/portal.php", diagnostic_stage="CATALOGUE")

    messages = " ".join(record.getMessage() for record in caplog.records)
    assert "STAGE=CATALOGUE_BODY_INCOMPLETE" in messages
    assert "ERROR=NETWORK_ERROR" in messages
    assert "HTTP_STATUS=<none>" in messages
    assert "RECEIVED_BYTES=0" in messages
    assert "portal.example.test" not in messages


@pytest.mark.asyncio
async def test_post_timeout_is_not_retried() -> None:
    conn = MAGConnection("https://portal.example.test/c/", max_retries=3)
    session = _Session(_TimedOutResponse())
    conn._session = session

    with patch("providers.mag.connection.asyncio.sleep", new=AsyncMock()) as sleep:
        with pytest.raises(NetworkError, match="failed after 1 attempts"):
            await conn.post("/portal.php", data={"action": "do_auth"})

    assert session.request_count == 1
    sleep.assert_not_awaited()


@pytest.mark.asyncio
async def test_catalogue_timeout_retries_the_configured_request_count() -> None:
    conn = MAGConnection("https://portal.example.test/c/", max_retries=3)
    session = _Session(_TimedOutResponse())
    conn._session = session

    with patch("providers.mag.connection.asyncio.sleep", new=AsyncMock()):
        with pytest.raises(NetworkError, match="failed after 3 attempts"):
            await conn.get("/portal.php", diagnostic_stage="CATALOGUE")

    assert session.request_count == 3


@pytest.mark.asyncio
async def test_catalogue_chunked_body_completes_after_multiple_progressing_chunks(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="providers.mag.connection")
    response = _Response(b'{"js":{"data":[]}}', transfer_encoding="chunked")
    response.content = _BodyContent([b'{"js":', b'{"data":[]}}'])
    conn = MAGConnection("https://portal.example.test/c/")
    conn._session = _Session(response)

    result = await conn.get("/portal.php", diagnostic_stage="CATALOGUE")

    assert result == {"js": {"data": []}}
    messages = " ".join(record.getMessage() for record in caplog.records)
    assert "STAGE=CATALOGUE_BODY_COMPLETE" in messages
    assert "ATTEMPT=1/3" in messages
    assert "TOTAL_TIMEOUT=30s" in messages
    assert "CHUNKS=2" in messages
    assert "FIRST_BODY_BYTE=" in messages
    assert "LAST_BODY_BYTE=" in messages


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


@pytest.mark.parametrize(
    ("base", "path", "expected"),
    [
        (
            "https://host/",
            "/server/load.php",
            "https://host/server/load.php",
        ),
        (
            "https://host/c/",
            "/server/load.php",
            "https://host/c/server/load.php",
        ),
        (
            "https://host/c",
            "/server/load.php",
            "https://host/c/server/load.php",
        ),
        (
            "https://host/stalker_portal/",
            "server/load.php",
            "https://host/stalker_portal/server/load.php",
        ),
        (
            "https://host/portal.php",
            "portal.php",
            "https://host/portal.php",
        ),
    ],
)
def test_sanitise_url_fixed_base_variants(base: str, path: str, expected: str) -> None:
    assert _sanitise_url(base, path) == expected
