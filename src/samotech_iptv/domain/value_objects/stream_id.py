"""StreamId value object."""

from __future__ import annotations

from dataclasses import dataclass

from samotech_iptv.core.exceptions import ValidationError

__all__ = ["StreamId"]


@dataclass(frozen=True)
class StreamId:
    """Opaque identifier for a stream."""

    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValidationError("value", "StreamId must not be blank")

    def __str__(self) -> str:
        return self.value
