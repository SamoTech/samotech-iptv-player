"""Safe application data-transfer objects for Electronic Programme Guide data."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = [
    "EPGEntryDTO",
    "LoadEPGRequest",
    "LoadEPGResponse",
    "LoadRegisteredEPGRequest",
]


@dataclass(frozen=True)
class EPGEntryDTO:
    """A presentation-safe programme entry with no provider secrets or URLs."""

    id: str
    channel_id: str
    title: str
    start: str  # ISO-8601
    end: str  # ISO-8601
    description: str | None = None


@dataclass(frozen=True)
class LoadEPGRequest:
    """Request programme entries from an already supplied EPG-capable provider."""

    channel_id: str
    limit: int = 48


@dataclass(frozen=True)
class LoadRegisteredEPGRequest:
    """Request programme entries from a provider selected by its safe identifier."""

    provider_id: str
    channel_id: str
    limit: int = 48


@dataclass(frozen=True)
class LoadEPGResponse:
    """Safe programme entries or a user-facing loading error."""

    entries: Sequence[EPGEntryDTO] = field(default_factory=list)
    error: str | None = None
