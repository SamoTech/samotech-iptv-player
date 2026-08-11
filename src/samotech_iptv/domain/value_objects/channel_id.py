"""ChannelId value object."""

from __future__ import annotations

from dataclasses import dataclass

from samotech_iptv.core.exceptions import ValidationError

__all__ = ["ChannelId"]


@dataclass(frozen=True)
class ChannelId:
    """Opaque identifier for a channel."""

    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValidationError("value", "ChannelId must not be blank")

    def __str__(self) -> str:
        return self.value
