"""Deterministic MAG/Stalker protocol compatibility lab.

The fixture is a protocol server, not a hardware emulator.  Every scenario is
exercised through the real MAG provider, HTTP connection, session parser,
legacy catalogue/stream layers, and application adapter boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest
from aiohttp import web
from providers.mag.provider import MAGProvider

from samotech_iptv.application.dtos import LoadCategoriesRequest
from samotech_iptv.application.use_cases.load_categories import LoadCategories
from samotech_iptv.core.exceptions import SamotechError
from samotech_iptv.domain.value_objects.channel_id import ChannelId
from samotech_iptv.domain.value_objects.credential import Credential
from samotech_iptv.infrastructure.providers.mag_adapter import MagProviderAdapter
from samotech_iptv.infrastructure.providers.provider_context import ProviderContext
from samotech_iptv.infrastructure.providers.provider_metadata import InfraProviderMetadata


@dataclass
class PortalState:
    scenario: str
    auth_count: int = 0
    channel_count: int = 0
    requests: list[dict[str, Any]] = field(default_factory=list)


SCENARIOS = (
    "legacy_success",
    "stalker_query_success",
    "empty",
    "malformed",
    "unauthorized",
    "forbidden",
    "not_found",
    "missing_token",
    "token_ttl",
    "expired_then_reauth",
    "successful_reauthentication",
    "unsupported_categories",
    "successful_categories",
    "successful_channels",
    "stream_resolution",
)


@pytest.fixture
async def local_mag_portal() -> tuple[str, PortalState]:
    state = PortalState("legacy_success")
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
        if request.path != "/server/load.php":
            return web.Response(status=404, text="not found")
        query = request.query
        is_handshake = query.get("action") == "handshake" or not query
        if is_handshake:
            state.auth_count += 1
            if state.scenario == "empty":
                return web.Response(status=200, body=b"", content_type="text/javascript")
            if state.scenario == "malformed":
                return web.Response(status=200, body=b"not-json", content_type="text/javascript")
            if state.scenario == "unauthorized":
                return web.Response(status=401, body=b"unauthorized", content_type="text/plain")
            if state.scenario == "forbidden":
                return web.Response(status=403, body=b"forbidden", content_type="text/plain")
            if state.scenario == "not_found":
                return web.Response(status=404, body=b"not found", content_type="text/plain")
            if state.scenario == "missing_token":
                return web.json_response({"js": {}})
            payload: dict[str, object] = {"js": {"token": f"fixture-token-{state.auth_count}"}}
            if state.scenario == "token_ttl":
                payload["js"] = {"token": "fixture-token", "token_TTL": "60"}
            return web.json_response(payload)

        if query.get("action") == "get_all_channels":
            state.channel_count += 1
            if (
                state.scenario in {"expired_then_reauth", "successful_reauthentication"}
                and state.channel_count == 1
            ):
                return web.json_response({"js": {"error": "fixture session expired"}})
            return web.json_response(
                {"js": {"data": [{"id": "1", "name": "Fixture News", "stream_id": "1"}]}}
            )
        if query.get("action") == "create_link":
            return web.json_response({"js": {"cmd": "ffmpeg http://127.0.0.1/fixture.ts"}})
        if query.get("action") == "get_genres":
            return web.json_response({"js": {"data": [{"id": "1", "title": "Fixture"}]}})
        return web.json_response({"js": {"data": []}})

    app.router.add_get("/server/load.php", handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]  # type: ignore[union-attr]
    try:
        yield f"http://127.0.0.1:{port}", state
    finally:
        await runner.cleanup()


def _build_adapter(base_url: str, scenario: str) -> tuple[MagProviderAdapter, ProviderContext]:
    context = ProviderContext.build(
        overrides={"connect_timeout": 1.0, "read_timeout": 1.0, "max_retries": 1}
    )
    profile = "stalker_query" if scenario == "stalker_query_success" else "legacy"
    provider = MAGProvider(
        config={
            "portal_url": base_url,
            "mac_address": "00:11:22:33:44:55",
            "protocol_profile": profile,
            "timeout_s": 2.0,
            "max_retries": 1,
            "use_keyring": False,
        }
    )
    metadata = InfraProviderMetadata(
        provider_id=f"fixture-{scenario}", provider_type="mag", base_url=base_url
    )
    return MagProviderAdapter(metadata, context, legacy_provider=provider), context


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("scenario", "expected_success"),
    [
        ("legacy_success", True),
        ("stalker_query_success", True),
        ("token_ttl", True),
        ("empty", False),
        ("malformed", False),
        ("unauthorized", False),
        ("forbidden", False),
        ("not_found", False),
        ("missing_token", False),
    ],
)
async def test_authentication_profiles_through_real_application_boundary(
    local_mag_portal: tuple[str, PortalState], scenario: str, expected_success: bool
) -> None:
    base_url, state = local_mag_portal
    state.scenario = scenario
    adapter, _context = _build_adapter(base_url, scenario)
    try:
        if expected_success:
            assert await adapter.authenticate(Credential("fixture-mac", "fixture-password")) is True
            assert adapter.is_authenticated is True
            assert state.auth_count == 1
            request = state.requests[0]
            if scenario == "stalker_query_success":
                assert request["query"] == {
                    "type": "stb",
                    "action": "handshake",
                    "token": "",
                    "JsHttpRequest": "1-xml",
                }
            else:
                assert request["query"] == {}
        else:
            with pytest.raises(SamotechError):
                await adapter.authenticate(Credential("fixture-mac", "fixture-password"))
            assert adapter.is_authenticated is False
    finally:
        await adapter.close_session()


@pytest.mark.asyncio
async def test_live_channels_stream_and_unsupported_categories_use_real_protocol_stack(
    local_mag_portal: tuple[str, PortalState],
) -> None:
    base_url, state = local_mag_portal
    state.scenario = "successful_channels"
    adapter, _context = _build_adapter(base_url, state.scenario)
    try:
        assert await adapter.authenticate(Credential("fixture-mac", "fixture-password")) is True
        channels = await adapter.load_channels()
        assert [channel.name for channel in channels] == ["Fixture News"]
        stream = await adapter.resolve_stream(ChannelId("1"))
        assert str(stream).startswith("http://127.0.0.1/")

        class Resolver:
            def resolve_category_provider(self, _provider_id: object) -> MagProviderAdapter:
                return adapter

        categories = await LoadCategories(Resolver()).execute(
            LoadCategoriesRequest(provider_id=adapter.provider_id.value)
        )
        assert categories.unsupported is True
        assert state.auth_count == 1
    finally:
        await adapter.close_session()


@pytest.mark.asyncio
async def test_expired_session_performs_one_controlled_reauthentication(
    local_mag_portal: tuple[str, PortalState],
) -> None:
    base_url, state = local_mag_portal
    state.scenario = "expired_then_reauth"
    adapter, _context = _build_adapter(base_url, state.scenario)
    try:
        assert await adapter.authenticate(Credential("fixture-mac", "fixture-password")) is True
        channels = await adapter.load_channels()
        assert len(channels) == 1
        assert state.auth_count == 2
        assert adapter.session_state == "authenticated"
    finally:
        await adapter.close_session()


def test_fixture_scenarios_are_explicit_and_complete() -> None:
    assert len(SCENARIOS) == 15
    assert {"unsupported_categories", "successful_categories"} <= set(SCENARIOS)
