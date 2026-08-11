"""Stream resolution DTOs."""
from __future__ import annotations

from dataclasses import dataclass

__all__ = ["ResolveStreamRequest", "ResolveStreamResponse"]


@dataclass(frozen=True)
class ResolveStreamRequest:
    channel_id: str
    provider_id: str


@dataclass(frozen=True)
class ResolveStreamResponse:
    url: str | None = None
    error: str | None = None
