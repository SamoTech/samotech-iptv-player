from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest
from PySide6.QtWidgets import QApplication

from samotech_iptv.application.dtos import ContentItemDTO, ContentType, PlaybackOutcome
from tests.player_shell_native_probe import (
    FakeBrowse,
    FakeFavorite,
    FakeSearch,
    make_shell,
    select_provider,
)


@pytest.fixture(scope="module", autouse=True)
def qapplication() -> QApplication:
    return QApplication.instance() or QApplication([])


class DelayedMovieDetails:
    def __init__(self, items: dict[str, ContentItemDTO]) -> None:
        self.items = items
        self.started: dict[str, asyncio.Event] = {key: asyncio.Event() for key in items}
        self.release: dict[str, asyncio.Event] = {key: asyncio.Event() for key in items}

    async def execute(self, request: object) -> SimpleNamespace:
        movie_id = request.movie_id
        self.started[movie_id].set()
        await self.release[movie_id].wait()
        return SimpleNamespace(item=self.items[movie_id], error=None, unsupported=False)


class DelayedSeasons:
    def __init__(self) -> None:
        self.started: dict[str, asyncio.Event] = {}
        self.release: dict[str, asyncio.Event] = {}

    async def execute(self, request: object) -> SimpleNamespace:
        series_id = request.series_id
        self.started.setdefault(series_id, asyncio.Event()).set()
        release = self.release.setdefault(series_id, asyncio.Event())
        await release.wait()
        return SimpleNamespace(
            seasons=(
                SimpleNamespace(
                    id=f"{series_id}:season:1",
                    provider_id=request.provider_id,
                    series_id=series_id,
                    number=1,
                    title=f"{series_id} Season One",
                ),
            ),
            error=None,
            unsupported=False,
        )


class DelayedEpisodes:
    def __init__(self) -> None:
        self.started: dict[int, asyncio.Event] = {}
        self.release: dict[int, asyncio.Event] = {}

    async def execute(self, request: object) -> SimpleNamespace:
        season = request.season
        self.started.setdefault(season, asyncio.Event()).set()
        release = self.release.setdefault(season, asyncio.Event())
        await release.wait()
        return SimpleNamespace(
            episodes=(
                SimpleNamespace(
                    id=f"{request.series_id}:episode:{season}",
                    provider_id=request.provider_id,
                    series_id=request.series_id,
                    season=season,
                    episode_number=1,
                    title=f"Season {season} Episode One",
                    resource_id=f"{season}|mp4",
                    duration_seconds=1200,
                    plot=None,
                ),
            ),
            error=None,
            unsupported=False,
        )


async def _flush() -> None:
    await asyncio.sleep(0)
    await asyncio.sleep(0)


async def _wait_for_key(mapping: dict[object, asyncio.Event], key: object) -> None:
    for _ in range(20):
        if key in mapping:
            return
        await asyncio.sleep(0)
    raise AssertionError(f"request did not start for {key!r}")


def _movie(provider_id: str, movie_id: str, title: str) -> ContentItemDTO:
    return ContentItemDTO(
        id=movie_id,
        provider_id=provider_id,
        content_type=ContentType.MOVIE,
        title=title,
        stream_id="42|mp4",
    )


def _series(provider_id: str, series_id: str, title: str) -> ContentItemDTO:
    return ContentItemDTO(
        id=series_id,
        provider_id=provider_id,
        content_type=ContentType.SERIES,
        title=title,
    )


def _season(provider_id: str, series_id: str, season: int) -> ContentItemDTO:
    return ContentItemDTO(
        id=f"{series_id}:season:{season}",
        provider_id=provider_id,
        content_type=ContentType.SERIES,
        title=f"Season {season}",
        series_id=series_id,
        season=season,
    )


@pytest.mark.asyncio
async def test_old_movie_detail_cannot_mutate_selection_or_start_playback() -> None:
    first = _movie("provider-a", "provider-a:movie-1", "First")
    second = _movie("provider-a", "provider-a:movie-2", "Second")
    details = DelayedMovieDetails({first.id: first, second.id: second})
    played: list[str] = []

    async def play(target: object) -> SimpleNamespace:
        played.append(target.canonical_content_id)  # type: ignore[union-attr]
        return SimpleNamespace(outcome=PlaybackOutcome.PLAYED, error=None)

    shell = make_shell(
        FakeBrowse(),
        FakeSearch(),
        FakeFavorite(),
        play,
        movie_details=details,  # type: ignore[arg-type]
    )
    await select_provider(shell, "provider-a")
    old_task = asyncio.create_task(shell._load_and_play_movie(first))
    await details.started[first.id].wait()
    new_task = asyncio.create_task(shell._load_and_play_movie(second))
    await details.started[second.id].wait()
    details.release[second.id].set()
    await new_task
    details.release[first.id].set()
    await old_task

    assert shell.selected_content is second
    assert played == [second.id]


@pytest.mark.asyncio
async def test_old_series_season_response_cannot_replace_current_series() -> None:
    first = _series("provider-a", "provider-a:series-1", "First series")
    second = _series("provider-a", "provider-a:series-2", "Second series")
    seasons = DelayedSeasons()
    shell = make_shell(
        FakeBrowse(),
        FakeSearch(),
        FakeFavorite(),
        lambda _: asyncio.sleep(0),
        series_seasons=seasons,  # type: ignore[arg-type]
    )
    await select_provider(shell, "provider-a")
    old_task = asyncio.create_task(shell._load_series_seasons_for(first))
    await _wait_for_key(seasons.started, first.id)
    await seasons.started[first.id].wait()
    new_task = asyncio.create_task(shell._load_series_seasons_for(second))
    await _wait_for_key(seasons.started, second.id)
    await seasons.started[second.id].wait()
    seasons.release[second.id].set()
    await new_task
    seasons.release[first.id].set()
    await old_task

    assert shell._series_context_id == second.id
    assert all(item.series_id == second.id for item in shell._series_seasons)


@pytest.mark.asyncio
async def test_old_season_response_cannot_replace_current_episode_list() -> None:
    episodes = DelayedEpisodes()
    shell = make_shell(
        FakeBrowse(),
        FakeSearch(),
        FakeFavorite(),
        lambda _: asyncio.sleep(0),
        season_episodes=episodes,  # type: ignore[arg-type]
    )
    await select_provider(shell, "provider-a")
    first = _season("provider-a", "provider-a:series-1", 1)
    second = _season("provider-a", "provider-a:series-1", 2)
    old_task = asyncio.create_task(shell._load_series_episodes_for(first))
    await _wait_for_key(episodes.started, 1)
    await episodes.started[1].wait()
    new_task = asyncio.create_task(shell._load_series_episodes_for(second))
    await _wait_for_key(episodes.started, 2)
    await episodes.started[2].wait()
    episodes.release[2].set()
    await new_task
    episodes.release[1].set()
    await old_task

    assert shell._series_view_mode == "episodes"
    assert shell._series_episodes[0].season == 2


@pytest.mark.asyncio
async def test_provider_switch_invalidates_inflight_non_live_response() -> None:
    movie = _movie("provider-a", "provider-a:movie-1", "Movie")
    details = DelayedMovieDetails({movie.id: movie})
    played: list[str] = []

    async def play(target: object) -> SimpleNamespace:
        played.append(target.canonical_content_id)  # type: ignore[union-attr]
        return SimpleNamespace(outcome=PlaybackOutcome.PLAYED, error=None)

    shell = make_shell(
        FakeBrowse(),
        FakeSearch(),
        FakeFavorite(),
        play,
        movie_details=details,  # type: ignore[arg-type]
    )
    await select_provider(shell, "provider-a")
    task = asyncio.create_task(shell._load_and_play_movie(movie))
    await details.started[movie.id].wait()
    await select_provider(shell, "provider-b")
    shell._provider_changed(0)
    details.release[movie.id].set()
    await task

    assert shell.selected_content is None
    assert played == []


@pytest.mark.asyncio
async def test_rapid_episode_selection_only_allows_latest_playback() -> None:
    played: list[str] = []
    first_started = asyncio.Event()
    first_release = asyncio.Event()

    async def play(target: object) -> SimpleNamespace:
        content_id = target.canonical_content_id  # type: ignore[union-attr]
        if content_id.endswith(":episode:1"):
            first_started.set()
            await first_release.wait()
        if content_id.endswith(":episode:1"):
            return SimpleNamespace(outcome=PlaybackOutcome.STALE, error=None)
        played.append(content_id)
        return SimpleNamespace(outcome=PlaybackOutcome.PLAYED, error=None)

    shell = make_shell(FakeBrowse(), FakeSearch(), FakeFavorite(), play)
    await select_provider(shell, "provider-a")
    first = ContentItemDTO(
        id="provider-a:series-1:episode:1",
        provider_id="provider-a",
        content_type=ContentType.EPISODE,
        title="Episode One",
        stream_id="1|mp4",
        series_id="provider-a:series-1",
        season=1,
        episode_number=1,
    )
    second = ContentItemDTO(
        id="provider-a:series-1:episode:2",
        provider_id="provider-a",
        content_type=ContentType.EPISODE,
        title="Episode Two",
        stream_id="2|mp4",
        series_id="provider-a:series-1",
        season=1,
        episode_number=2,
    )
    old_task = asyncio.create_task(shell._play_content_item(first))
    await first_started.wait()
    new_task = asyncio.create_task(shell._play_content_item(second))
    await new_task
    first_release.set()
    await old_task

    assert played == [second.id]


@pytest.mark.asyncio
async def test_disposed_shell_rejects_late_movie_completion() -> None:
    movie = _movie("provider-a", "provider-a:movie-disposed", "Disposed movie")
    details = DelayedMovieDetails({movie.id: movie})
    played: list[str] = []

    async def play(target: object) -> SimpleNamespace:
        played.append(target.canonical_content_id)  # type: ignore[union-attr]
        return SimpleNamespace(outcome=PlaybackOutcome.PLAYED, error=None)

    shell = make_shell(
        FakeBrowse(),
        FakeSearch(),
        FakeFavorite(),
        play,
        movie_details=details,  # type: ignore[arg-type]
    )
    await select_provider(shell, "provider-a")
    task = asyncio.create_task(shell._load_and_play_movie(movie))
    await details.started[movie.id].wait()
    shell._disposed = True
    shell._invalidate_non_live_requests()
    details.release[movie.id].set()
    await task

    assert shell.selected_content is None
    assert played == []


@pytest.mark.asyncio
async def test_navigation_away_rejects_late_movie_completion() -> None:
    movie = _movie("provider-a", "provider-a:movie-navigation", "Navigation movie")
    details = DelayedMovieDetails({movie.id: movie})
    played: list[str] = []

    async def play(target: object) -> SimpleNamespace:
        played.append(target.canonical_content_id)  # type: ignore[union-attr]
        return SimpleNamespace(outcome=PlaybackOutcome.PLAYED, error=None)

    shell = make_shell(
        FakeBrowse(),
        FakeSearch(),
        FakeFavorite(),
        play,
        movie_details=details,  # type: ignore[arg-type]
    )
    await select_provider(shell, "provider-a")
    task = asyncio.create_task(shell._load_and_play_movie(movie))
    await details.started[movie.id].wait()
    shell._change_page(0)
    details.release[movie.id].set()
    await task

    assert shell.selected_content is None
    assert played == []
