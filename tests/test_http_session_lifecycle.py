"""Regression tests for application-owned HTTP session lifecycle."""
from __future__ import annotations

import pytest
from aiohttp import web

from samotech_iptv.infrastructure.network.http_client import AsyncHttpClient
from samotech_iptv.infrastructure.network.http_session import HttpSession
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
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]  # type: ignore[union-attr]
    try:
        yield f"http://127.0.0.1:{port}"
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
