"""Stream resolution DTOs."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

__all__ = ["ResolveStreamRequest", "ResolveStreamResponse"]


@dataclass(frozen=True)
class ResolveStreamRequest:
    channel_id: str
    provider_id: str


@dataclass(frozen=True)
class ResolveStreamResponse:
    url: Optional[str] = None
    error: Optional[str] = None
