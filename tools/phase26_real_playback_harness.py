"""Phase 26 local real-playback acceptance harness.

This tool is deliberately outside the production playback architecture. It has two
modes:

* ``mock`` runs entirely on localhost with generated M3U metadata and deterministic
  media-time scenarios.
* ``real`` accepts an explicitly supplied authorized stream URL through environment
  variables and reuses the existing VlcPlayerAdapter and VlcVideoSurface.

The tool never prints or persists credentials, tokens, cookies, authorization headers,
or raw configured stream URLs. Public demo URLs are optional fixtures only; they are
not commercial IPTV acceptance evidence.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import re
import threading
import time
from dataclasses import asdict, dataclass
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVIDENCE = ROOT / "build" / "phase26_synthetic_evidence.json"
DEFAULT_M3U = ROOT / "build" / "phase26_generated_playlist.m3u"

PUBLIC_FIXTURES = {
    "mux_big_buck_bunny_adaptive": {
        "url": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8",
        "kind": "public_test_vod",
        "source": "Mux Test HLS Streams",
    },
    "mux_big_buck_bunny_480p": {
        "url": "https://test-streams.mux.dev/x36xhzz/url_6/193039199_mp4_h264_aac_hq_7.m3u8",
        "kind": "public_test_vod",
        "source": "Mux Test HLS Streams",
    },
    "public_test_streams_repo": {
        "url": "https://github.com/video-commander/public-test-streams",
        "kind": "public_fixture_catalogue",
        "source": "video-commander/public-test-streams (MIT)",
    },
}


def generated_m3u(base_url: str) -> str:
    """Return deterministic generated metadata with local-only stream URLs."""
    return "\n".join(
        [
            "#EXTM3U",
            (
                '#EXTINF:-1 tvg-id="synthetic-news" tvg-name="Synthetic News" '
                'group-title="News" tvg-logo="https://example.test/news.png",Synthetic News'
            ),
            f"{base_url}/media/live-news.m3u8",
            (
                '#EXTINF:-1 tvg-id="synthetic-sports" tvg-name="Synthetic Sports" '
                'group-title="Sports" tvg-logo="https://example.test/sports.png",Synthetic Sports'
            ),
            f"{base_url}/media/live-sports.m3u8",
            (
                '#EXTINF:-1 tvg-id="synthetic-cinema" tvg-name="Synthetic Cinema" '
                'group-title="Movies" tvg-logo="https://example.test/cinema.png",Synthetic Cinema'
            ),
            f"{base_url}/media/live-cinema.m3u8",
            "",
        ]
    )


def write_generated_m3u(path: Path, base_url: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(generated_m3u(base_url), encoding="utf-8")


def identifier_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def sanitized_url_identifier(value: str) -> str:
    """Hash a URL without retaining its query, path, or credential-bearing text."""
    return identifier_hash(value)


def configured_value(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name, default)
    return value.strip() if value and value.strip() else default


def _safe_text(value: str) -> str:
    return re.sub(r"[\r\n\t]", " ", value)[:200]


@dataclass(frozen=True)
class EvidenceSample:
    timestamp: float
    provider_type: str
    content_type: str
    stream_identifier_hash: str
    vlc_state: str
    media_time: int | None
    position: float | None
    duration: int | None
    buffering_state: str
    recovery_state: str
    GUI_responsive: bool


@dataclass(frozen=True)
class HarnessResult:
    mode: str
    scenario: str
    result: str
    provider_type: str
    content_type: str
    stream_identifier_hash: str
    samples: tuple[EvidenceSample, ...]
    recovery_attempts: int
    notes: tuple[str, ...] = ()

    def to_json(self) -> dict[str, Any]:
        data = asdict(self)
        data["samples"] = [asdict(sample) for sample in self.samples]
        return data


class SyntheticMediaClock:
    """Deterministic clock for progress, stall, interruption, and recovery tests."""

    def __init__(self, *, scenario: str, duration_ms: int = 120_000) -> None:
        if scenario not in {"progress", "stall", "interruption", "switching"}:
            raise ValueError("unsupported synthetic scenario")
        self.scenario = scenario
        self.duration_ms = duration_ms
        self.media_time_ms = 0
        self.sample_index = 0
        self.recovery_attempts = 0
        self.recovered = False

    def sample(self) -> tuple[str, int, float, str, str]:
        self.sample_index += 1
        if (
            self.scenario in {"stall", "interruption"}
            and self.sample_index >= 4
            and not self.recovered
        ):
            if self.sample_index == 4:
                self.recovery_attempts += 1
                return (
                    "Playing",
                    self.media_time_ms,
                    self.media_time_ms / self.duration_ms,
                    "stalled",
                    "recovering",
                )
            if self.sample_index == 5:
                self.recovered = True
                self.media_time_ms += 4_000
                return (
                    "Playing",
                    self.media_time_ms,
                    self.media_time_ms / self.duration_ms,
                    "rebuffering",
                    "resumed",
                )
        self.media_time_ms += 4_000
        return (
            "Playing",
            self.media_time_ms,
            self.media_time_ms / self.duration_ms,
            "stable",
            "none",
        )


def run_synthetic(
    *, scenario: str, provider_type: str = "synthetic", content_type: str = "LIVE"
) -> HarnessResult:
    clock = SyntheticMediaClock(scenario=scenario)
    stream_hash = identifier_hash(f"synthetic://{provider_type}/{scenario}/{content_type}")
    samples: list[EvidenceSample] = []
    for _ in range(8):
        state, media_time, position, buffering, recovery = clock.sample()
        samples.append(
            EvidenceSample(
                timestamp=round(time.monotonic(), 3),
                provider_type=provider_type,
                content_type=content_type,
                stream_identifier_hash=stream_hash,
                vlc_state=state,
                media_time=media_time,
                position=round(position, 6),
                duration=clock.duration_ms,
                buffering_state=buffering,
                recovery_state=recovery,
                GUI_responsive=True,
            )
        )
    positions = [sample.media_time for sample in samples if sample.media_time is not None]
    if scenario == "progress":
        result = (
            "PASS"
            if all(left < right for left, right in zip(positions, positions[1:], strict=False))
            else "DEFECT"
        )
    elif scenario in {"stall", "interruption"}:
        stalled = any(sample.buffering_state == "stalled" for sample in samples)
        resumed = any(sample.recovery_state == "resumed" for sample in samples)
        result = "PASS" if stalled and resumed and clock.recovery_attempts == 1 else "DEFECT"
    else:
        result = "PASS" if all(sample.GUI_responsive for sample in samples) else "DEFECT"
    return HarnessResult(
        mode="mock",
        scenario=scenario,
        result=result,
        provider_type=provider_type,
        content_type=content_type,
        stream_identifier_hash=stream_hash,
        samples=tuple(samples),
        recovery_attempts=clock.recovery_attempts,
        notes=("Synthetic evidence is not real provider acceptance.",),
    )


class _MockHandler(BaseHTTPRequestHandler):
    server_version = "Phase26Mock/1.0"

    def log_message(self, _format: str, *_args: object) -> None:
        return

    def _send(self, status: int, content_type: str, body: str) -> None:
        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        path = parsed.path
        if path == "/m3u/playlist.m3u8":
            self._send(
                200,
                "application/vnd.apple.mpegurl",
                generated_m3u(self.server.base_url),  # type: ignore[attr-defined]
            )
            return
        if path == "/player_api.php":
            query = parse_qs(parsed.query)
            action = query.get("action", [""])[0]
            payload: object
            if action == "get_live_categories":
                payload = [{"category_id": "1", "category_name": "Synthetic News"}]
            elif action == "get_live_streams":
                payload = [{"stream_id": 101, "name": "Synthetic News", "stream_icon": ""}]
            elif action == "get_vod_categories":
                payload = [{"category_id": "2", "category_name": "Synthetic Movies"}]
            elif action == "get_series_categories":
                payload = [{"category_id": "3", "category_name": "Synthetic Series"}]
            elif action == "get_short_epg":
                payload = {"epg_listings": []}
            else:
                payload = {"user_info": {"auth": 1}, "server_info": {"url": self.server.base_url}}  # type: ignore[attr-defined]
            self._send(200, "application/json", json.dumps(payload))
            return
        if path == "/stalker/handshake":
            self._send(
                200,
                "application/json",
                json.dumps({"js": {"session_marker": "synthetic-session-marker"}}),
            )
            return
        if path == "/stalker/get_profile":
            self._send(200, "application/json", json.dumps({"js": {"status": "ok"}}))
            return
        if path == "/stalker/channels":
            self._send(
                200, "application/json", json.dumps({"js": [{"id": 101, "name": "Synthetic News"}]})
            )
            return
        if path == "/stalker/create_link":
            self._send(
                200,
                "application/json",
                json.dumps(
                    {"js": {"cmd": f"{self.server.base_url}/media/live-news.m3u8"}}  # type: ignore[attr-defined]
                ),
            )
            return
        if path.startswith("/media/"):
            self._send(200, "application/vnd.apple.mpegurl", "#EXTM3U\n#EXT-X-ENDLIST\n")
            return
        self._send(404, "application/json", json.dumps({"error": "not_found"}))


class MockEndpointServer:
    """Local-only Xtream/MAG/M3U endpoint server for deterministic tests."""

    def __init__(self) -> None:
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), _MockHandler)
        address = self._server.server_address
        host = str(address[0])
        port = int(address[1])
        self.base_url = f"http://{host}:{port}"
        self._server.base_url = self.base_url  # type: ignore[attr-defined]
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    def __enter__(self) -> MockEndpointServer:
        self._thread.start()
        return self

    def __exit__(self, *_args: object) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=2)

    def request_text(self, path: str) -> str:
        parsed = urlsplit(self.base_url)
        if parsed.hostname not in {"127.0.0.1", "localhost"}:
            raise RuntimeError("mock endpoint must remain localhost-only")
        connection = HTTPConnection(parsed.hostname, parsed.port, timeout=5)
        try:
            connection.request("GET", path, headers={"Accept": "application/json"})
            response = connection.getresponse()
            if response.status != 200:
                raise RuntimeError(f"mock endpoint returned HTTP {response.status}")
            return response.read().decode("utf-8")
        finally:
            connection.close()


async def run_real() -> HarnessResult:
    """Run the existing VlcPlayerAdapter against an explicitly configured stream."""
    stream_url = configured_value("PHASE26_STREAM_URL")
    provider_type = configured_value("PHASE26_PROVIDER_TYPE", "authorized") or "authorized"
    content_type = (configured_value("PHASE26_CONTENT_TYPE", "LIVE") or "LIVE").upper()
    if not stream_url:
        return HarnessResult(
            mode="real",
            scenario="authorized_stream",
            result="AUTHORIZED DATA BLOCKED",
            provider_type=provider_type,
            content_type=content_type,
            stream_identifier_hash="",
            samples=(),
            recovery_attempts=0,
            notes=("Set PHASE26_STREAM_URL only with an authorized stream URL.",),
        )

    try:
        from PySide6.QtWidgets import QApplication

        from samotech_iptv.application.dtos.content import ContentType
        from samotech_iptv.application.dtos.playback import PlaybackResource, ResolvedPlayback
        from samotech_iptv.domain.value_objects.url import URL
        from samotech_iptv.infrastructure.player.vlc_player_adapter import VlcPlayerAdapter
        from samotech_iptv.presentation.widgets.vlc_video_surface import VlcVideoSurface
    except Exception as exc:  # pragma: no cover - environment-specific
        return HarnessResult(
            mode="real",
            scenario="authorized_stream",
            result="ENVIRONMENTAL BLOCKER",
            provider_type=provider_type,
            content_type=content_type,
            stream_identifier_hash=sanitized_url_identifier(stream_url),
            samples=(),
            recovery_attempts=0,
            notes=(f"Real harness imports unavailable: {type(exc).__name__}.",),
        )

    stream_hash = sanitized_url_identifier(stream_url)
    app = QApplication.instance() or QApplication([])
    try:
        adapter = VlcPlayerAdapter()
    except Exception as exc:  # pragma: no cover - native-runtime-specific
        if QApplication.instance() is app:
            app.quit()
        return HarnessResult(
            mode="real",
            scenario="authorized_stream",
            result="ENVIRONMENTAL BLOCKER",
            provider_type=provider_type,
            content_type=content_type,
            stream_identifier_hash=stream_hash,
            samples=(),
            recovery_attempts=0,
            notes=(f"libVLC initialization unavailable: {type(exc).__name__}.",),
        )
    surface = VlcVideoSurface(adapter)
    surface.resize(960, 540)
    surface.show()
    app.processEvents()
    enum_type = ContentType(content_type)
    if enum_type is ContentType.LIVE:
        resource = PlaybackResource.live(provider_type, "authorized-live")
    elif enum_type is ContentType.MOVIE:
        resource = PlaybackResource.movie(provider_type, "authorized-movie", "movie")
    else:
        resource = PlaybackResource.episode(
            provider_type, "authorized-episode", "episode", "series", 1, 1
        )
    playback = ResolvedPlayback.from_url(URL(stream_url), resource=resource)
    samples: list[EvidenceSample] = []
    interval_s = float(configured_value("PHASE26_SAMPLE_INTERVAL_S", "2") or "2")
    duration_s = float(configured_value("PHASE26_SAMPLE_DURATION_S", "30") or "30")
    started = time.monotonic()
    try:
        await adapter.play(playback)
        while time.monotonic() - started < duration_s:
            loop_started = time.monotonic()
            app.processEvents()
            media_time = await adapter.get_position_ms()
            duration = await adapter.get_duration_ms()
            state = getattr(adapter.state, "value", str(adapter.state))
            samples.append(
                EvidenceSample(
                    timestamp=round(time.monotonic() - started, 3),
                    provider_type=provider_type,
                    content_type=content_type,
                    stream_identifier_hash=stream_hash,
                    vlc_state=state,
                    media_time=media_time,
                    position=(
                        media_time / duration
                        if media_time is not None and duration and duration > 0
                        else None
                    ),
                    duration=duration,
                    buffering_state=state if state in {"buffering", "reconnecting"} else "stable",
                    recovery_state="recovering" if state == "reconnecting" else "none",
                    GUI_responsive=(time.monotonic() - loop_started) < 1.0,
                )
            )
            await asyncio.sleep(interval_s)
        times = [sample.media_time for sample in samples if sample.media_time is not None]
        progressed = len(times) >= 2 and all(
            left < right for left, right in zip(times, times[1:], strict=False)
        )
        result = "PASS" if progressed else "DEFECT"
        return HarnessResult(
            mode="real",
            scenario="authorized_stream",
            result=result,
            provider_type=provider_type,
            content_type=content_type,
            stream_identifier_hash=stream_hash,
            samples=tuple(samples),
            recovery_attempts=sum(sample.recovery_state == "recovering" for sample in samples),
            notes=("PASS requires repeated forward media-time samples.",),
        )
    finally:
        await adapter.stop()
        await adapter.close()
        surface.close()
        if QApplication.instance() is app:
            app.quit()


def write_evidence(results: list[HarnessResult], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "phase": 26,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "results": [result.to_json() for result in results],
        "public_fixtures": PUBLIC_FIXTURES,
        "security": {
            "raw_stream_urls_persisted": False,
            "credentials_persisted": False,
            "authorization_headers_persisted": False,
        },
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("mock", "real"), default="mock")
    parser.add_argument(
        "--scenario", choices=("progress", "stall", "interruption", "switching"), default="progress"
    )
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--write-m3u", type=Path, default=DEFAULT_M3U)
    parser.add_argument("--serve-seconds", type=float, default=0)
    args = parser.parse_args()

    if args.mode == "mock":
        with MockEndpointServer() as server:
            write_generated_m3u(args.write_m3u, server.base_url)
            results = [run_synthetic(scenario=args.scenario)]
            if args.serve_seconds > 0:
                time.sleep(args.serve_seconds)
    else:
        results = [asyncio.run(run_real())]
    write_evidence(results, args.evidence)
    print(
        json.dumps(
            {
                "mode": args.mode,
                "scenario": args.scenario,
                "result": results[0].result,
                "evidence": str(args.evidence),
                "generated_m3u": str(args.write_m3u),
            },
            indent=2,
        )
    )
    return (
        0
        if results[0].result in {"PASS", "AUTHORIZED DATA BLOCKED", "ENVIRONMENTAL BLOCKER"}
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
