from __future__ import annotations

import asyncio
import json
import os
from time import perf_counter

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel

from samotech_iptv.application.channel_catalogue_cache import ChannelCatalogueCache
from samotech_iptv.application.dtos import (
    ChannelDTO,
    ContentItemDTO,
    ContentType,
    LoadChannelsResponse,
    SearchChannelsResponse,
    SearchRegisteredChannelsRequest,
)
from samotech_iptv.application.use_cases.search_registered_channels import (
    SearchRegisteredChannels,
)
from samotech_iptv.presentation.player_shell import PlayerShell
from samotech_iptv.presentation.viewmodels.content_list_model import ContentListModel

TOTAL = 39_753
CONTENT_TOTAL = 5_000
DYNAMIC_SIZES = (0, 1, 10, 100, 500, 1_000, 5_000, 10_000, 17_431, TOTAL, 50_000, 100_000)


class FakeBrowse:
    async def execute(self, _: object) -> LoadChannelsResponse:
        return LoadChannelsResponse(channels=(), total=0)


class FakeShellSearch:
    async def execute(self, _: object) -> SearchChannelsResponse:
        return SearchChannelsResponse(channels=(), total=0)


class FakeFavorite:
    async def execute(self, _: object) -> object:
        return type("Result", (), {"success": True})()


class FakeProviders:
    async def execute(self) -> tuple[object, ...]:
        return ()


class FakeResolver:
    def __init__(self) -> None:
        self.resolve_calls = 0
        self.search_calls = 0

    def resolve_search_provider(self, _: str) -> FakeResolver:
        self.resolve_calls += 1
        return self

    async def search_channels(self, _: str, limit: int = 100) -> tuple[object, ...]:
        self.search_calls += 1
        return ()


async def noop() -> None:
    return None


def make_shell() -> PlayerShell:
    return PlayerShell(
        QLabel(),
        FakeBrowse(),  # type: ignore[arg-type]
        noop,
        FakeShellSearch(),  # type: ignore[arg-type]
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


def channels(total: int = TOTAL) -> tuple[ChannelDTO, ...]:
    categories = ("news", "sports", "movies", "documentary")
    return tuple(
        ChannelDTO(
            id=f"channel-{number:05d}",
            name=(
                f"Arena Live {number}"
                if number % 10 == 0
                else f"World Report {number}" if number % 17 == 0 else f"Channel {number}"
            ),
            provider_id="performance-provider",
            stream_id=f"stream-{number}",
            category_id=categories[number % len(categories)],
            number=number,
        )
        for number in range(1, total + 1)
    )


def content_items(
    total: int = CONTENT_TOTAL,
    content_type: ContentType | None = None,
) -> tuple[ContentItemDTO, ...]:
    """Build synthetic non-live DTOs without provider or resolver interaction."""
    return tuple(
        ContentItemDTO(
            id=f"{content_type.value if content_type is not None else 'content'}-{number:05d}",
            provider_id="performance-provider",
            content_type=content_type or (ContentType.MOVIE if number % 2 else ContentType.SERIES),
            title=(
                f"Arena Content {number}" if number % 10 == 0 else f"Catalogue Content {number}"
            ),
            stream_id=(
                f"movie-stream-{number}"
                if (content_type or (ContentType.MOVIE if number % 2 else ContentType.SERIES))
                is ContentType.MOVIE
                else None
            ),
            category_id="drama" if number % 3 else "documentary",
            year=2020 + number % 5,
        )
        for number in range(1, total + 1)
    )


async def main() -> None:
    application = QApplication.instance() or QApplication([])
    dataset = channels()
    content_dataset = content_items()
    shell = make_shell()
    timings: dict[str, float] = {}

    start = perf_counter()
    shell.channel_model.replace_channels(dataset)
    timings["initial_model_replacement_ms"] = (perf_counter() - start) * 1000

    identities = (
        shell.channel_model.channel_at(0).id,
        shell.channel_model.channel_at(TOTAL // 2).id,
        shell.channel_model.channel_at(TOTAL - 1).id,
    )

    start = perf_counter()
    middle_index = shell.channel_model.index(TOTAL // 2, 0)
    shell.channel_list.setCurrentIndex(middle_index)
    shell._select_index(middle_index)
    timings["selection_latency_ms"] = (perf_counter() - start) * 1000
    initial_selection_identity = shell.selected_channel.id if shell.selected_channel else None

    start = perf_counter()
    shell.channel_model.replace_channels(())
    timings["empty_replacement_ms"] = (perf_counter() - start) * 1000
    empty_row_count = shell.channel_model.rowCount()

    start = perf_counter()
    shell._catalogue_channels = dataset
    shell._search_channels_result = tuple(
        channel for channel in dataset if "arena" in channel.name.casefold()
    )
    shell._render_active_catalogue()
    timings["search_result_replacement_ms"] = (perf_counter() - start) * 1000
    search_row_count = shell.channel_model.rowCount()

    content_model = ContentListModel()
    start = perf_counter()
    content_model.replace_items(content_dataset)
    timings["content_model_replacement_ms"] = (perf_counter() - start) * 1000
    content_identities = (
        content_model.item_at(0).id,
        content_model.item_at(CONTENT_TOTAL // 2).id,
        content_model.item_at(CONTENT_TOTAL - 1).id,
    )

    cache = ChannelCatalogueCache()
    cache.replace("performance-provider", dataset)
    resolver = FakeResolver()
    search = SearchRegisteredChannels(resolver, cache)  # type: ignore[arg-type]
    search_timings: dict[str, float] = {}
    search_counts: dict[str, int] = {}
    for label, query in (
        ("empty", ""),
        ("common", "arena"),
        ("rare", "world report 39746"),
        ("no_match", "missing signal"),
        ("repeated", "arena"),
        ("clear", ""),
    ):
        start = perf_counter()
        response = await search.execute(
            SearchRegisteredChannelsRequest("performance-provider", query, limit=TOTAL)
        )
        search_timings[f"{label}_search_ms"] = (perf_counter() - start) * 1000
        search_counts[label] = response.total

    dynamic_results: dict[str, dict[str, int | float | str | None]] = {}
    for size in DYNAMIC_SIZES:
        dynamic_dataset = channels(size)
        start = perf_counter()
        shell.channel_model.replace_channels(dynamic_dataset)
        replacement_ms = (perf_counter() - start) * 1000
        selection_identity: str | None = None
        selection_ms = 0.0
        first_middle_last_identity: tuple[str, str, str] | None = None
        if dynamic_dataset:
            first_middle_last_identity = (
                shell.channel_model.channel_at(0).id,
                shell.channel_model.channel_at(size // 2).id,
                shell.channel_model.channel_at(size - 1).id,
            )
            middle_index = shell.channel_model.index(size // 2, 0)
            start = perf_counter()
            shell.channel_list.setCurrentIndex(middle_index)
            shell._select_index(middle_index)
            selection_ms = (perf_counter() - start) * 1000
            selection_identity = shell.selected_channel.id if shell.selected_channel else None

        shell._catalogue_channels = dynamic_dataset
        shell._active_category_id = "sports"
        start = perf_counter()
        shell._render_active_catalogue()
        category_filter_ms = (perf_counter() - start) * 1000
        category_rows = shell.channel_model.rowCount()

        shell._active_category_id = None
        shell._search_channels_result = tuple(
            channel for channel in dynamic_dataset if "arena" in channel.name.casefold()
        )
        start = perf_counter()
        shell._render_active_catalogue()
        search_render_ms = (perf_counter() - start) * 1000
        search_rows = shell.channel_model.rowCount()

        shell._search_channels_result = ()
        start = perf_counter()
        shell._render_active_catalogue()
        no_match_search_ms = (perf_counter() - start) * 1000
        no_match_rows = shell.channel_model.rowCount()

        shell._search_channels_result = None
        start = perf_counter()
        shell._render_active_catalogue()
        clear_search_ms = (perf_counter() - start) * 1000
        dynamic_results[str(size)] = {
            "model_replacement_ms": round(replacement_ms, 3),
            "selection_ms": round(selection_ms, 3),
            "selection_identity": selection_identity,
            "first_middle_last_identity": first_middle_last_identity,
            "category_filter_ms": round(category_filter_ms, 3),
            "category_rows": category_rows,
            "search_render_ms": round(search_render_ms, 3),
            "search_rows": search_rows,
            "no_match_search_ms": round(no_match_search_ms, 3),
            "no_match_rows": no_match_rows,
            "clear_search_ms": round(clear_search_ms, 3),
            "clear_search_rows": shell.channel_model.rowCount(),
        }

    content_dynamic_results: dict[
        str, dict[str, dict[str, int | float | str | tuple[str, str, str] | None]]
    ] = {}
    for content_type in (ContentType.MOVIE, ContentType.SERIES):
        family_results: dict[str, dict[str, int | float | str | tuple[str, str, str] | None]] = {}
        shell._content_categories[content_type] = (
            ("Drama", "drama"),
            ("Documentary", "documentary"),
        )
        shell._active_content_type = content_type
        for size in DYNAMIC_SIZES:
            dynamic_content = content_items(size, content_type)
            shell._content_catalogues[content_type] = dynamic_content
            shell._active_content_category_id = None
            shell.search_input.setText("")
            start = perf_counter()
            shell._render_content_catalogue(content_type)
            replacement_ms = (perf_counter() - start) * 1000
            content_identities_for_size: tuple[str, str, str] | None = None
            selection_identity: str | None = None
            selection_ms = 0.0
            if dynamic_content:
                content_identities_for_size = (
                    shell.content_model.item_at(0).id,
                    shell.content_model.item_at(size // 2).id,
                    shell.content_model.item_at(size - 1).id,
                )
                middle_index = shell.content_model.index(size // 2, 0)
                start = perf_counter()
                shell._content_lists[content_type].setCurrentIndex(middle_index)
                shell._select_content_index(content_type, middle_index)
                selection_ms = (perf_counter() - start) * 1000
                selection_identity = (
                    shell.selected_content.id if shell.selected_content is not None else None
                )

            shell._active_content_category_id = "drama"
            start = perf_counter()
            shell._render_content_catalogue(content_type)
            category_filter_ms = (perf_counter() - start) * 1000
            category_rows = shell.content_model.rowCount()

            shell._active_content_category_id = None
            shell.search_input.setText("arena")
            start = perf_counter()
            shell._render_content_catalogue(content_type)
            search_render_ms = (perf_counter() - start) * 1000
            search_rows = shell.content_model.rowCount()

            shell.search_input.setText("missing signal")
            start = perf_counter()
            shell._render_content_catalogue(content_type)
            no_match_search_ms = (perf_counter() - start) * 1000
            no_match_rows = shell.content_model.rowCount()

            shell.search_input.setText("")
            start = perf_counter()
            shell._render_content_catalogue(content_type)
            clear_search_ms = (perf_counter() - start) * 1000
            family_results[str(size)] = {
                "model_replacement_ms": round(replacement_ms, 3),
                "selection_ms": round(selection_ms, 3),
                "selection_identity": selection_identity,
                "first_middle_last_identity": content_identities_for_size,
                "category_filter_ms": round(category_filter_ms, 3),
                "category_rows": category_rows,
                "search_render_ms": round(search_render_ms, 3),
                "search_rows": search_rows,
                "no_match_search_ms": round(no_match_search_ms, 3),
                "no_match_rows": no_match_rows,
                "clear_search_ms": round(clear_search_ms, 3),
                "clear_search_rows": shell.content_model.rowCount(),
            }
        content_dynamic_results[content_type.value] = family_results

    result = {
        "total_records": TOTAL,
        "model_row_count_after_initial_replace": TOTAL,
        "first_middle_last_identity": identities,
        "selection_identity": initial_selection_identity,
        "empty_row_count": empty_row_count,
        "search_result_row_count": search_row_count,
        "content_model_records": CONTENT_TOTAL,
        "content_model_row_count": content_model.rowCount(),
        "content_first_middle_last_identity": content_identities,
        "resolver_calls": resolver.resolve_calls,
        "provider_search_calls": resolver.search_calls,
        "catalogue_reload_calls": 0,
        "timings_ms": {key: round(value, 3) for key, value in timings.items()},
        "search_timings_ms": {key: round(value, 3) for key, value in search_timings.items()},
        "search_counts": search_counts,
        "dynamic_catalogue_results": dynamic_results,
        "dynamic_content_results": content_dynamic_results,
    }
    assert result["model_row_count_after_initial_replace"] == TOTAL
    assert identities == ("channel-00001", "channel-19877", "channel-39753")
    assert result["selection_identity"] == "channel-19877"
    assert empty_row_count == 0
    assert search_row_count == TOTAL // 10
    assert content_model.rowCount() == CONTENT_TOTAL
    assert content_identities == ("content-00001", "content-02501", "content-05000")
    assert resolver.resolve_calls == 0
    assert resolver.search_calls == 0
    assert tuple(int(size) for size in dynamic_results) == DYNAMIC_SIZES
    for size, values in dynamic_results.items():
        assert values["clear_search_rows"] == int(size)
        assert values["category_rows"] <= int(size)
        assert values["no_match_rows"] == 0
        if int(size) > 0:
            assert values["first_middle_last_identity"] == (
                "channel-00001",
                f"channel-{int(size) // 2 + 1:05d}",
                f"channel-{int(size):05d}",
            )
    for content_type, family_results in content_dynamic_results.items():
        assert tuple(int(size) for size in family_results) == DYNAMIC_SIZES
        for size, values in family_results.items():
            assert values["clear_search_rows"] == int(size)
            assert values["category_rows"] <= int(size)
            assert values["no_match_rows"] == 0
            if int(size) > 0:
                assert values["first_middle_last_identity"] == (
                    f"{content_type}-00001",
                    f"{content_type}-{int(size) // 2 + 1:05d}",
                    f"{content_type}-{int(size):05d}",
                )
    print(json.dumps(result, indent=2))
    application.quit()


if __name__ == "__main__":
    asyncio.run(main())
