"""Known-good local Stalker/Ministra protocol laboratory.

The fixture models the readable classic middleware contract discovered in the
open-source Stalker 5.1.1 tree: an origin-relative
``stalker_portal/server/load.php`` DataLoader dispatcher receiving ``type`` and
``action`` parameters.  It is a deterministic local reference server, not a
production portal or hardware emulator.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest
from aiohttp import web
from providers.mag.provider import MAGProvider

from samotech_iptv.domain.value_objects.channel_id import ChannelId
from samotech_iptv.domain.value_objects.credential import Credential
from samotech_iptv.infrastructure.providers.mag_adapter import MagProviderAdapter
from samotech_iptv.infrastructure.providers.provider_context import ProviderContext
from samotech_iptv.infrastructure.providers.provider_metadata import InfraProviderMetadata


@dataclass
class MiddlewareLabState:
    requests: list[dict[str, Any]] = field(default_factory=list)


@pytest.fixture
async def middleware_lab() -> tuple[str, MiddlewareLabState]:
    state = MiddlewareLabState()
    app = web.Application()

    async def handler(request: web.Request) -> web.StreamResponse:
        query = dict(request.query)
        action = query.get("action", "")
        state.requests.append(
            {
                "path": request.path,
                "query": query,
                "has_bearer": request.headers.get("Authorization", "").startswith("Bearer "),
                "has_token_cookie": "token" in request.cookies,
                "has_mac_cookie": "mac" in request.cookies,
                "user_agent": request.headers.get("User-Agent", ""),
                "x_user_agent": request.headers.get("X-User-Agent", ""),
                "referer": request.headers.get("Referer", ""),
            }
        )

        if request.path != "/stalker_portal/server/load.php":
            return web.Response(status=404, text="not found")

        if action == "handshake":
            if query != {
                "type": "stb",
                "action": "handshake",
                "token": "",
                "JsHttpRequest": "1-xml",
            }:
                return web.Response(status=400, text="bad handshake")
            return web.json_response({"js": {"token": "lab-token", "token_TTL": "120"}})

        authenticated = (
            request.headers.get("Authorization", "").startswith("Bearer ")
            and "token" in request.cookies
            and "mac" in request.cookies
        )
        if not authenticated:
            return web.Response(status=401, text="session required")

        if action == "get_profile":
            return web.json_response({"js": {"stb_type": "MAG250"}})
        if action == "get_main_info":
            return web.json_response({"js": {"status": "active"}})
        if action == "get_genres":
            return web.json_response({"js": [{"id": "1", "title": "News"}]})
        if action == "get_ordered_list":
            if query.get("genre") != "1" or query.get("JsHttpRequest") != "1-xml":
                return web.Response(status=400, text="bad ordered-list query")
            pages = {
                "1": [
                    {"id": "1", "name": "Channel A", "cmd": "ffmpeg http://127.0.0.1/lab/a.ts"},
                    {"id": "2", "name": "Channel B", "cmd": "ffmpeg http://127.0.0.1/lab/b.ts"},
                ],
                "2": [
                    {"id": "3", "name": "Channel C", "cmd": "ffmpeg http://127.0.0.1/lab/c.ts"},
                ],
            }
            page = query.get("p", "")
            return web.json_response({"js": {"total_items": "3", "data": pages.get(page, [])}})
        if action == "create_link":
            if query.get("type") != "itv" or query.get("JsHttpRequest") != "1-xml":
                return web.Response(status=400, text="bad create-link query")
            return web.json_response({"js": {"cmd": "ffmpeg http://127.0.0.1/lab/resolved.ts"}})
        return web.Response(status=404, text="unsupported action")

    app.router.add_get("/stalker_portal/server/load.php", handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]  # type: ignore[union-attr]
    try:
        yield f"http://127.0.0.1:{port}/", state
    finally:
        await runner.cleanup()


@pytest.mark.asyncio
async def test_samotech_authenticates_against_known_good_stalker_middleware_lab(
    middleware_lab: tuple[str, MiddlewareLabState],
) -> None:
    base_url, state = middleware_lab
    provider = MAGProvider(
        {
            "portal_url": base_url,
            "mac_address": "00:11:22:33:44:55",
            "protocol_profile": "stalker_helper_compatibility",
            "mag_model": "MAG250",
            "timeout_s": 2.0,
            "max_retries": 1,
            "use_keyring": False,
        }
    )
    adapter = MagProviderAdapter(
        InfraProviderMetadata("middleware-lab", "mag", base_url),
        ProviderContext.build(overrides={"connect_timeout": 1.0, "read_timeout": 1.0}),
        legacy_provider=provider,
    )

    try:
        assert await adapter.authenticate(Credential("lab-mac", "lab-password")) is True
        categories = await adapter.load_live_categories()
        channels = await adapter.load_channels()
        resolved = await adapter.resolve_stream(ChannelId("2"))
    finally:
        await adapter.close_session()

    assert [(category.id, category.name) for category in categories] == [("1", "News")]
    assert [(str(channel.id), channel.name) for channel in channels] == [
        ("1", "Channel A"),
        ("2", "Channel B"),
        ("3", "Channel C"),
    ]
    assert str(resolved) == "http://127.0.0.1/lab/resolved.ts"

    handshake = [
        request for request in state.requests if request["query"].get("action") == "handshake"
    ]
    ordered = [
        request
        for request in state.requests
        if request["query"].get("action") == "get_ordered_list"
    ]
    create_link = [
        request for request in state.requests if request["query"].get("action") == "create_link"
    ]
    assert len(handshake) == 1
    assert handshake[0]["path"] == "/stalker_portal/server/load.php"
    assert handshake[0]["has_bearer"] is False
    assert handshake[0]["has_token_cookie"] is False
    assert handshake[0]["has_mac_cookie"] is True
    assert handshake[0]["x_user_agent"] == "Model: MAG250; Link: WiFi"
    assert len(ordered) == 2
    assert [request["query"].get("p") for request in ordered] == ["1", "2"]
    assert len(create_link) == 1
    assert create_link[0]["has_bearer"] is True
    assert create_link[0]["has_token_cookie"] is True
    assert all(request["path"] == "/stalker_portal/server/load.php" for request in state.requests)
    assert "lab-token" not in repr(state.requests)
