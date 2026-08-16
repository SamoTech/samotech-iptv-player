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
from samotech_iptv.application.dtos.playback import PlaybackOutcome
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
        self.started = asyncio.Event()
        self.release = asyncio.Event()
        self.wait_for_release = False

    async def execute(self, _: object) -> LoadChannelsResponse:
        self.started.set()
        if self.wait_for_release:
            await self.release.wait()
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
    def __init__(
        self,
        categories: tuple[CategoryDTO, ...],
        categories_by_provider: dict[str, tuple[CategoryDTO, ...]] | None = None,
    ) -> None:
        self.categories = categories
        self.categories_by_provider = categories_by_provider or {}
        self.started = asyncio.Event()
        self.release = asyncio.Event()
        self.wait_for_release = False
        self.waiting_provider_id: str | None = None

    async def execute(self, request: object) -> LoadCategoriesResponse:
        self.started.set()
        if self.wait_for_release and (
            self.waiting_provider_id is None or request.provider_id == self.waiting_provider_id
        ):
            await self.release.wait()
        return LoadCategoriesResponse(
            categories=self.categories_by_provider.get(request.provider_id, self.categories)
        )


class FakeContent:
    def __init__(self, items: dict[ContentType, tuple[ContentItemDTO, ...]]) -> None:
        self.items = items
        self.calls: list[ContentType] = []
        self.started = asyncio.Event()
        self.release = asyncio.Event()
        self.wait_for_release = False

    async def execute(self, request: object) -> BrowseContentResponse:
        content_type = request.content_type
        self.calls.append(content_type)
        self.started.set()
        if self.wait_for_release:
            await self.release.wait()
        items = self.items.get(content_type, ())
        return BrowseContentResponse(items=items, total=len(items))


class FakeCapabilities:
    def __init__(self, capabilities: ProviderCapabilities) -> None:
        self.capabilities = capabilities
        self.provider_ids: list[str] = []

    def execute(self, provider_id: str) -> ProviderCapabilities:
        self.provider_ids.append(provider_id)
        return self.capabilities


class FakeMovieDetails:
    def __init__(self, item: ContentItemDTO) -> None:
        self.item = item

    async def execute(self, _: object) -> SimpleNamespace:
        return SimpleNamespace(item=self.item, error=None, unsupported=False)


class FakeSeriesSeasons:
    async def execute(self, request: object) -> SimpleNamespace:
        return SimpleNamespace(
            seasons=(
                SimpleNamespace(
                    id=f"{request.series_id}:season:1",
                    provider_id=request.provider_id,
                    series_id=request.series_id,
                    number=1,
                    title="Season One",
                ),
            ),
            error=None,
            unsupported=False,
        )


class FakeSeasonEpisodes:
    async def execute(self, request: object) -> SimpleNamespace:
        return SimpleNamespace(
            episodes=(
                SimpleNamespace(
                    id=f"{request.series_id}:episode:501",
                    provider_id=request.provider_id,
                    series_id=request.series_id,
                    season=request.season,
                    episode_number=1,
                    title="Pilot",
                    resource_id="501|mp4",
                    duration_seconds=1200,
                    plot="Episode metadata",
                ),
            ),
            error=None,
            unsupported=False,
        )


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
    movie_details: FakeMovieDetails | None = None,
    series_seasons: FakeSeriesSeasons | None = None,
    season_episodes: FakeSeasonEpisodes | None = None,
    invalidate_pending_playback: object | None = None,
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
        load_movie_details=movie_details,  # type: ignore[arg-type]
        load_series_seasons=series_seasons,  # type: ignore[arg-type]
        load_season_episodes=season_episodes,  # type: ignore[arg-type]
        invalidate_pending_playback=invalidate_pending_playback,  # type: ignore[arg-type]
    )


async def main() -> None:
    app = QApplication.instance() or QApplication([])
    a, b, c = (
        make_channel("A", "news", 1),
        make_channel("B", "sports", 2),
        make_channel("C", "news", 3),
    )
    played: list[str] = []

    async def play(target: object) -> SimpleNamespace:
        played.append(target.canonical_content_id)  # type: ignore[union-attr]
        return SimpleNamespace(outcome=PlaybackOutcome.PLAYED, error=None)

    async def legacy_play(_: str, channel_id: str) -> None:
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
        FakeBrowse(), legacy_play, FakeSearch(), legacy_favorite  # type: ignore[arg-type]
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

    invalidations = 0

    def invalidate_pending_playback() -> None:
        nonlocal invalidations
        invalidations += 1

    switching_shell = make_shell(
        FakeBrowse(),
        FakeSearch(),
        FakeFavorite(),
        play,
        invalidate_pending_playback=invalidate_pending_playback,
    )
    switching_shell.provider_selector.setEditText("provider-a")
    switching_shell._provider_changed(0)
    switching_shell.provider_selector.setEditText("provider-b")
    switching_shell._provider_changed(0)
    assert invalidations == 2

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

    live_only_shell = make_shell(
        FakeBrowse(),
        FakeSearch(),
        FakeFavorite(),
        play,
        capabilities=FakeCapabilities(ProviderCapabilities(live_tv=True)),
    )
    live_only_shell.provider_selector.setEditText("provider-a")
    await live_only_shell.refresh_provider_capabilities("provider-a")
    assert "Live TV" in live_only_shell.navigation_model.stringList()
    assert "Movies" not in live_only_shell.navigation_model.stringList()
    assert "Series" not in live_only_shell.navigation_model.stringList()

    stale_live_browse = FakeBrowse()
    stale_live_browse.response = LoadChannelsResponse(channels=(old,), total=1)
    stale_live_browse.wait_for_release = True
    stale_live_shell = make_shell(stale_live_browse, FakeSearch(), FakeFavorite(), play)
    stale_live_shell.provider_selector.setEditText("provider-a")
    stale_live_load = asyncio.create_task(stale_live_shell.load_channels())
    await stale_live_browse.started.wait()
    stale_live_shell.provider_selector.setEditText("provider-b")
    stale_live_shell._provider_changed(0)
    stale_live_browse.release.set()
    await stale_live_load
    assert stale_live_shell.channel_model.rowCount() == 0

    provider_categories = FakeCategories(
        (),
        {
            "provider-a": (CategoryDTO("a", "Provider A", "provider-a"),),
            "provider-b": (CategoryDTO("b", "Provider B", "provider-b"),),
        },
    )
    provider_categories.wait_for_release = True
    provider_categories.waiting_provider_id = "provider-a"
    stale_category_shell = make_shell(
        FakeBrowse(), FakeSearch(), FakeFavorite(), play, categories=provider_categories
    )
    stale_category_shell.provider_selector.setEditText("provider-a")
    stale_category_load = asyncio.create_task(stale_category_shell.refresh_categories("provider-a"))
    await provider_categories.started.wait()
    stale_category_shell.provider_selector.setEditText("provider-b")
    stale_category_shell._provider_changed(0)
    await asyncio.sleep(0)
    provider_categories.release.set()
    await stale_category_load
    await asyncio.sleep(0)
    assert stale_category_shell.category_selector.itemText(1) == "Provider B"

    movie = ContentItemDTO(
        id="movie-1",
        provider_id="provider-a",
        content_type=ContentType.MOVIE,
        title="Arena Film",
        stream_id="movie-stream-1|mp4",
        category_id="sports",
        year=2024,
        rating=8.2,
        plot="A safe metadata fixture.",
        genre="Drama",
        duration_seconds=5400,
        director="Example Director",
        cast="Example Cast",
        country="Synthetic",
        release_date="2024-01-02",
        poster_url="https://assets.example.test/movie.jpg",
        backdrop_url="https://assets.example.test/backdrop.jpg",
        container_extension="mp4",
    )
    newer_movie = ContentItemDTO(
        id="movie-2",
        provider_id="provider-a",
        content_type=ContentType.MOVIE,
        title="Beta Film",
        stream_id="movie-stream-2|mp4",
        category_id="sports",
        year=2025,
        rating=8.9,
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
        movie_details=FakeMovieDetails(movie),
        series_seasons=FakeSeriesSeasons(),
        season_episodes=FakeSeasonEpisodes(),
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
        "Search",
        "Providers",
        "Settings",
    ]
    content_shell._active_content_type = ContentType.MOVIE
    await content_shell.load_content(ContentType.MOVIE)
    assert content_shell.content_model.rowCount() == 1
    assert content_shell.content_model.item_at(0) is movie
    movie_list = content_shell._content_lists[ContentType.MOVIE]
    assert movie_list.viewMode().name == "IconMode"
    content_shell._content_catalogues[ContentType.MOVIE] = (movie, newer_movie)
    content_shell._content_sort_selectors[ContentType.MOVIE].setCurrentIndex(2)
    assert content_shell.content_model.item_at(0) is newer_movie
    content_shell._content_sort_selectors[ContentType.MOVIE].setCurrentIndex(0)
    assert movie_list.gridSize().width() == 172
    assert content_shell.sidebar_toggle.text() == "Menu"
    assert content_shell._player_overlay is not None
    content_shell._set_status_text("● Playing")
    assert content_shell.overlay_status.text() == "● Playing"
    content_shell._toggle_sidebar()
    assert content_shell.sidebar_toggle.text() == "☰"
    content_shell._toggle_sidebar()
    content_shell._select_content_index(ContentType.MOVIE, content_shell.content_model.index(0, 0))
    assert content_shell.selected_content is movie
    detail_text = content_shell._content_detail_labels[ContentType.MOVIE].text()
    assert "Movie · Arena Film" in detail_text
    assert "2024 · ★ 8.2 · Drama · 1h 30m · MP4" in detail_text
    assert "Example Director · Example Cast · Synthetic · 2024-01-02" in detail_text
    assert "Artwork available" in detail_text
    assert played == ["b", "b"]
    content_shell._navigate_to_page(6)
    content_shell.search_input.setText("2024")
    assert content_shell.global_search_model.stringList() == ["MOVIES  ·  Arena Film"]
    assert content_shell.global_search_status.text() == "1 loaded result(s)"
    content_shell._navigate_to_page(2)
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
    await asyncio.sleep(0)
    assert "Playing" in content_shell._content_detail_labels[ContentType.MOVIE].text()
    assert played == ["b", "b", "movie-1"]

    content_shell._active_content_type = ContentType.SERIES
    content_shell.search_input.clear()
    await content_shell.load_content(ContentType.SERIES)
    series_index = content_shell.content_model.index(0, 0)
    content_shell._content_lists[ContentType.SERIES].setCurrentIndex(series_index)
    content_shell._activate_content_index(ContentType.SERIES, series_index)
    await asyncio.sleep(0)
    assert content_shell._series_view_mode == "seasons"
    season_index = content_shell.content_model.index(0, 0)
    content_shell._activate_content_index(ContentType.SERIES, season_index)
    await asyncio.sleep(0)
    assert content_shell._series_view_mode == "episodes"
    episode_index = content_shell.content_model.index(0, 0)
    content_shell._activate_content_index(ContentType.SERIES, episode_index)
    await asyncio.sleep(0)
    await asyncio.sleep(0)
    assert played == ["b", "b", "movie-1", "series-1:episode:501"]

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

    stale_series_content = FakeContent({ContentType.SERIES: (series,)})
    stale_series_content.wait_for_release = True
    stale_series_shell = make_shell(
        FakeBrowse(),
        FakeSearch(),
        FakeFavorite(),
        play,
        content=stale_series_content,
    )
    stale_series_shell.provider_selector.setEditText("provider-a")
    stale_series_load = asyncio.create_task(stale_series_shell.load_content(ContentType.SERIES))
    await stale_series_content.started.wait()
    stale_series_shell.provider_selector.setEditText("provider-b")
    stale_series_shell._provider_changed(0)
    stale_series_content.release.set()
    await stale_series_load
    assert ContentType.SERIES not in stale_series_shell._content_catalogues
    assert stale_series_shell.content_model.rowCount() == 0

    stale_provider_search = FakeSearch()
    stale_provider_search.response = SearchChannelsResponse(channels=(old,), total=1)
    stale_provider_search.wait_for_release = True
    stale_search_shell = make_shell(FakeBrowse(), stale_provider_search, FakeFavorite(), play)
    stale_search_shell.provider_selector.setEditText("provider-a")
    stale_search_shell.search_input.setText("old")
    stale_search_load = asyncio.create_task(stale_search_shell.search_channels())
    await stale_provider_search.started.wait()
    stale_search_shell.provider_selector.setEditText("provider-b")
    stale_search_shell._provider_changed(0)
    stale_provider_search.release.set()
    await stale_search_load
    assert stale_search_shell.channel_model.rowCount() == 0

    playback_started = asyncio.Event()
    playback_release = asyncio.Event()

    async def delayed_play(_: object) -> SimpleNamespace:
        playback_started.set()
        await playback_release.wait()
        return SimpleNamespace(outcome=PlaybackOutcome.PLAYED, error=None)

    stale_playback_shell = make_shell(FakeBrowse(), FakeSearch(), FakeFavorite(), delayed_play)
    stale_playback_shell.provider_selector.setEditText("provider-a")
    stale_playback_shell._render_channels((a,))
    stale_playback = asyncio.create_task(stale_playback_shell.play_channel(a))
    await playback_started.wait()
    stale_playback_shell.provider_selector.setEditText("provider-b")
    stale_playback_shell._provider_changed(0)
    playback_release.set()
    await stale_playback
    assert stale_playback_shell.playing_channel is None
    assert stale_playback_shell.loading_channel is None
    assert stale_playback_shell.playback_error_channel is None

    async def stale_result_play(_: object) -> SimpleNamespace:
        return SimpleNamespace(outcome=PlaybackOutcome.STALE, error=None)

    stale_result_shell = make_shell(FakeBrowse(), FakeSearch(), FakeFavorite(), stale_result_play)
    stale_result_shell.provider_selector.setEditText("provider-a")
    stale_result_shell._render_channels((a,))
    await stale_result_shell.play_channel(a)
    assert stale_result_shell.selected_channel is a
    assert stale_result_shell.playing_channel is None
    assert stale_result_shell.playback_error_channel is None
    assert "Playback error" not in stale_result_shell.status_label.text()

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
    print("playback_attempt_invalidation=PASS")
    print("selection_without_playback=PASS")
    print("local_category_filtering=PASS")
    print("capability_navigation=PASS")
    print("content_identity_and_local_search=PASS")
    print("content_stale_provider_protection=PASS")
    print("series_and_search_stale_provider_protection=PASS")
    print("playback_stale_provider_protection=PASS")
    print("playback_stale_result_protection=PASS")
    print("keyboard_accessibility=PASS")
    print("player_shell_native_probe=PASS")
    app.quit()


if __name__ == "__main__":
    asyncio.run(main())
