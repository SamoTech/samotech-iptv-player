"""EPG DTOs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Sequence

__all__ = ["EPGEntryDTO", "LoadEPGRequest", "LoadEPGResponse"]


@dataclass(frozen=True)
class EPGEntryDTO:
    id: str
    channel_id: str
    title: str
    start: str  # ISO-8601
    end: str    # ISO-8601
    description: Optional[str] = None


@dataclass(frozen=True)
class LoadEPGRequest:
    channel_id: str
    limit: int = 48


@dataclass(frozen=True)
class LoadEPGResponse:
    entries: Sequence[EPGEntryDTO] = field(default_factory=list)
    error: Optional[str] = None
