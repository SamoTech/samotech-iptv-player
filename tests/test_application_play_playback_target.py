from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from samotech_iptv.application.dtos import ContentType
from samotech_iptv.application.dtos.playback import (
    PlaybackOutcome,
    PlaybackTarget,
    ResolvedPlayback,
)
from samotech_iptv.application.ports.player_port import PlayerPort
from samotech_iptv.application.ports.provider_capabilities import (
    EpisodePlaybackProvider,
    MoviePlaybackProvider,
    PlaybackProvider,
)
from samotech_iptv.application.ports.provider_resolver_port import ProviderResolverPort
from samotech_iptv.application.use_cases.play_playback_target import (
    PlaybackAttemptRegistry,
    PlayPlaybackTarget,
)
from samotech_iptv.core.exceptions import ProviderError, ValidationError
from samotech_iptv.domain.entities.history import History
from samotech_iptv.domain.value_objects.url import URL

if TYPE_CHECKING:
    from samotech_iptv.application.dtos.player import AudioTrack, SubtitleTrack
    from samotech_iptv.application.ports.provider_capabilities import CategoryProvider
    from samotech_iptv.domain.value_objects.channel_id import ChannelId


class ControlledPlaybackProvider(PlaybackProvider):
    """Provider double whose per-channel resolution order is explicitly controlled."""

    def __init__(self) -> None:
        self.channel_ids: list[str] = []
        self._futures: dict[str, asyncio.Future[URL]] = {}

    def pending(self, channel_id: str) -> asyncio.Future[URL]:
        future = asyncio.get_running_loop().create_future()
        self._futures[channel_id] = future
        return future

    async def resolve_stream(self, channel_id: ChannelId) -> URL:
        self.channel_ids.append(channel_id.value)
        return await self._futures[channel_id.value]


class RecordingPlayer(PlayerPort):
    """Player double retaining only resolved URL values passed to PlayerPort.play."""

    def __init__(self, error: Exception | None = None) -> None:
        self.urls: list[URL] = []
        self.playbacks: list[ResolvedPlayback] = []
        self.seek_calls: list[int] = []
        self._error = error

    async def play(self, playback: ResolvedPlayback) -> None:
        if self._error is not None:
            raise self._error
        self.playbacks.append(playback)
        self.urls.append(playback.url)

    async def stop(self) -> None:
        return None

    async def get_position_ms(self) -> int | None:
        return None

    async def get_duration_ms(self) -> int | None:
        return None

    async def seek_ms(self, position_ms: int) -> None:
        self.seek_calls.append(position_ms)

    async def seek_fraction(self, position: float) -> None:
        return None

    async def get_volume(self) -> int | None:
        return None

    async def set_volume(self, volume: int) -> None:
        return None

    async def is_muted(self) -> bool | None:
        return None

    async def set_muted(self, muted: bool) -> None:
        return None

    async def get_audio_tracks(self) -> tuple[AudioTrack, ...]:
        return ()

    async def select_audio_track(self, track_id: int) -> None:
        return None

    async def get_subtitle_tracks(self) -> tuple[SubtitleTrack, ...]:
        return ()

    async def select_subtitle_track(self, track_id: int | None) -> None:
        return None

    async def restart(self) -> None:
        return None

    async def get_aspect_ratio(self) -> str | None:
        return None

    async def set_aspect_ratio(self, aspect_ratio: str | None) -> None:
        return None

    async def pause(self) -> None:
        return None

    async def resume(self) -> None:
        return None

    async def start_recording(self, destination: object) -> None:
        return None

    async def stop_recording(self) -> None:
        return None

    def attach_video_output(self, native_window_id: int) -> None:
        return None

    @property
    def is_playing(self) -> bool:
        return bool(self.urls)

    @property
    def is_recording(self) -> bool:
        return False


class FixedResolver(ProviderResolverPort):
    """Resolve every requested provider id to the controlled playback provider."""

    def __init__(self, provider: PlaybackProvider) -> None:
        self.provider = provider
        self.provider_ids: list[str] = []

    def resolve_catalog_provider(self, provider_id: str) -> object:
        raise AssertionError(f"Unexpected catalogue resolution for {provider_id}")

    def resolve_category_provider(self, provider_id: str) -> CategoryProvider:
        raise AssertionError(f"Unexpected category resolution for {provider_id}")

    def resolve_playback_provider(self, provider_id: str) -> PlaybackProvider:
        self.provider_ids.append(provider_id)
        return self.provider

    def resolve_movie_playback_provider(self, provider_id: str) -> object:
        raise AssertionError(f"Unexpected movie playback resolution for {provider_id}")

    def resolve_episode_playback_provider(self, provider_id: str) -> object:
        raise AssertionError(f"Unexpected episode playback resolution for {provider_id}")

    def resolve_search_provider(self, provider_id: str) -> object:
        raise AssertionError(f"Unexpected search resolution for {provider_id}")

    def resolve_epg_provider(self, provider_id: str) -> object:
        raise AssertionError(f"Unexpected EPG resolution for {provider_id}")


class RecordingHistory:
    """History double collecting safe channel identity records only."""

    def __init__(self, error: Exception | None = None) -> None:
        self.requests: list[tuple[str, str]] = []
        self._error = error

    async def execute(self, request: object) -> object:
        if self._error is not None:
            raise self._error
        self.requests.append((request.item_id, request.item_type))  # type: ignore[union-attr]
        return object()


class FixedNonLiveProvider(MoviePlaybackProvider, EpisodePlaybackProvider):
    """Provider double returning deterministic URLs for opaque non-live resources."""

    def __init__(self) -> None:
        self.movie_calls: list[tuple[str, str]] = []
        self.episode_calls: list[tuple[str, str]] = []

    async def resolve_movie_stream(self, movie_id: str, resource_id: str) -> URL:
        self.movie_calls.append((movie_id, resource_id))
        return URL("https://example.invalid/movie")

    async def resolve_episode_stream(self, episode_id: str, resource_id: str) -> URL:
        self.episode_calls.append((episode_id, resource_id))
        return URL("https://example.invalid/episode")


class ResumeHistory:
    """Provider-scoped resume repository double."""

    def __init__(self, record: History | None) -> None:
        self.record = record

    async def find_latest(
        self,
        *,
        provider_id: str | None,
        item_id: str,
        item_type: str,
    ) -> History | None:
        if self.record is None:
            return None
        if (
            self.record.provider_id == provider_id
            and self.record.item_id == item_id
            and self.record.item_type == item_type
        ):
            return self.record
        return None


class FixedNonLiveResolver:
    """Resolve one deterministic provider without exposing a production provider."""

    def __init__(self, provider: FixedNonLiveProvider) -> None:
        self.provider = provider
        self.provider_ids: list[str] = []

    def resolve_movie_playback_provider(self, provider_id: str) -> MoviePlaybackProvider:
        self.provider_ids.append(provider_id)
        return self.provider

    def resolve_episode_playback_provider(self, provider_id: str) -> EpisodePlaybackProvider:
        self.provider_ids.append(provider_id)
        return self.provider


def live(channel_id: str, provider_id: str = "provider-a") -> PlaybackTarget:
    """Create a terse, valid Live target for concurrency tests."""
    return PlaybackTarget.live(provider_id, channel_id)


@pytest.mark.parametrize(
    ("kwargs", "field"),
    [
        (
            {
                "provider_id": "",
                "content_type": ContentType.LIVE,
                "canonical_content_id": "a",
                "resource_id": "a",
            },
            "provider_id",
        ),
        (
            {
                "provider_id": "p",
                "content_type": ContentType.LIVE,
                "canonical_content_id": " ",
                "resource_id": "a",
            },
            "canonical_content_id",
        ),
        (
            {"provider_id": "p", "content_type": ContentType.SERIES, "canonical_content_id": "a"},
            "content_type",
        ),
        (
            {"provider_id": "p", "content_type": ContentType.LIVE, "canonical_content_id": "a"},
            "resource_id",
        ),
        (
            {
                "provider_id": "p",
                "content_type": ContentType.LIVE,
                "canonical_content_id": "a",
                "resource_id": "https://example.invalid/live.m3u8",
            },
            "resource_id",
        ),
        (
            {"provider_id": "p", "content_type": ContentType.EPISODE, "canonical_content_id": "e"},
            "parent_series_id",
        ),
        (
            {
                "provider_id": "p",
                "content_type": ContentType.EPISODE,
                "canonical_content_id": "e",
                "parent_series_id": "s",
            },
            "season",
        ),
        (
            {
                "provider_id": "p",
                "content_type": ContentType.EPISODE,
                "canonical_content_id": "e",
                "parent_series_id": "s",
                "season": 1,
            },
            "episode_number",
        ),
    ],
)
def test_playback_target_rejects_incomplete_or_unsupported_identity(
    kwargs: dict[str, object], field: str
) -> None:
    with pytest.raises(ValidationError, match=f"^{field}:"):
        PlaybackTarget(**kwargs)  # type: ignore[arg-type]


def test_live_factory_creates_provider_scoped_immutable_target() -> None:
    target = PlaybackTarget.live("provider-a", "channel-a", "stream-a")

    assert target.provider_id == "provider-a"
    assert target.content_type is ContentType.LIVE
    assert target.canonical_content_id == "channel-a"
    assert target.resource_id == "stream-a"
    with pytest.raises(AttributeError):
        target.provider_id = "other"  # type: ignore[misc]


def test_attempt_registry_monotonically_replaces_and_invalidates_attempts() -> None:
    registry = PlaybackAttemptRegistry()
    first = registry.begin(live("channel-a"))
    second = registry.begin(live("channel-b"))

    assert first.generation == 1
    assert second.generation == 2
    assert not registry.is_current(first)
    assert registry.is_current(second)
    registry.invalidate()
    assert not registry.is_current(second)
    third = registry.begin(live("channel-c"))
    assert third.generation == 4
    assert registry.is_current(third)


@pytest.mark.asyncio
async def test_a_then_b_b_resolves_before_a_only_plays_b() -> None:
    provider = ControlledPlaybackProvider()
    player = RecordingPlayer()
    use_case = PlayPlaybackTarget(FixedResolver(provider), player)
    a_future = provider.pending("a")
    b_future = provider.pending("b")

    a_task = asyncio.create_task(use_case.execute(live("a")))
    await asyncio.sleep(0)
    b_task = asyncio.create_task(use_case.execute(live("b")))
    await asyncio.sleep(0)
    b_url = URL("https://example.invalid/b")
    b_future.set_result(b_url)
    b_result = await b_task
    a_future.set_result(URL("https://example.invalid/a"))
    a_result = await a_task

    assert b_result.outcome is PlaybackOutcome.PLAYED
    assert a_result.outcome is PlaybackOutcome.STALE
    assert player.urls == [b_url]
    assert player.playbacks[0].resource == live("b")


@pytest.mark.asyncio
async def test_a_then_b_a_resolves_before_b_only_plays_b() -> None:
    provider = ControlledPlaybackProvider()
    player = RecordingPlayer()
    use_case = PlayPlaybackTarget(FixedResolver(provider), player)
    a_future = provider.pending("a")
    b_future = provider.pending("b")

    a_task = asyncio.create_task(use_case.execute(live("a")))
    await asyncio.sleep(0)
    b_task = asyncio.create_task(use_case.execute(live("b")))
    await asyncio.sleep(0)
    a_future.set_result(URL("https://example.invalid/a"))
    a_result = await a_task
    b_url = URL("https://example.invalid/b")
    b_future.set_result(b_url)
    b_result = await b_task

    assert a_result.outcome is PlaybackOutcome.STALE
    assert b_result.outcome is PlaybackOutcome.PLAYED
    assert player.urls == [b_url]


@pytest.mark.asyncio
async def test_provider_context_invalidation_discards_late_live_resolution() -> None:
    provider = ControlledPlaybackProvider()
    player = RecordingPlayer()
    use_case = PlayPlaybackTarget(FixedResolver(provider), player)
    a_future = provider.pending("a")

    task = asyncio.create_task(use_case.execute(live("a")))
    await asyncio.sleep(0)
    use_case.attempts.invalidate()
    a_future.set_result(URL("https://example.invalid/a"))
    result = await task

    assert result.outcome is PlaybackOutcome.STALE
    assert player.urls == []


@pytest.mark.asyncio
async def test_single_live_target_resolves_plays_and_records_history() -> None:
    provider = ControlledPlaybackProvider()
    player = RecordingPlayer()
    history = RecordingHistory()
    use_case = PlayPlaybackTarget(FixedResolver(provider), player, history)  # type: ignore[arg-type]
    a_url = URL("https://example.invalid/a")
    provider.pending("a").set_result(a_url)

    result = await use_case.execute(live("a"))

    assert result.outcome is PlaybackOutcome.PLAYED
    assert player.urls == [a_url]
    assert player.playbacks[0].resource == live("a")
    assert history.requests == [("a", "channel")]


@pytest.mark.asyncio
async def test_a_then_b_both_fail_only_latest_attempt_reports_failure() -> None:
    provider = ControlledPlaybackProvider()
    use_case = PlayPlaybackTarget(FixedResolver(provider), RecordingPlayer())
    a_future = provider.pending("a")
    b_future = provider.pending("b")

    a_task = asyncio.create_task(use_case.execute(live("a")))
    await asyncio.sleep(0)
    b_task = asyncio.create_task(use_case.execute(live("b")))
    await asyncio.sleep(0)
    a_future.set_exception(ProviderError("a failed"))
    a_result = await a_task
    b_future.set_exception(ProviderError("b failed"))
    b_result = await b_task

    assert a_result.outcome is PlaybackOutcome.STALE
    assert b_result.outcome is PlaybackOutcome.FAILED
    assert b_result.error == "Unable to start playback"


@pytest.mark.asyncio
async def test_unsupported_movie_target_returns_safe_outcome_without_resolution() -> None:
    provider = ControlledPlaybackProvider()
    resolver = FixedResolver(provider)
    player = RecordingPlayer()
    result = await PlayPlaybackTarget(resolver, player).execute(
        PlaybackTarget("provider-a", ContentType.MOVIE, "movie-a", "movie-stream-a")
    )

    assert result.outcome is PlaybackOutcome.UNSUPPORTED
    assert resolver.provider_ids == []
    assert player.urls == []


@pytest.mark.asyncio
async def test_provider_scoped_resume_restores_vod_position_but_never_live() -> None:
    non_live_provider = FixedNonLiveProvider()
    player = RecordingPlayer()
    resume = ResumeHistory(
        History(
            id="resume-1",
            item_id="movie-a",
            item_type="movie",
            watched_at=datetime.now(UTC),
            provider_id="provider-a",
            duration_seconds=120,
            position_seconds=45,
            watched_percentage=37.5,
        )
    )
    use_case = PlayPlaybackTarget(
        FixedResolver(ControlledPlaybackProvider()),
        player,
        non_live_provider_resolver=FixedNonLiveResolver(non_live_provider),
        history_repository=resume,  # type: ignore[arg-type]
    )

    movie_result = await use_case.execute(PlaybackTarget.movie("provider-a", "movie-a", "42|mp4"))
    live_result = await use_case.execute(live("channel-a"))

    assert movie_result.outcome is PlaybackOutcome.PLAYED
    assert player.seek_calls == [45_000]
    assert live_result.outcome is PlaybackOutcome.FAILED
    assert player.seek_calls == [45_000]


@pytest.mark.asyncio
async def test_movie_and_episode_targets_use_the_single_player_path_and_history() -> None:
    live_provider = ControlledPlaybackProvider()
    non_live_provider = FixedNonLiveProvider()
    non_live_resolver = FixedNonLiveResolver(non_live_provider)
    player = RecordingPlayer()
    history = RecordingHistory()
    use_case = PlayPlaybackTarget(
        FixedResolver(live_provider),
        player,
        history,  # type: ignore[arg-type]
        non_live_provider_resolver=non_live_resolver,  # type: ignore[arg-type]
    )

    movie_result = await use_case.execute(PlaybackTarget.movie("provider-a", "movie-a", "42|mp4"))
    episode_result = await use_case.execute(
        PlaybackTarget.episode("provider-a", "episode-a", "501|mp4", "series-a", 1, 1)
    )

    assert movie_result.outcome is PlaybackOutcome.PLAYED
    assert episode_result.outcome is PlaybackOutcome.PLAYED
    assert non_live_provider.movie_calls == [("movie-a", "42|mp4")]
    assert non_live_provider.episode_calls == [("episode-a", "501|mp4")]
    assert [url.value for url in player.urls] == [
        "https://example.invalid/movie",
        "https://example.invalid/episode",
    ]
    assert [playback.resource for playback in player.playbacks] == [
        PlaybackTarget.movie("provider-a", "movie-a", "42|mp4"),
        PlaybackTarget.episode("provider-a", "episode-a", "501|mp4", "series-a", 1, 1),
    ]
    assert history.requests == [("movie-a", "movie"), ("episode-a", "episode")]


def test_same_provider_different_content_types_have_distinct_identities() -> None:
    live_target = PlaybackTarget.live("provider-a", "shared-id")
    movie_target = PlaybackTarget.movie("provider-a", "shared-id", "movie-resource")

    assert live_target != movie_target
    assert len({live_target, movie_target}) == 2


def test_same_movie_identifier_on_different_providers_has_distinct_identities() -> None:
    provider_a = PlaybackTarget.movie("provider-a", "movie-a", "movie-resource")
    provider_b = PlaybackTarget.movie("provider-b", "movie-a", "movie-resource")

    assert provider_a != provider_b
    assert len({provider_a, provider_b}) == 2


@pytest.mark.asyncio
async def test_player_failure_returns_safe_failed_outcome_without_url_disclosure() -> None:
    provider = ControlledPlaybackProvider()
    resolved_url = URL("https://example.invalid/private-stream")
    provider.pending("a").set_result(resolved_url)

    result = await PlayPlaybackTarget(
        FixedResolver(provider), RecordingPlayer(ProviderError("player failed"))
    ).execute(live("a"))

    assert result.outcome is PlaybackOutcome.FAILED
    assert result.error == "Unable to start playback"
    assert str(resolved_url) not in (result.error or "")


@pytest.mark.asyncio
async def test_history_failure_preserves_existing_legacy_error_semantics() -> None:
    provider = ControlledPlaybackProvider()
    provider.pending("a").set_result(URL("https://example.invalid/a"))
    use_case = PlayPlaybackTarget(
        FixedResolver(provider),
        RecordingPlayer(),
        RecordingHistory(ProviderError("history failed")),  # type: ignore[arg-type]
    )

    with pytest.raises(ProviderError, match="Unable to record playback history"):
        await use_case.execute(live("a"))
