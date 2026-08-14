from __future__ import annotations

import asyncio
import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication, QLabel

from samotech_iptv.application.dtos import (
    BrowseContentResponse,
    CategoryDTO,
    ChannelDTO,
    ContentItemDTO,
    ContentType,
    LoadCategoriesResponse,
    LoadChannelsResponse,
    ProviderCapabilities,
    ProviderMetadata,
    SearchChannelsResponse,
)
from samotech_iptv.presentation.dialogs.channel_browser_dialog import ChannelBrowserDialog
from samotech_iptv.presentation.player_shell import PlayerShell

N = 3


def make_channel(
    name: str, category_id: str | None = None, number: int | None = None
) -> ChannelDTO:
    return ChannelDTO(
        id=name.lower(),
        name=name,
        provider_id="provider-a",
        stream_id=name,
        category_id=category_id,
        number=number,
    )


class FakeBrowse:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.response = LoadChannelsResponse(channels=(), total=0)

    async def execute(self, _: object) -> LoadChannelsResponse:
        if self.error:
            raise self.error
        return self.response


class FakeSearch:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.response = SearchChannelsResponse(channels=(), total=0)
        self.started = asyncio.Event()
        self.release = asyncio.Event()
        self.wait_for_release = False

    async def execute(self, _: object) -> SearchChannelsResponse:
        self.started.set()
        if self.wait_for_release:
            await self.release.wait()
        if self.error:
            raise self.error
        return self.response


class FakeFavorite:
    def __init__(self) -> None:
        self.ids: list[str] = []

    async def execute(self, request: object) -> SimpleNamespace:
        self.ids.append(request.item_id)
        return SimpleNamespace(success=True)


class FakeProviders:
    def __init__(self, providers: tuple[ProviderMetadata, ...]) -> None:
        self.providers = providers

    async def execute(self) -> tuple[ProviderMetadata, ...]:
        return self.providers


class FakeCategories:
    def __init__(self, categories: tuple[CategoryDTO, ...]) -> None:
        self.categories = categories
        self.started = asyncio.Event()
        self.release = asyncio.Event()
        self.wait_for_release = False

    async def execute(self, _: object) -> LoadCategoriesResponse:
        self.started.set()
        if self.wait_for_release:
            await self.release.wait()
        return LoadCategoriesResponse(categories=self.categories)


class FakeContent:
    def __init__(self, items: dict[ContentType, tuple[ContentItemDTO, ...]]) -> None:
        self.items = items
        self.calls: list[ContentType] = []

    async def execute(self, request: object) -> BrowseContentResponse:
        content_type = request.content_type
        self.calls.append(content_type)
        items = self.items.get(content_type, ())
        return BrowseContentResponse(items=items, total=len(items))


class FakeCapabilities:
    def __init__(self, capabilities: ProviderCapabilities) -> None:
        self.capabilities = capabilities
        self.provider_ids: list[str] = []

    def execute(self, provider_id: str) -> ProviderCapabilities:
        self.provider_ids.append(provider_id)
        return self.capabilities


async def noop() -> None:
    return None


def make_shell(
    browse: FakeBrowse,
    search: FakeSearch,
    favorite: FakeFavorite,
    play: object,
    providers: FakeProviders | None = None,
    categories: FakeCategories | None = None,
    content: FakeContent | None = None,
    capabilities: FakeCapabilities | None = None,
) -> PlayerShell:
    return PlayerShell(
        QLabel(),
        browse,
        play,  # type: ignore[arg-type]
        search,  # type: ignore[arg-type]
        favorite,  # type: ignore[arg-type]
        noop,
        noop,
        noop,
        providers or FakeProviders(()),
        lambda: None,
        lambda: None,
        lambda: None,
        lambda: None,
        lambda: None,
        lambda: None,
        load_categories=categories,  # type: ignore[arg-type]
        browse_content=content,  # type: ignore[arg-type]
        load_provider_capabilities=capabilities,  # type: ignore[arg-type]
    )


async def main() -> None:
    app = QApplication.instance() or QApplication([])
    a, b, c = (
        make_channel("A", "news", 1),
        make_channel("B", "sports", 2),
        make_channel("C", "news", 3),
    )
    played: list[str] = []

    async def play(_: str, channel_id: str) -> None:
        played.append(channel_id)

    favorite = FakeFavorite()
    shell = make_shell(FakeBrowse(), FakeSearch(), favorite, play)
    shell._render_channels((a, b, c))
    shell.channel_list.setCurrentIndex(shell.channel_model.index(1, 0))
    shell._select_index(shell.channel_model.index(1, 0))
    assert shell.selected_channel is b
    assert "B" in shell.current_channel_label.text()
    assert played == []
    shell._schedule_selected_channel(shell.channel_model.index(1, 0))
    shell._schedule_add_favorite()
    shell._render_channels((a, c))
    await asyncio.sleep(0)
    assert played == ["b"]
    assert favorite.ids == ["b"]

    legacy_favorite = FakeFavorite()
    legacy_dialog = ChannelBrowserDialog(
        FakeBrowse(), play, FakeSearch(), legacy_favorite  # type: ignore[arg-type]
    )
    legacy_dialog._render_channels((a, b, c))
    legacy_dialog.channel_list.setCurrentIndex(legacy_dialog.channel_model.index(1, 0))
    legacy_dialog._schedule_selected_channel(legacy_dialog.channel_model.index(1, 0))
    legacy_dialog._schedule_add_favorite()
    legacy_dialog._render_channels((a, c))
    await asyncio.sleep(0)
    assert played == ["b", "b"]
    assert legacy_favorite.ids == ["b"]

    failure_shell = make_shell(
        FakeBrowse(error=RuntimeError("provider failed")),
        FakeSearch(error=RuntimeError("search failed")),
        FakeFavorite(),
        play,
    )
    await failure_shell.load_channels()
    assert failure_shell.channel_status.text() == "Unable to load channels"
    assert failure_shell.load_button.isEnabled()
    await failure_shell.search_channels()
    assert failure_shell.channel_status.text() == "Unable to search channels"
    assert failure_shell.search_button.isEnabled()

    old, new = make_channel("Old"), make_channel("New")
    search = FakeSearch()
    search.wait_for_release = True
    stale_shell = make_shell(FakeBrowse(), search, FakeFavorite(), play)
    first = asyncio.create_task(stale_shell.search_channels(stale_shell._begin_request()))
    await search.started.wait()
    search.wait_for_release = False
    search.response = SearchChannelsResponse(channels=(new,), total=1)
    second = asyncio.create_task(stale_shell.search_channels(stale_shell._begin_request()))
    await second
    search.release.set()
    search.response = SearchChannelsResponse(channels=(old,), total=1)
    await first
    assert stale_shell.channel_model.channel_at(0) is new

    providers = FakeProviders(
        (ProviderMetadata("provider-a", "Provider A", "m3u", "https://safe.invalid", True),)
    )
    provider_shell = make_shell(FakeBrowse(), FakeSearch(), FakeFavorite(), play, providers)
    await provider_shell.refresh_providers()
    provider_shell.provider_selector.setCurrentIndex(1)
    assert provider_shell._provider_id() == "provider-a"
    assert provider_shell.provider_selector.accessibleName() == "Active IPTV provider"
    assert provider_shell.channel_list.accessibleName() == "Live channel list"
    assert provider_shell.navigation.accessibleName() == "Main navigation"

    category_shell = make_shell(
        FakeBrowse(),
        FakeSearch(),
        FakeFavorite(),
        play,
        categories=FakeCategories((CategoryDTO("sports", "Sports", "provider-a"),)),
    )
    category_shell.provider_selector.setEditText("provider-a")
    category_shell._catalogue_channels = (a, b, c)
    await category_shell.refresh_categories("provider-a")
    category_shell.category_selector.setCurrentIndex(1)
    assert category_shell.channel_model.rowCount() == 1
    assert category_shell.channel_model.channel_at(0) is b

    movie = ContentItemDTO(
        id="movie-1",
        provider_id="provider-a",
        content_type=ContentType.MOVIE,
        title="Arena Film",
        stream_id="movie-stream-1",
        category_id="sports",
        year=2024,
    )
    series = ContentItemDTO(
        id="series-1",
        provider_id="provider-a",
        content_type=ContentType.SERIES,
        title="Arena Series",
        category_id="sports",
        year=2023,
    )
    content = FakeContent({ContentType.MOVIE: (movie,), ContentType.SERIES: (series,)})
    capabilities = FakeCapabilities(
        ProviderCapabilities(live_tv=True, vod_movies=True, vod_series=True, epg=False)
    )
    content_shell = make_shell(
        FakeBrowse(),
        FakeSearch(),
        FakeFavorite(),
        play,
        categories=FakeCategories((CategoryDTO("sports", "Sports", "provider-a"),)),
        content=content,
        capabilities=capabilities,
    )
    content_shell.provider_selector.setEditText("provider-a")
    await content_shell.refresh_provider_capabilities("provider-a")
    assert content_shell.navigation_model.stringList() == [
        "Home",
        "Live TV",
        "Movies",
        "Series",
        "Favorites",
        "History",
        "Providers",
        "Settings",
    ]
    content_shell._active_content_type = ContentType.MOVIE
    await content_shell.load_content(ContentType.MOVIE)
    assert content_shell.content_model.rowCount() == 1
    assert content_shell.content_model.item_at(0) is movie
    content_shell._select_content_index(ContentType.MOVIE, content_shell.content_model.index(0, 0))
    assert content_shell.selected_content is movie
    assert played == ["b", "b"]
    content_shell.search_input.setText("2024")
    content_shell._schedule_search()
    assert content_shell.content_model.rowCount() == 1
    assert content.calls == [ContentType.MOVIE]
    movie_index = content_shell.content_model.index(0, 0)
    content_shell._content_lists[ContentType.MOVIE].setCurrentIndex(movie_index)
    movie_enter = QKeyEvent(
        QEvent.Type.KeyPress,
        Qt.Key.Key_Return,
        Qt.KeyboardModifier.NoModifier,
    )
    assert content_shell.eventFilter(content_shell._content_lists[ContentType.MOVIE], movie_enter)
    assert (
        "VOD playback is not exposed"
        in content_shell._content_detail_labels[ContentType.MOVIE].text()
    )
    assert played == ["b", "b"]

    stale_categories = FakeCategories((CategoryDTO("sports", "Sports", "provider-a"),))
    stale_categories.wait_for_release = True
    stale_content_shell = make_shell(
        FakeBrowse(),
        FakeSearch(),
        FakeFavorite(),
        play,
        categories=stale_categories,
        content=FakeContent({ContentType.MOVIE: (movie,)}),
    )
    stale_content_shell.provider_selector.setEditText("provider-a")
    stale_content_load = asyncio.create_task(stale_content_shell.load_content(ContentType.MOVIE))
    await stale_categories.started.wait()
    stale_content_shell.provider_selector.setEditText("provider-b")
    stale_content_shell._provider_changed(0)
    stale_categories.release.set()
    await stale_content_load
    assert ContentType.MOVIE not in stale_content_shell._content_catalogues
    assert stale_content_shell.content_model.rowCount() == 0

    provider_shell._render_channels((a, b))
    provider_shell.channel_list.setCurrentIndex(provider_shell.channel_model.index(0, 0))
    down = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Down, Qt.KeyboardModifier.NoModifier)
    assert provider_shell.eventFilter(provider_shell.channel_list, down)
    assert provider_shell.channel_list.currentIndex().row() == 1
    fullscreen = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_F, Qt.KeyboardModifier.NoModifier)
    assert provider_shell.eventFilter(provider_shell.navigation, fullscreen)
    assert provider_shell.isFullScreen()
    escape = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
    assert provider_shell.eventFilter(provider_shell.navigation, escape)
    assert not provider_shell.isFullScreen()
    enter = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)
    assert provider_shell.eventFilter(provider_shell.channel_list, enter)
    await asyncio.sleep(0)

    print(f"records={N}")
    print("stale_identity=PASS")
    print("legacy_dialog_stale_identity=PASS")
    print("async_error_cleanup=PASS")
    print("stale_request_protection=PASS")
    print("provider_selection=PASS")
    print("selection_without_playback=PASS")
    print("local_category_filtering=PASS")
    print("capability_navigation=PASS")
    print("content_identity_and_local_search=PASS")
    print("content_stale_provider_protection=PASS")
    print("keyboard_accessibility=PASS")
    print("player_shell_native_probe=PASS")
    app.quit()


if __name__ == "__main__":
    asyncio.run(main())
