"""History DTOs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = ["HistoryItemDTO", "LoadHistoryRequest", "LoadHistoryResponse"]


@dataclass(frozen=True)
class HistoryItemDTO:
    id: str
    item_id: str
    item_type: str
    watched_at: str  # ISO-8601
    duration_seconds: int = 0


@dataclass(frozen=True)
class LoadHistoryRequest:
    limit: int = 50


@dataclass(frozen=True)
class LoadHistoryResponse:
    items: Sequence[HistoryItemDTO] = field(default_factory=list)
    error: str | None = None
