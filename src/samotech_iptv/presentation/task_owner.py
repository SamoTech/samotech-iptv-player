"""Explicit ownership for asynchronous Qt presentation tasks."""

from __future__ import annotations

import asyncio
import inspect
import logging
import weakref
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Awaitable

__all__ = ["cancel_owned_tasks", "close_all_task_owners", "create_owned_task"]

_LOG = logging.getLogger(__name__)
_OWNERS: weakref.WeakSet[_TaskOwner] = weakref.WeakSet()
_OWNER_BY_OBJECT: weakref.WeakKeyDictionary[object, _TaskOwner] = weakref.WeakKeyDictionary()


class _TaskOwner:
    """Own tasks for one Qt object and cancel them on close, destruction, or shutdown."""

    def __init__(self, owner: object) -> None:
        self._owner_ref = weakref.ref(owner)
        self._tasks: set[asyncio.Task[Any]] = set()
        self._closed = False
        destroyed = getattr(owner, "destroyed", None)
        if destroyed is not None:
            destroyed.connect(self.cancel_now)
        _install_close_filter(owner, self)
        _OWNERS.add(self)

    def eventFilter(self, watched: object, event: object) -> bool:  # noqa: N802
        event_type_getter = getattr(event, "type", None)
        event_type = event_type_getter() if callable(event_type_getter) else None
        is_close = getattr(event_type, "name", None) == "Close" or event_type == 19
        if watched is self._owner_ref() and is_close:
            self.cancel_now()
        return False

    def create(self, awaitable: Awaitable[Any]) -> asyncio.Task[Any] | None:
        if self._closed:
            if inspect.iscoroutine(awaitable):
                awaitable.close()
            elif isinstance(awaitable, asyncio.Future):
                awaitable.cancel()
            else:
                asyncio.ensure_future(awaitable).cancel()
            return None
        task = asyncio.ensure_future(awaitable)
        self._tasks.add(task)
        task.add_done_callback(self._discard)
        task.add_done_callback(self._consume_failure)
        return task

    def cancel_pending(self) -> None:
        """Cancel current work while keeping this owner available for new requests."""
        for task in tuple(self._tasks):
            if not task.done():
                task.cancel()

    def cancel_now(self) -> None:
        """Cancel immediately and prevent new work after close or destruction."""
        self._closed = True
        self.cancel_pending()

    async def close(self) -> None:
        """Cancel and await every task currently owned by this object."""
        self.cancel_now()
        tasks = tuple(self._tasks)
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self._tasks.clear()

    def _discard(self, task: asyncio.Task[Any]) -> None:
        self._tasks.discard(task)

    @staticmethod
    def _consume_failure(task: asyncio.Task[Any]) -> None:
        if task.cancelled():
            return
        try:
            exception = task.exception()
        except asyncio.CancelledError:
            return
        if exception is not None:
            _LOG.error(
                "Owned presentation task failed type=%s",
                type(exception).__name__,
            )


def _install_close_filter(owner: object, task_owner: _TaskOwner) -> None:
    """Install a real Qt close filter only when the real Qt runtime is available."""
    try:
        from PySide6.QtCore import QObject as QtObject
    except ImportError:
        return
    if not isinstance(owner, QtObject):
        return

    class CloseEventFilter(QtObject):
        def __init__(self, parent: QtObject) -> None:
            super().__init__(parent)

        def eventFilter(self, watched: object, event: object) -> bool:  # noqa: N802
            return task_owner.eventFilter(watched, event)

    owner.installEventFilter(CloseEventFilter(owner))


def _owner_for(owner: object) -> _TaskOwner:
    current = _OWNER_BY_OBJECT.get(owner)
    if current is not None:
        return current
    current = _TaskOwner(owner)
    _OWNER_BY_OBJECT[owner] = current
    return current


def create_owned_task(owner: object, awaitable: Awaitable[Any]) -> asyncio.Task[Any] | None:
    """Create a task that belongs to the supplied Qt owner."""
    return _owner_for(owner).create(awaitable)


def cancel_owned_tasks(owner: object) -> None:
    """Synchronously cancel tasks owned by one Qt object."""
    current = _OWNER_BY_OBJECT.get(owner)
    if current is not None:
        current.cancel_pending()


async def close_all_task_owners() -> None:
    """Await cancellation of every live presentation owner during app shutdown."""
    owners = tuple(_OWNERS)
    if owners:
        await asyncio.gather(*(owner.close() for owner in owners), return_exceptions=True)
