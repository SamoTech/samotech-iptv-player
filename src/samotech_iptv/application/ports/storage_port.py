"""StoragePort — local persistence adapter contract."""
from __future__ import annotations

from abc import ABC, abstractmethod

__all__ = ["StoragePort"]


class StoragePort(ABC):
    """Contract for the local persistence adapter (SQLite, JSON, …)."""

    @abstractmethod
    async def initialise(self) -> None: ...

    @abstractmethod
    async def close(self) -> None: ...
