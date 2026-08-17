"""Regression tests for application-owned HTTP session lifecycle."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import web

from samotech_iptv.infrastructure.network.exceptions import HttpClientError, HttpServerError
from samotech_iptv.infrastructure.network.http_client import AsyncHttpClient
from samotech_iptv.infrastructure.network.http_session import HttpSession
from samotech_iptv.infrastructure.network.retry_policy import RetryPolicy
from samotech_iptv.infrastructure.providers.m3u_adapter import M3UProviderAdapter
from samotech_iptv.infrastructure.providers.provider_metadata import InfraProviderMetadata


@pytest.fixture
async def local_http_server() -> str:
    """Serve a deterministic M3U response from an ephemeral local port."""
    app = web.Application()
    app.router.add_get(
        "/playlist.m3u",
        lambda _: web.Response(
            text="#EXTM3U\n#EXTINF:-1,Local News\nhttps://stream.example.test/news\n",
            content_type="audio/x-mpegurl",
        ),
    )
    app.router.add_get("/artwork.jpg", lambda _: web.Response(body=b"image-bytes"))
    app.router.add_get("/large-text", lambda _: web.Response(text="x" * 64))
    app.router.add_get("/invalid-json", lambda _: web.Response(text="not-json"))
    app.router.add_get(
        "/client-error",
        lambda _: web.Response(
            status=401,
            text=(
                "username=SAMOSAFE_HTTP_USER password=SAMOSAFE_HTTP_PASSWORD "
                "token=SAMOSAFE_HTTP_TOKEN"
            ),
            content_type="application/json",
        ),
    )
    app.router.add_get(
        "/server-error",
        lambda _: web.Response(
            status=503,
            text="cookie=SAMOSAFE_HTTP_COOKIE authorization=SAMOSAFE_HTTP_AUTH",
            content_type="application/json",
        ),
    )
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]  # type: ignore[union-attr]
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        await runner.cleanup()


@pytest.fixture
async def post_retry_server() -> tuple[str, list[int]]:
    """Serve a deterministic failing POST endpoint and count attempts."""
    attempts = [0]
    app = web.Application()

    async def handler(_: web.Request) -> web.Response:
        attempts[0] += 1
        return web.Response(status=503, text="SAMOSAFE_POST_RESPONSE_BODY")

    app.router.add_post("/post-server-error", handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]  # type: ignore[union-attr]
    try:
        yield f"http://127.0.0.1:{port}", attempts
    finally:
        await runner.cleanup()


@pytest.mark.asyncio
async def test_http_session_requires_open_and_releases_on_close() -> None:
    session = HttpSession()

    assert session.is_open is False
    with pytest.raises(RuntimeError, match="HttpSession is not open"):
        _ = session.raw

    await session.open()
    assert session.is_open is True
    await session.close()
    assert session.is_open is False


@pytest.mark.asyncio
async def test_http_client_local_operation_requires_open_and_closes(
    local_http_server: str,
) -> None:
    client = AsyncHttpClient()

    with pytest.raises(RuntimeError, match="HttpSession is not open"):
        await client.get_text(f"{local_http_server}/playlist.m3u")

    await client.open()
    text = await client.get_text(f"{local_http_server}/playlist.m3u")
    assert "Local News" in text
    assert client._session.is_open is True  # type: ignore[union-attr]
    await client.close()
    assert client._session.is_open is False  # type: ignore[union-attr]


@pytest.mark.asyncio
async def test_http_client_get_text_and_json_enforce_safe_response_bounds(
    local_http_server: str,
) -> None:
    client = AsyncHttpClient(retry_policy=RetryPolicy.no_retry())
    await client.open()
    try:
        with pytest.raises(HttpClientError, match="size limit"):
            await client.get_text(f"{local_http_server}/large-text", max_bytes=4)
        with pytest.raises(HttpClientError, match="not valid JSON"):
            await client.get_json(f"{local_http_server}/invalid-json")
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_http_client_get_bytes_reuses_open_session_and_enforces_limit(
    local_http_server: str,
) -> None:
    client = AsyncHttpClient()
    await client.open()
    try:
        assert (
            await client.get_bytes(f"{local_http_server}/artwork.jpg", max_bytes=32)
            == b"image-bytes"
        )
        with pytest.raises(HttpClientError, match="size limit"):
            await client.get_bytes(f"{local_http_server}/artwork.jpg", max_bytes=4)
    finally:
        await client.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("path", "expected_status", "canaries"),
    [
        (
            "/client-error",
            401,
            ("SAMOSAFE_HTTP_USER", "SAMOSAFE_HTTP_PASSWORD", "SAMOSAFE_HTTP_TOKEN"),
        ),
        (
            "/server-error",
            503,
            ("SAMOSAFE_HTTP_COOKIE", "SAMOSAFE_HTTP_AUTH"),
        ),
    ],
)
async def test_http_error_excludes_response_body_and_query_credentials(
    local_http_server: str,
    path: str,
    expected_status: int,
    canaries: tuple[str, ...],
) -> None:
    client = AsyncHttpClient(retry_policy=RetryPolicy.no_retry())
    await client.open()
    try:
        with pytest.raises((HttpClientError, HttpServerError)) as caught:
            await client.get_json(
                f"{local_http_server}{path}?username=SAMOSAFE_QUERY_USER&token=SAMOSAFE_QUERY_TOKEN"
            )
    finally:
        await client.close()

    error = caught.value
    assert error.status_code == expected_status
    message = str(error)
    assert "SAMOSAFE_QUERY_USER" not in message
    assert "SAMOSAFE_QUERY_TOKEN" not in message
    for canary in canaries:
        assert canary not in message
    assert "?" not in message
    assert error.__cause__ is None


@pytest.mark.asyncio
async def test_http_client_does_not_retry_post_requests(
    post_retry_server: tuple[str, list[int]],
) -> None:
    server, attempts = post_retry_server
    client = AsyncHttpClient(
        retry_policy=RetryPolicy(max_attempts=3, base_delay=0.01, jitter=False)
    )
    await client.open()
    try:
        with patch(
            "samotech_iptv.infrastructure.network.retry_policy.RetryPolicy.sleep",
            new=AsyncMock(),
        ):
            with pytest.raises(HttpServerError, match="503"):
                await client.post_json(f"{server}/post-server-error", json={"operation": "login"})
    finally:
        await client.close()
    assert attempts == [1]


@pytest.mark.asyncio
async def test_m3u_adapter_loads_channels_through_shared_open_client(
    local_http_server: str,
) -> None:
    client = AsyncHttpClient()
    metadata = InfraProviderMetadata(
        provider_id="m3u-local",
        provider_type="m3u",
        base_url=f"{local_http_server}/playlist.m3u",
    )

    class Context:
        http_client = client

        class Credentials:
            async def retrieve(self, _provider_id: object) -> None:
                return None

        credential_store = Credentials()

    adapter = M3UProviderAdapter(metadata, Context())  # type: ignore[arg-type]
    await client.open()
    try:
        channels = await adapter.load_channels()
    finally:
        await client.close()

    assert [channel.name for channel in channels] == ["Local News"]
    assert client._session.is_open is False  # type: ignore[union-attr]
