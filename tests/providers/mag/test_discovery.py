"""Deterministic local tests for bounded MAG/Stalker endpoint discovery."""

from __future__ import annotations

import gc
import warnings
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
from providers.mag.protocol_profile import (
    StalkerClientCompatibilityProfile,
    StalkerHelperCompatibilityProfile,
)
from providers.mag.provider import MAGProvider

from samotech_iptv.core.exceptions import AuthenticationError
from samotech_iptv.domain.value_objects.credential import Credential
from samotech_iptv.infrastructure.providers.mag_adapter import MagProviderAdapter
from samotech_iptv.infrastructure.providers.provider_context import ProviderContext
from samotech_iptv.infrastructure.providers.provider_metadata import InfraProviderMetadata

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
                "has_cookie": "Cookie" in request.headers,
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
        "origin_stalker_portal_helper",
        "origin_stb_server",
        "origin_portal_php",
        "origin_portal_php_stalker_client",
        "origin_portal_php_mac_client",
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
        "/stalker_portal/server/load.php",
        "/stb/server/load.php",
        "/portal.php",
        "/portal.php",
        "/portal.php",
    ]
    assert all(state.requests[index]["has_mac_header"] is True for index in (0, 1, 3, 4))
    assert all(state.requests[index]["has_mac_header"] is False for index in (2, 5, 6))
    assert all(state.requests[index]["has_cookie"] is True for index in (2, 5, 6))
    assert all(state.requests[index]["has_authorization"] is False for index in range(6))
    assert state.requests[6]["has_authorization"] is True
    assert all(
        state.requests[index]["query"]
        == {"type": "stb", "action": "handshake", "token": "", "JsHttpRequest": "1-xml"}
        for index in (0, 1, 2, 3, 4)
    )
    assert state.requests[5]["query"] == {
        "type": "stb",
        "action": "handshake",
        "JsHttpRequest": "1-xml",
    }
    assert state.requests[6]["query"] == {
        "action": "handshake",
        "type": "stb",
        "token": "",
        "JsHttpRequest": "1-xml",
    }
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
        session = provider._connection._session
        assert session is not None
        assert session.closed is False
        assert provider._session.profile.name == "discovered_configured_base"
        channels = await provider.get_channels()
        assert channels == [{"id": "1", "name": "Fixture News", "stream_id": "1"}]
        assert state.requests[-1]["path"] == "/c/server/load.php"
        assert state.requests[-1]["query"]["action"] == "get_all_channels"  # type: ignore[index]
        assert provider._connection._session is session
        assert session.closed is False
    finally:
        await provider.close()
    assert session.closed is True


@pytest.mark.asyncio
async def test_discovery_failure_closes_owned_connection_without_resource_warning(
    discovery_portal: tuple[str, DiscoveryPortalState],
) -> None:
    base_url, state = discovery_portal
    state.mode = "classifications"
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
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", ResourceWarning)
        with pytest.raises(Exception, match="did not establish a valid handshake"):
            await provider.connect()
        session = provider._connection._session
        assert session is not None
        assert session.closed is True
        gc.collect()
    assert not [warning for warning in caught if issubclass(warning.category, ResourceWarning)]


@pytest.mark.asyncio
async def test_adapter_repeated_discovery_failures_close_every_owned_connection(
    discovery_portal: tuple[str, DiscoveryPortalState],
) -> None:
    base_url, state = discovery_portal
    state.mode = "classifications"
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
    adapter = MagProviderAdapter(
        InfraProviderMetadata("fixture-mag", "mag", base_url),
        ProviderContext.build(overrides={"connect_timeout": 1.0, "read_timeout": 1.0}),
        legacy_provider=provider,
    )
    closed_sessions = []
    try:
        for _ in range(3):
            with pytest.raises(AuthenticationError):
                await adapter.authenticate(Credential("00:11:22:33:44:55", "fixture"))
            session = provider._connection._session
            assert session is not None
            assert session.closed is True
            closed_sessions.append(session)
        assert len({id(session) for session in closed_sessions}) == 3
        assert all(session.closed for session in closed_sessions)
    finally:
        await adapter.close_session()


@pytest.mark.asyncio
async def test_provider_close_releases_successful_session(
    discovery_portal: tuple[str, DiscoveryPortalState],
) -> None:
    base_url, _state = discovery_portal
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
    await provider.connect()
    session = provider._connection._session
    assert session is not None
    assert session.closed is False
    await provider.close()
    assert session.closed is True


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
        MAGDiscoveryClassification.HTTP_401,
        MAGDiscoveryClassification.EMPTY_RESPONSE,
        MAGDiscoveryClassification.MALFORMED_JSON,
        MAGDiscoveryClassification.MALFORMED_JSON,
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


def test_gui_and_helper_profiles_preserve_observed_mac_cookie_encodings() -> None:
    identity = {
        "portal_url": "http://fixture.test/c/",
        "mac_address": "00:11:22:33:44:55",
        "serial_number": "",
        "device_id": "",
        "device_id2": "",
        "token": "",
    }

    gui_headers = StalkerClientCompatibilityProfile().request_headers(**identity)
    helper_headers = StalkerHelperCompatibilityProfile().request_headers(**identity)
    helper_model_headers = StalkerHelperCompatibilityProfile().request_headers(
        **identity, mag_model="MAG250"
    )

    assert "mac=00:11:22:33:44:55" in gui_headers["Cookie"]
    assert "%3A" not in gui_headers["Cookie"]
    assert "mac=00%3A11%3A22%3A33%3A44%3A55" in helper_headers["Cookie"]
    assert "X-User-Agent" not in helper_headers
    assert helper_model_headers["X-User-Agent"] == "Model: MAG250; Link: WiFi"


@dataclass
class StalkerClientPortalState:
    mode: str = "gui"
    requests: list[dict[str, object]] = field(default_factory=list)


@pytest.fixture
async def stalker_client_portal() -> tuple[str, StalkerClientPortalState]:
    state = StalkerClientPortalState()
    app = web.Application()

    async def handler(request: web.Request) -> web.StreamResponse:
        query = dict(request.query)
        is_client_fingerprint = (
            request.headers.get("User-Agent") == "Mozilla/5.0 (QtEmbedded; U; Linux; C) "
            "AppleWebKit/533.3 (KHTML, like Gecko) "
            "MAG200 stbapp ver: 2 rev: 250 Safari/533.3"
            and "X-User-Agent" not in request.headers
            and "Referer" not in request.headers
            and "mac=00:11:22:33:44:55" in request.headers.get("Cookie", "")
            and "%3A" not in request.headers.get("Cookie", "")
        )
        is_helper_fingerprint = (
            request.headers.get("User-Agent") == "Mozilla/5.0 (QtEmbedded; U; Linux; C) "
            "AppleWebKit/533.3 (KHTML, like Gecko) "
            "MAG200 stbapp ver: 2 rev: 250 Safari/533.3"
            and request.headers.get("X-User-Agent") == "Model: MAG250; Link: WiFi"
            and request.headers.get("Referer")
            == f"http://{request.host}/stalker_portal/c/index.html"
            and "mac=00%3A11%3A22%3A33%3A44%3A55" in request.headers.get("Cookie", "")
            and request.headers.get("Accept") == "*/*"
            and request.headers.get("Accept-Language") == "en-US,en;q=0.5"
            and request.headers.get("Pragma") == "no-cache"
            and request.headers.get("Connection") == "Close"
            and request.headers.get("Accept-Encoding") == "gzip, deflate"
        )
        expected_path = (
            "/stalker_portal/server/load.php" if state.mode == "helper" else "/portal.php"
        )
        expected_fingerprint = (
            is_helper_fingerprint if state.mode == "helper" else is_client_fingerprint
        )
        state.requests.append(
            {
                "path": request.path,
                "query": query,
                "client_fingerprint": is_client_fingerprint,
                "helper_fingerprint": is_helper_fingerprint,
                "has_authorization": "Authorization" in request.headers,
                "has_cookie": "Cookie" in request.headers,
            }
        )
        if request.path != expected_path:
            return web.Response(status=404, text="not found")
        if query.get("action") == "handshake":
            if expected_fingerprint:
                return web.json_response({"js": {"token": "fixture-token", "token_TTL": "120"}})
            return web.Response(status=404, text="not found")
        if not expected_fingerprint or "Authorization" not in request.headers:
            return web.Response(status=401, text="missing session")
        if query.get("action") == "get_genres":
            return web.json_response({"js": [{"id": "10", "title": "Fixture Live"}]})
        if query.get("action") == "get_ordered_list":
            assert query == {
                "type": "itv",
                "action": "get_ordered_list",
                "JsHttpRequest": "1-xml",
                "genre": "10",
                "p": "1" if state.mode == "helper" else "0",
            }
            return web.json_response(
                {
                    "js": {
                        "total_items": "1",
                        "data": [
                            {
                                "id": "1",
                                "name": "Fixture News",
                                "stream_id": "1",
                                "cmd": "ffmpeg http://localhost/ch/1_",
                            }
                        ],
                    }
                }
            )
        if query.get("action") == "create_link":
            assert query["cmd"] == "ffmpeg http://localhost/ch/1_"
            return web.json_response({"js": {"cmd": "ffmpeg https://stream.example/live"}})
        return web.Response(status=404, text="unexpected request")

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


@pytest.mark.asyncio
async def test_stalker_client_profile_runs_adapter_fixture_flow_with_safe_fingerprint(
    stalker_client_portal: tuple[str, StalkerClientPortalState],
) -> None:
    base_url, state = stalker_client_portal
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
    adapter = MagProviderAdapter(
        InfraProviderMetadata("fixture-stalker-client", "mag", base_url),
        ProviderContext.build(overrides={"connect_timeout": 1.0, "read_timeout": 1.0}),
        legacy_provider=provider,
    )
    try:
        assert await adapter.authenticate(Credential("00:11:22:33:44:55", "fixture"))
        assert provider._session.profile.name == "stalker_gui_compatibility"
        categories = await adapter.load_live_categories()
        channels = await adapter.load_channels()
        resolved = await adapter.resolve_stream(channels[0].id)
    finally:
        await adapter.close_session()

    assert [(category.id, category.name) for category in categories] == [("10", "Fixture Live")]
    assert [(str(channel.id), channel.name) for channel in channels] == [("1", "Fixture News")]
    assert str(resolved).startswith("https://")
    assert provider.live_catalogue_stats == {"received": 1, "accepted": 1, "rejected": 0}
    client_handshakes = [
        request
        for request in state.requests
        if request["path"] == "/portal.php"
        and request["query"].get("action") == "handshake"  # type: ignore[index]
        and request["client_fingerprint"] is True
    ]
    assert len(client_handshakes) == 2
    assert all(request["has_authorization"] is False for request in client_handshakes)
    assert all(request["has_cookie"] is True for request in client_handshakes)
    assert not any(
        request["query"].get("prehash") for request in client_handshakes  # type: ignore[index]
    )
    assert "00:11:22:33:44:55" not in repr(state.requests)
    assert "fixture-token" not in repr(state.requests)


@pytest.mark.asyncio
async def test_stalker_helper_profile_runs_adapter_fixture_flow_from_page_one(
    stalker_client_portal: tuple[str, StalkerClientPortalState],
) -> None:
    base_url, state = stalker_client_portal
    state.mode = "helper"
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
        InfraProviderMetadata("fixture-stalker-helper", "mag", base_url),
        ProviderContext.build(overrides={"connect_timeout": 1.0, "read_timeout": 1.0}),
        legacy_provider=provider,
    )
    try:
        assert await adapter.authenticate(Credential("00:11:22:33:44:55", "fixture"))
        assert provider._session.profile.name == "stalker_helper_compatibility"
        categories = await adapter.load_live_categories()
        channels = await adapter.load_channels()
        resolved = await adapter.resolve_stream(channels[0].id)
    finally:
        await adapter.close_session()

    assert [(category.id, category.name) for category in categories] == [("10", "Fixture Live")]
    assert [(str(channel.id), channel.name) for channel in channels] == [("1", "Fixture News")]
    assert str(resolved).startswith("https://")
    helper_handshakes = [
        request
        for request in state.requests
        if request["path"] == "/stalker_portal/server/load.php"
        and request["query"].get("action") == "handshake"  # type: ignore[index]
        and request["helper_fingerprint"] is True
    ]
    ordered_list_requests = [
        request
        for request in state.requests
        if request["query"].get("action") == "get_ordered_list"  # type: ignore[index]
    ]
    assert len(helper_handshakes) == 1
    assert helper_handshakes[0]["query"] == {
        "type": "stb",
        "action": "handshake",
        "token": "",
        "JsHttpRequest": "1-xml",
    }
    assert len(ordered_list_requests) == 1
    assert ordered_list_requests[0]["query"].get("p") == "1"  # type: ignore[index]
    assert not any(
        request["query"].get("prehash") for request in helper_handshakes  # type: ignore[index]
    )
    assert "00:11:22:33:44:55" not in repr(state.requests)
    assert "fixture-token" not in repr(state.requests)
