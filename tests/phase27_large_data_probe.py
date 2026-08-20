"""Deterministic Phase 27 large-data measurements using real PySide6 presentation surfaces."""

from __future__ import annotations

import asyncio
import json
import os
import resource
import threading
from pathlib import Path
from time import perf_counter, process_time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel

from samotech_iptv.application.channel_catalogue_cache import ChannelCatalogueCache
from samotech_iptv.application.dtos import (
    ChannelDTO,
    ContentItemDTO,
    ContentType,
    EPGEntryDTO,
    LoadChannelsResponse,
    SearchChannelsResponse,
    SearchRegisteredChannelsRequest,
)
from samotech_iptv.application.use_cases.search_registered_channels import (
    SearchRegisteredChannels,
)
from samotech_iptv.domain.value_objects.provider_id import ProviderId
from samotech_iptv.infrastructure.parsing.m3u_parser import M3UParser
from samotech_iptv.presentation.dialogs.epg_grid_dialog import EPGGridDialog
from samotech_iptv.presentation.player_shell import PlayerShell

CHANNEL_TOTAL = 10_000
CONTENT_TOTAL = 10_000
EPG_TOTAL = 10_000
CATEGORY_TOTAL = 1_000


class FakeBrowse:
    async def execute(self, _: object) -> LoadChannelsResponse:
        return LoadChannelsResponse(channels=(), total=0)


class FakeSearch:
    async def execute(self, _: object) -> SearchChannelsResponse:
        return SearchChannelsResponse(channels=(), total=0)


class FakeFavorite:
    async def execute(self, _: object) -> object:
        return type("Result", (), {"success": True})()


class FakeProviders:
    async def execute(self) -> tuple[object, ...]:
        return ()


class FakeEPG:
    async def execute(self, _: object) -> object:
        return type("Result", (), {"entries": (), "error": None})()


class FakeResolver:
    def __init__(self) -> None:
        self.resolve_calls = 0
        self.search_calls = 0

    def resolve_search_provider(self, _: str) -> FakeResolver:
        self.resolve_calls += 1
        return self

    async def search_channels(self, _: str, limit: int = 100) -> tuple[object, ...]:
        del limit
        self.search_calls += 1
        return ()


async def noop() -> None:
    return None


def make_shell() -> PlayerShell:
    return PlayerShell(
        QLabel(),
        FakeBrowse(),  # type: ignore[arg-type]
        noop,
        FakeSearch(),  # type: ignore[arg-type]
        FakeFavorite(),  # type: ignore[arg-type]
        noop,
        noop,
        noop,
        FakeProviders(),  # type: ignore[arg-type]
        lambda: None,
        lambda: None,
        lambda: None,
        lambda: None,
        lambda: None,
        lambda: None,
    )


def channels(total: int = CHANNEL_TOTAL) -> tuple[ChannelDTO, ...]:
    categories = tuple(f"category-{index:04d}" for index in range(CATEGORY_TOTAL))
    return tuple(
        ChannelDTO(
            id=f"channel-{number:05d}",
            name=f"Arena Live {number}" if number % 10 == 0 else f"Channel {number}",
            provider_id="phase27-performance",
            stream_id=f"stream-{number}",
            category_id=categories[number % len(categories)],
            number=number,
        )
        for number in range(1, total + 1)
    )


def content(
    total: int = CONTENT_TOTAL, kind: ContentType = ContentType.MOVIE
) -> tuple[ContentItemDTO, ...]:
    return tuple(
        ContentItemDTO(
            id=f"{kind.value}-{number:05d}",
            provider_id="phase27-performance",
            content_type=kind,
            title=(
                f"Arena {kind.value.title()} {number}"
                if number % 10 == 0
                else f"{kind.value.title()} {number}"
            ),
            stream_id=f"stream-{number}" if kind is ContentType.MOVIE else None,
            category_id=f"genre-{number % 80}",
            year=2020 + number % 5,
        )
        for number in range(1, total + 1)
    )


def epg_entries(total: int = EPG_TOTAL) -> tuple[EPGEntryDTO, ...]:
    return tuple(
        EPGEntryDTO(
            id=f"epg-{number:05d}",
            channel_id=f"channel-{number % CHANNEL_TOTAL:05d}",
            title=f"Programme {number}",
            start="2026-08-20T12:00:00Z",
            end="2026-08-20T12:30:00Z",
        )
        for number in range(total)
    )


def playlist(total: int = CHANNEL_TOTAL) -> str:
    rows = ["#EXTM3U"]
    rows.extend(
        (
            f'#EXTINF:-1 tvg-id="channel-{number}" '
            f'group-title="Category {number % CATEGORY_TOTAL}",Channel {number}\n'
            f"https://media.example.test/live/{number}.m3u8"
        )
        for number in range(1, total + 1)
    )
    return "\n".join(rows)


def process_threads() -> int | None:
    try:
        for line in Path("/proc/self/status").read_text(encoding="utf-8").splitlines():
            if line.startswith("Threads:"):
                return int(line.split()[1])
    except OSError:
        return None
    return None


def metric(action: Callable[[], object]) -> tuple[float, float]:
    cpu_start = process_time()
    elapsed_start = perf_counter()
    action()
    return (
        round((perf_counter() - elapsed_start) * 1000, 3),
        round((process_time() - cpu_start) * 1000, 3),
    )


async def main() -> None:
    application = QApplication.instance() or QApplication([])
    before_rss_kib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    before_threads = process_threads()
    startup_start = perf_counter()
    shell = make_shell()
    startup_ms = round((perf_counter() - startup_start) * 1000, 3)
    dataset = channels()
    measurements: dict[str, dict[str, float | int]] = {}

    render_ms, render_cpu_ms = metric(
        lambda: (
            setattr(shell, "_catalogue_channels", dataset),
            shell._render_active_catalogue(),
        )
    )
    measurements["initial_live_render"] = {
        "wall_ms": render_ms,
        "cpu_ms": render_cpu_ms,
        "rows": shell.channel_model.rowCount(),
    }
    middle = shell.channel_model.index(CHANNEL_TOTAL // 2, 0)
    selection_ms, selection_cpu_ms = metric(
        lambda: (
            shell.channel_list.setCurrentIndex(middle),
            shell._select_index(middle),
            shell.channel_list.scrollTo(middle),
            application.processEvents(),
        )
    )
    measurements["selection_and_scroll"] = {
        "wall_ms": selection_ms,
        "cpu_ms": selection_cpu_ms,
        "selected_row": middle.row(),
    }
    shell._active_category_id = "category-0007"
    category_ms, category_cpu_ms = metric(shell._render_active_catalogue)
    measurements["category_switch"] = {
        "wall_ms": category_ms,
        "cpu_ms": category_cpu_ms,
        "rows": shell.channel_model.rowCount(),
    }
    shell._active_category_id = None
    cache = ChannelCatalogueCache()
    cache.replace("phase27-performance", dataset)
    resolver = FakeResolver()
    search = SearchRegisteredChannels(resolver, cache)  # type: ignore[arg-type]
    search_start = perf_counter()
    search_cpu_start = process_time()
    response = await search.execute(
        SearchRegisteredChannelsRequest("phase27-performance", "arena", limit=CHANNEL_TOTAL)
    )
    measurements["cached_search"] = {
        "wall_ms": round((perf_counter() - search_start) * 1000, 3),
        "cpu_ms": round((process_time() - search_cpu_start) * 1000, 3),
        "rows": response.total,
    }
    parse_start = perf_counter()
    parse_cpu_start = process_time()
    parsed = M3UParser().parse(playlist(), ProviderId("phase27-performance"))
    measurements["m3u_parse"] = {
        "wall_ms": round((perf_counter() - parse_start) * 1000, 3),
        "cpu_ms": round((process_time() - parse_cpu_start) * 1000, 3),
        "rows": len(parsed.channels),
    }
    category_start = perf_counter()
    shell.category_selector.blockSignals(True)
    shell.category_selector.clear()
    shell.category_selector.addItem("All live channels", None)
    for category_id in sorted({channel.category_id for channel in dataset if channel.category_id}):
        shell.category_selector.addItem(str(category_id), category_id)
    shell.category_selector.blockSignals(False)
    measurements["category_population"] = {
        "wall_ms": round((perf_counter() - category_start) * 1000, 3),
        "cpu_ms": 0.0,
        "rows": shell.category_selector.count(),
    }
    for content_type in (ContentType.MOVIE, ContentType.SERIES):
        shell._active_content_type = content_type
        shell._active_content_category_id = None
        shell._content_catalogues[content_type] = content(kind=content_type)
        shell.search_input.setText("")
        content_ms, content_cpu_ms = metric(
            lambda kind=content_type: shell._render_content_catalogue(kind)
        )
        measurements[f"{content_type.value}_render"] = {
            "wall_ms": content_ms,
            "cpu_ms": content_cpu_ms,
            "rows": shell.content_model.rowCount(),
        }
    epg_dialog = EPGGridDialog(FakeEPG())  # type: ignore[arg-type]
    epg_ms, epg_cpu_ms = metric(lambda: epg_dialog._render_entries(epg_entries()))
    measurements["epg_render"] = {
        "wall_ms": epg_ms,
        "cpu_ms": epg_cpu_ms,
        "rows": epg_dialog.epg_list.count(),
    }
    responsiveness_ms, responsiveness_cpu_ms = metric(application.processEvents)
    measurements["gui_event_turn"] = {
        "wall_ms": responsiveness_ms,
        "cpu_ms": responsiveness_cpu_ms,
        "rows": 1,
    }
    after_rss_kib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    result = {
        "startup_ms": startup_ms,
        "dataset_sizes": {
            "channels": CHANNEL_TOTAL,
            "movies": CONTENT_TOTAL,
            "series": CONTENT_TOTAL,
            "epg_entries": EPG_TOTAL,
            "categories": CATEGORY_TOTAL,
        },
        "measurements": measurements,
        "rss_kib": {
            "before": before_rss_kib,
            "after": after_rss_kib,
            "delta": after_rss_kib - before_rss_kib,
        },
        "process_threads": {"before": before_threads, "after": process_threads()},
        "python_threads": threading.active_count(),
        "provider_search_calls": resolver.search_calls,
        "resolver_calls": resolver.resolve_calls,
        "selected_channel": shell.selected_channel.id if shell.selected_channel else None,
    }
    assert result["dataset_sizes"]["channels"] == CHANNEL_TOTAL
    assert result["measurements"]["initial_live_render"]["rows"] == CHANNEL_TOTAL
    assert result["measurements"]["cached_search"]["rows"] == CHANNEL_TOTAL // 10
    assert result["measurements"]["m3u_parse"]["rows"] == CHANNEL_TOTAL
    assert result["measurements"]["category_population"]["rows"] == CATEGORY_TOTAL + 1
    assert result["measurements"]["movie_render"]["rows"] == CONTENT_TOTAL
    assert result["measurements"]["series_render"]["rows"] == CONTENT_TOTAL
    assert result["measurements"]["epg_render"]["rows"] == EPG_TOTAL
    assert result["provider_search_calls"] == 0
    assert result["resolver_calls"] == 0
    print(json.dumps(result, sort_keys=True))
    application.quit()


if __name__ == "__main__":
    asyncio.run(main())
