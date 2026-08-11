"""NotificationPort — user-facing notification contract."""

from __future__ import annotations

from abc import ABC, abstractmethod

__all__ = ["NotificationPort"]


class NotificationPort(ABC):
    """Contract for user-facing notifications (toast, tray, …)."""

    @abstractmethod
    async def info(self, title: str, message: str) -> None: ...

    @abstractmethod
    async def warning(self, title: str, message: str) -> None: ...

    @abstractmethod
    async def error(self, title: str, message: str) -> None: ...
