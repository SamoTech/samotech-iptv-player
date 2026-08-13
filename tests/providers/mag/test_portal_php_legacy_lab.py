from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest
from aiohttp import web
from providers.mag.catalogue import MAGCatalogue
from providers.mag.errors import ProviderError
from providers.mag.provider import MAGProvider

from samotech_iptv.domain.value_objects.channel_id import ChannelId
from samotech_iptv.domain.value_objects.credential import Credential
from samotech_iptv.infrastructure.providers.mag_adapter import MagProviderAdapter
from samotech_iptv.infrastructure.providers.provider_context import ProviderContext
from samotech_iptv.infrastructure.providers.provider_metadata import InfraProviderMetadata


@dataclass
class PortalPhpLabState:
    requests: list[dict[str, Any]] = field(default_factory=list)


@pytest.fixture
async def portal_php_lab() -> tuple[str, PortalPhpLabState]:
    state = PortalPhpLabState()
    app = web.Application()

    async def handler(request: web.Request) -> web.StreamResponse:
        query = dict(request.query)
        action = query.get("action", "")
        authorization = request.headers.get("Authorization", "")
        state.requests.append(
            {
                "path": request.path,
                "query": query,
                "has_mac_authorization": authorization.startswith("MAC "),
                "has_bearer": authorization.startswith("Bearer "),
                "has_mac_cookie": "mac" in request.cookies,
                "user_agent": request.headers.get("User-Agent", ""),
                "referer": request.headers.get("Referer", ""),
                "accept": request.headers.get("Accept", ""),
                "x_requested_with": request.headers.get("X-Requested-With", ""),
            }
        )

        if request.path == "/portal.php" and action == "handshake":
            expected_query = {
                "action": "handshake",
                "type": "stb",
                "token": "",
                "JsHttpRequest": "1-xml",
            }
            if query != expected_query:
                return web.json_response({"error": "bad handshake"}, status=400)
            if not authorization.startswith("MAC ") or "mac" not in request.cookies:
                return web.json_response({"error": "missing mac authentication"}, status=401)
            return web.json_response({"js": {"token": "fixture-portal-token", "token_TTL": "120"}})

        authenticated = authorization.startswith("Bearer ") and "mac" in request.cookies
        if not authenticated:
            return web.json_response({"error": "session required"}, status=401)

        if request.path == "/portal.php" and action == "get_main_info":
            return web.json_response({"js": {"mac": "fixture-mac", "phone": "fixture-expiry"}})
        if request.path == "/server/load.php" and action == "get_genres":
            return web.json_response({"js": [{"id": "1", "title": "News"}]})
        if request.path == "/portal.php" and action == "get_all_channels":
            return web.json_response(
                {
                    "js": {
                        "data": [
                            {
                                "id": "1",
                                "name": "Channel A",
                                "logo": "-http://127.0.0.1/lab/a.png",
                                "tv_genre_id": "1",
                                "cmds": [{"url": "ffmpeg http://127.0.0.1/lab/a.ts"}],
                            },
                            {
                                "id": "2",
                                "name": "Channel B",
                                "logo": "http://127.0.0.1/lab/b.png",
                                "tv_genre_id": "1",
                                "cmds": [{"url": "http://127.0.0.1/lab/b.ts"}],
                            },
                            {"id": "3", "name": "Rejected Channel", "cmds": []},
                        ]
                    }
                }
            )
        return web.json_response({"error": "unsupported action"}, status=404)

    app.router.add_route("*", "/{tail:.*}", handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]  # type: ignore[union-attr]
    try:
        yield f"http://127.0.0.1:{port}/c/", state
    finally:
        await runner.cleanup()


@pytest.mark.asyncio
async def test_portal_php_legacy_contract_through_full_adapter_stack(
    portal_php_lab: tuple[str, PortalPhpLabState],
) -> None:
    base_url, state = portal_php_lab
    provider = MAGProvider(
        {
            "portal_url": base_url,
            "mac_address": "00:11:22:33:44:55",
            "protocol_profile": "stalker_portal_php_legacy",
            "timeout_s": 2.0,
            "max_retries": 1,
            "use_keyring": False,
        }
    )
    adapter = MagProviderAdapter(
        InfraProviderMetadata("portal-php-lab", "mag", base_url),
        ProviderContext.build(overrides={"connect_timeout": 1.0, "read_timeout": 1.0}),
        legacy_provider=provider,
    )

    try:
        assert await adapter.authenticate(Credential("lab-mac", "lab-password")) is True
        categories = await adapter.load_live_categories()
        channels = await adapter.load_channels()
        resolved = await adapter.resolve_stream(ChannelId("1"))
    finally:
        await adapter.close_session()

    assert [(category.id, category.name) for category in categories] == [("1", "News")]
    assert [(str(channel.id), channel.name) for channel in channels] == [
        ("1", "Channel A"),
        ("2", "Channel B"),
    ]
    assert str(channels[0].logo_url) == "http://127.0.0.1/lab/a.png"
    assert str(resolved) == "http://127.0.0.1/lab/a.ts"
    assert provider.live_catalogue_stats == {"received": 3, "accepted": 2, "rejected": 1}

    handshake = [
        request for request in state.requests if request["query"].get("action") == "handshake"
    ]
    account_info = [
        request for request in state.requests if request["query"].get("action") == "get_main_info"
    ]
    genres = [
        request for request in state.requests if request["query"].get("action") == "get_genres"
    ]
    channels_requests = [
        request
        for request in state.requests
        if request["query"].get("action") == "get_all_channels"
    ]
    assert len(handshake) == 1
    assert handshake[0]["path"] == "/portal.php"
    assert handshake[0]["has_mac_authorization"] is True
    assert handshake[0]["has_mac_cookie"] is True
    assert handshake[0]["referer"] == base_url
    assert handshake[0]["x_requested_with"] == "XMLHttpRequest"
    assert len(account_info) == 1
    assert account_info[0]["path"] == "/portal.php"
    assert account_info[0]["has_bearer"] is True
    assert len(genres) == 1
    assert genres[0]["path"] == "/server/load.php"
    assert genres[0]["has_bearer"] is True
    assert len(channels_requests) == 1
    assert channels_requests[0]["path"] == "/portal.php"
    assert all(request["query"].get("action") != "get_ordered_list" for request in state.requests)
    assert channels_requests[0]["has_bearer"] is True
    assert "fixture-portal-token" not in repr(state.requests)


def test_concrete_catalogue_parsers_reject_missing_or_invalid_response_shapes() -> None:
    with pytest.raises(ProviderError, match="missing js category data"):
        MAGCatalogue._records_from_js_list({})
    with pytest.raises(ProviderError, match="category data was not a list"):
        MAGCatalogue._records_from_js_list({"js": {}})
    with pytest.raises(ProviderError, match="missing js.data"):
        MAGCatalogue._records_from_direct_response({"js": {}})
    with pytest.raises(ProviderError, match="data was not a list"):
        MAGCatalogue._records_from_direct_response({"js": {"data": {}}})


def test_concrete_catalogue_parser_accepts_empty_channel_collection() -> None:
    assert MAGCatalogue._records_from_direct_response({"js": {"data": []}}) == []
