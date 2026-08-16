"""Deterministic tests for explicit Qt-owned asynchronous task lifecycle."""

from __future__ import annotations

import asyncio

import pytest

from samotech_iptv.presentation.task_owner import (
    _owner_for,
    close_all_task_owners,
    create_owned_task,
)


class _FakeOwner:
    """Weak-referenceable QObject-shaped owner for lifecycle tests."""

    destroyed = None

    def deleteLater(self) -> None:  # noqa: N802
        pass


class _CloseEvent:
    def type(self) -> int:
        return 19


def _dispose(owner: _FakeOwner) -> None:
    owner.deleteLater()


async def _blocked_operation(
    label: str,
    gate: asyncio.Event,
    state: list[str],
    generation: int,
    current_generation: list[int],
) -> None:
    try:
        await gate.wait()
    except asyncio.CancelledError:
        state.append(f"cancelled:{label}")
        raise
    if generation == current_generation[0]:
        state.append(label)


async def _run_provider_replacement_case(operation: str) -> tuple[list[str], asyncio.Task[None]]:
    owner = _FakeOwner()
    state: list[str] = []
    current_generation = [1]
    first_gate = asyncio.Event()
    second_gate = asyncio.Event()
    first = create_owned_task(
        owner,
        _blocked_operation(operation + ":A", first_gate, state, 1, current_generation),
    )
    assert first is not None
    await asyncio.sleep(0)
    current_generation[0] = 2
    first.cancel()
    second = create_owned_task(
        owner,
        _blocked_operation(operation + ":B", second_gate, state, 2, current_generation),
    )
    assert second is not None
    second_gate.set()
    await second
    await asyncio.gather(first, return_exceptions=True)
    await close_all_task_owners()
    _dispose(owner)
    return state, first


@pytest.mark.asyncio
async def test_provider_a_to_b_catalogue_cancels_a_and_keeps_b() -> None:
    state, first = await _run_provider_replacement_case("catalogue")
    assert first.cancelled()
    assert state == ["cancelled:catalogue:A", "catalogue:B"]


@pytest.mark.asyncio
async def test_provider_a_to_b_search_cancels_a_and_keeps_b() -> None:
    state, first = await _run_provider_replacement_case("search")
    assert first.cancelled()
    assert state == ["cancelled:search:A", "search:B"]


@pytest.mark.asyncio
async def test_provider_a_to_b_movie_details_cancels_a_and_keeps_b() -> None:
    state, first = await _run_provider_replacement_case("movie-details")
    assert first.cancelled()
    assert state == ["cancelled:movie-details:A", "movie-details:B"]


@pytest.mark.asyncio
async def test_series_a_to_b_seasons_cancels_a_and_keeps_b() -> None:
    state, first = await _run_provider_replacement_case("series-seasons")
    assert first.cancelled()
    assert state == ["cancelled:series-seasons:A", "series-seasons:B"]


@pytest.mark.asyncio
async def test_episode_a_to_b_resolution_cancels_a_and_keeps_b() -> None:
    state, first = await _run_provider_replacement_case("episode-resolution")
    assert first.cancelled()
    assert state == ["cancelled:episode-resolution:A", "episode-resolution:B"]


@pytest.mark.asyncio
async def test_widget_close_cancels_owned_pending_task() -> None:
    owner = _FakeOwner()
    state: list[str] = []
    task = create_owned_task(
        owner,
        _blocked_operation("widget-close", asyncio.Event(), state, 1, [1]),
    )
    assert task is not None
    await asyncio.sleep(0)
    task_owner = _owner_for(owner)
    assert task_owner.eventFilter(owner, _CloseEvent()) is False
    await asyncio.sleep(0)
    await asyncio.gather(task, return_exceptions=True)
    assert task.cancelled()
    assert state == ["cancelled:widget-close"]
    _dispose(owner)


@pytest.mark.asyncio
async def test_application_shutdown_cancels_multiple_owned_tasks() -> None:
    owners = [_FakeOwner(), _FakeOwner()]
    tasks: list[asyncio.Task[None]] = []
    state: list[str] = []
    for index, owner in enumerate(owners):
        task = create_owned_task(
            owner,
            _blocked_operation(f"shutdown-{index}", asyncio.Event(), state, 1, [1]),
        )
        assert task is not None
        tasks.append(task)
    await close_all_task_owners()
    assert all(task.cancelled() for task in tasks)
    assert sorted(state) == ["cancelled:shutdown-0", "cancelled:shutdown-1"]
    assert not [
        task
        for task in asyncio.all_tasks()
        if task is not asyncio.current_task() and not task.done()
    ]
    for owner in owners:
        _dispose(owner)


@pytest.mark.asyncio
async def test_obsolete_task_cancellation_cannot_mutate_ui_state() -> None:
    owner = _FakeOwner()
    state: list[str] = []
    task = create_owned_task(
        owner,
        _blocked_operation("obsolete", asyncio.Event(), state, 1, [2]),
    )
    assert task is not None
    await asyncio.sleep(0)
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)
    assert state == ["cancelled:obsolete"]
    _dispose(owner)


@pytest.mark.asyncio
async def test_stale_generation_completion_cannot_mutate_state() -> None:
    owner = _FakeOwner()
    state: list[str] = []
    gate = asyncio.Event()
    current_generation = [1]
    task = create_owned_task(
        owner,
        _blocked_operation("stale", gate, state, 1, current_generation),
    )
    assert task is not None
    current_generation[0] = 2
    gate.set()
    await task
    assert state == []
    _dispose(owner)


@pytest.mark.asyncio
async def test_provider_runtime_replacement_cancels_pending_owner_task() -> None:
    old_owner = _FakeOwner()
    new_owner = _FakeOwner()
    state: list[str] = []
    old_task = create_owned_task(
        old_owner,
        _blocked_operation("runtime-old", asyncio.Event(), state, 1, [1]),
    )
    new_task = create_owned_task(
        new_owner,
        _blocked_operation("runtime-new", asyncio.Event(), state, 2, [2]),
    )
    assert old_task is not None
    assert new_task is not None
    await asyncio.sleep(0)
    old_owner_owner = _owner_for(old_owner)
    assert old_owner_owner.eventFilter(old_owner, _CloseEvent()) is False
    await asyncio.sleep(0)
    await asyncio.gather(old_task, return_exceptions=True)
    new_task.cancel()
    await asyncio.gather(new_task, return_exceptions=True)
    assert old_task.cancelled()
    assert new_task.cancelled()
    assert state == ["cancelled:runtime-old", "cancelled:runtime-new"]
    _dispose(old_owner)
    _dispose(new_owner)
