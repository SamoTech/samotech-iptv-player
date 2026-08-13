"""Deterministic local tests for bounded MAG/Stalker endpoint discovery."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import pytest
from aiohttp import web
from providers.mag.connection import MAGConnection, MAGProbeResponse
from providers.mag.credentials import MAGCredentials
from providers.mag.discovery import (
    MAGDiscoveryClassification,
    MAGDiscoveryResult,
    MAGProtocolDiscovery,
)
from providers.mag.provider import MAGProvider

if TYPE_CHECKING:
    from providers.mag.protocol_profile import MAGProtocolProfile


@dataclass
class DiscoveryPortalState:
    mode: str = "all_valid"
    requests: list[dict[str, object]] = field(default_factory=list)
    configured_calls: int = 0


@pytest.fixture
async def discovery_portal() -> tuple[str, DiscoveryPortalState]:
    state = DiscoveryPortalState()
    app = web.Application()

    async def handler(request: web.Request) -> web.StreamResponse:
        state.requests.append(
            {
                "path": request.path,
                "query": dict(request.query),
                "has_mac_header": "X-User-Mac" in request.headers,
                "has_authorization": "Authorization" in request.headers,
            }
        )
        if request.path == "/c/server/load.php":
            state.configured_calls += 1
            if request.query.get("action") == "get_all_channels":
                return web.json_response(
                    {"js": {"data": [{"id": "1", "name": "Fixture News", "stream_id": "1"}]}}
                )
            if state.mode == "prehash":
                if request.query.get("prehash") == "false":
                    return web.json_response({"js": {"token": "fixture-token"}})
                return web.json_response({"js": {}})
            if state.mode == "classifications":
                return web.Response(status=404, text="not found", content_type="text/plain")
            return web.json_response({"js": {"token": "fixture-token"}})
        if request.path == "/stalker_portal/server/load.php":
            if state.mode == "classifications":
                return web.Response(status=401, text="unauthorized", content_type="text/plain")
            return web.json_response({"js": {"token": "fixture-token"}})
        if request.path == "/stb/server/load.php":
            if state.mode == "classifications":
                return web.Response(status=200, body=b"", content_type="text/javascript")
            return web.json_response({"js": {"token": "fixture-token"}})
        if request.path == "/portal.php":
            if state.mode == "classifications":
                return web.Response(status=200, body=b"not-json", content_type="text/javascript")
            return web.json_response({"js": {"token": "fixture-token"}})
        return web.Response(status=404, text="not found")

    for path in (
        "/c/server/load.php",
        "/stalker_portal/server/load.php",
        "/stb/server/load.php",
        "/portal.php",
    ):
        app.router.add_get(path, handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]  # type: ignore[union-attr]
    try:
        yield f"http://127.0.0.1:{port}/c/", state
    finally:
        await runner.cleanup()


async def _discover(
    base_url: str,
) -> tuple[tuple[MAGDiscoveryResult, ...], MAGProtocolProfile | None]:
    connection = MAGConnection(base_url, timeout_s=2.0, max_retries=1)
    credentials = MAGCredentials(portal_url=base_url, mac_address="00:11:22:33:44:55")
    await connection.open()
    try:
        return await MAGProtocolDiscovery(connection, credentials).discover()
    finally:
        await connection.close()


@pytest.mark.asyncio
async def test_discovery_probes_only_fixed_candidates_and_uses_deterministic_priority(
    discovery_portal: tuple[str, DiscoveryPortalState],
) -> None:
    base_url, state = discovery_portal

    results, profile = await _discover(base_url)

    assert [result.candidate_name for result in results] == [
        "configured_base_server",
        "origin_stalker_portal",
        "origin_stb_server",
        "origin_portal_php",
    ]
    assert all(
        result.classification is MAGDiscoveryClassification.VALID_STALKER_HANDSHAKE
        for result in results
    )
    assert profile is not None
    assert profile.name == "discovered_configured_base"
    assert [request["path"] for request in state.requests] == [
        "/c/server/load.php",
        "/stalker_portal/server/load.php",
        "/stb/server/load.php",
        "/portal.php",
    ]
    assert all(request["has_mac_header"] is True for request in state.requests)
    assert all(request["has_authorization"] is False for request in state.requests)
    assert all(
        request["query"]
        == {"type": "stb", "action": "handshake", "token": "", "JsHttpRequest": "1-xml"}
        for request in state.requests
    )
    assert "00:11:22:33:44:55" not in repr(results)
    assert "fixture-token" not in repr(results)


@pytest.mark.asyncio
async def test_auto_profile_reuses_discovered_endpoint_for_authenticated_channels(
    discovery_portal: tuple[str, DiscoveryPortalState],
) -> None:
    base_url, state = discovery_portal
    provider = MAGProvider(
        {
            "portal_url": base_url,
            "mac_address": "00:11:22:33:44:55",
            "protocol_profile": "auto",
            "timeout_s": 2.0,
            "max_retries": 1,
            "use_keyring": False,
        }
    )
    try:
        await provider.connect()
        assert provider._session.profile.name == "discovered_configured_base"
        channels = await provider.get_channels()
        assert channels == [{"id": "1", "name": "Fixture News", "stream_id": "1"}]
        assert state.requests[-1]["path"] == "/c/server/load.php"
        assert state.requests[-1]["query"]["action"] == "get_all_channels"  # type: ignore[index]
    finally:
        await provider.close()


@pytest.mark.asyncio
async def test_discovery_uses_prehash_only_after_json_missing_token(
    discovery_portal: tuple[str, DiscoveryPortalState],
) -> None:
    base_url, state = discovery_portal
    state.mode = "prehash"

    results, profile = await _discover(base_url)

    configured = [result for result in results if result.candidate_name == "configured_base_server"]
    assert [result.classification for result in configured] == [
        MAGDiscoveryClassification.JSON_WITHOUT_TOKEN,
        MAGDiscoveryClassification.VALID_STALKER_HANDSHAKE,
    ]
    assert [result.used_prehash for result in configured] == [False, True]
    assert profile is not None
    assert profile.name == "discovered_configured_base"
    assert state.requests[1]["path"] == "/c/server/load.php"
    assert state.requests[1]["query"]["prehash"] == "false"  # type: ignore[index]


@pytest.mark.asyncio
async def test_discovery_classifies_http_empty_and_malformed_boundaries(
    discovery_portal: tuple[str, DiscoveryPortalState],
) -> None:
    base_url, state = discovery_portal
    state.mode = "classifications"

    results, profile = await _discover(base_url)

    assert profile is None
    assert [result.classification for result in results] == [
        MAGDiscoveryClassification.HTTP_404,
        MAGDiscoveryClassification.HTTP_401,
        MAGDiscoveryClassification.EMPTY_RESPONSE,
        MAGDiscoveryClassification.MALFORMED_JSON,
    ]
    assert all(result.token_present is False for result in results)


@pytest.mark.parametrize(
    ("response", "expected"),
    [
        (
            MAGProbeResponse(403, "text/plain", 9, 0.01, payload=None),
            MAGDiscoveryClassification.HTTP_403,
        ),
        (
            MAGProbeResponse(500, "text/plain", 9, 0.01, payload=None),
            MAGDiscoveryClassification.HTTP_OTHER,
        ),
        (
            MAGProbeResponse(200, "application/json", 2, 0.01, payload=[]),
            MAGDiscoveryClassification.UNKNOWN_PROTOCOL,
        ),
        (
            MAGProbeResponse(200, "application/json", 10, 0.01, payload={"js": {}}),
            MAGDiscoveryClassification.JSON_WITHOUT_TOKEN,
        ),
    ],
)
def test_discovery_classifies_remaining_safe_probe_outcomes(
    response: MAGProbeResponse, expected: MAGDiscoveryClassification
) -> None:
    result = MAGProtocolDiscovery._classify("fixture", response, prehash=False)
    assert result.classification is expected
    assert result.token_present is False
