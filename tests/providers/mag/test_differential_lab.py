from __future__ import annotations

from dataclasses import dataclass, field

import pytest
from aiohttp import web
from providers.mag.credentials import MAGCredentials
from providers.mag.discovery import (
    MAGDifferentialCase,
    MAGDiscoveryClassification,
    MAGProtocolDiscovery,
)
from providers.mag.protocol_profile import (
    StalkerClientCompatibilityProfile,
    StalkerHelperCompatibilityProfile,
)


@dataclass
class DifferentialState:
    requests: list[dict[str, object]] = field(default_factory=list)


@pytest.fixture
async def differential_portal() -> tuple[str, DifferentialState]:
    state = DifferentialState()
    app = web.Application()

    async def handler(request: web.Request) -> web.StreamResponse:
        state.requests.append(
            {
                "method": request.method,
                "path": request.path,
                "query": dict(request.query),
                "content_type": request.headers.get("Content-Type", ""),
                "has_cookie": bool(request.headers.get("Cookie")),
            }
        )
        if request.path == "/portal.php" and request.method == "GET":
            return web.Response(status=200, content_type="text/javascript", body=b"")
        if request.path == "/portal.php" and request.method == "POST":
            return web.Response(status=405, headers={"Allow": "GET"})
        if request.path == "/stalker_portal/server/load.php":
            if request.method == "GET" and request.query.get("prehash") == "false":
                return web.json_response({"js": {"token": "fixture-token"}})
            if request.method == "GET" and request.query.get("prehash") == "0":
                return web.json_response({"js": {"error": "unauthorized"}})
            if request.method == "POST":
                return web.Response(status=405, headers={"Allow": "GET"})
        return web.Response(status=404)

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
async def test_fixed_differential_matrix_retains_safe_metadata_only(
    differential_portal: tuple[str, DifferentialState],
) -> None:
    base_url, state = differential_portal
    credentials = MAGCredentials(portal_url=base_url, mac_address="00:11:22:33:44:55")
    connection = __import__("providers.mag.connection", fromlist=["MAGConnection"]).MAGConnection(
        base_url, timeout_s=2.0, max_retries=1
    )
    await connection.open()
    try:
        discovery = MAGProtocolDiscovery(connection, credentials)
        gui = StalkerClientCompatibilityProfile()
        helper = StalkerHelperCompatibilityProfile()
        cases = (
            MAGDifferentialCase(
                "T01",
                gui,
                "portal.php",
                "GET",
                header_fingerprint="gui",
                cookie_policy="raw-mac",
                expected_evidence="GUI handshake source",
            ),
            MAGDifferentialCase(
                "T02",
                gui,
                "portal.php",
                "POST",
                form=gui.handshake_params,
                header_fingerprint="gui",
                cookie_policy="raw-mac",
                expected_evidence="POST form experiment supported by current stalkerhek",
            ),
            MAGDifferentialCase(
                "T03",
                helper,
                "stalker_portal/server/load.php",
                "GET",
                params={"token": "", "prehash": "false"},
                header_fingerprint="helper",
                cookie_policy="encoded-mac",
                expected_evidence="current stalkerhek handshake",
            ),
            MAGDifferentialCase(
                "T04",
                helper,
                "stalker_portal/server/load.php",
                "GET",
                params={"token": "", "prehash": "0"},
                header_fingerprint="helper",
                cookie_policy="encoded-mac",
                expected_evidence="archived stalkerhek handshake",
            ),
            MAGDifferentialCase(
                "T05",
                gui,
                "portal.php",
                "POST",
                form={**gui.handshake_params, "prehash": "false"},
                header_fingerprint="gui",
                cookie_policy="raw-mac",
                expected_evidence="POST plus prehash source experiment",
            ),
            MAGDifferentialCase(
                "T06",
                helper,
                "stalker_portal/server/load.php",
                "POST",
                form={**helper.handshake_params, "prehash": "0"},
                header_fingerprint="helper",
                cookie_policy="encoded-mac",
                expected_evidence="POST form source experiment",
            ),
        )
        results = [await discovery.probe_case(case) for case in cases]
    finally:
        await connection.close()

    assert [result.test_id for result in results] == ["T01", "T02", "T03", "T04", "T05", "T06"]
    assert results[0].classification is MAGDiscoveryClassification.EMPTY_RESPONSE
    assert results[1].classification is MAGDiscoveryClassification.METHOD_NOT_ALLOWED
    assert results[2].token_present is True
    assert results[3].error_present is True
    assert results[4].classification is MAGDiscoveryClassification.METHOD_NOT_ALLOWED
    assert results[5].classification is MAGDiscoveryClassification.METHOD_NOT_ALLOWED
    assert all(
        result.endpoint in {"portal.php", "stalker_portal/server/load.php"} for result in results
    )
    assert "fixture-token" not in repr(results)
    assert len(state.requests) == 6
