"""Channel DTOs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Sequence

__all__ = ["ChannelDTO", "LoadChannelsRequest", "LoadChannelsResponse"]


@dataclass(frozen=True)
class ChannelDTO:
    id: str
    name: str
    provider_id: str
    stream_id: str
    category_id: Optional[str] = None
    logo_url: Optional[str] = None
    number: Optional[int] = None


@dataclass(frozen=True)
class LoadChannelsRequest:
    provider_id: str
    category_id: Optional[str] = None


@dataclass(frozen=True)
class LoadChannelsResponse:
    channels: Sequence[ChannelDTO] = field(default_factory=list)
    total: int = 0
    error: Optional[str] = None
