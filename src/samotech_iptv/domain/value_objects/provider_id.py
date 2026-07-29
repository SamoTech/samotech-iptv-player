"""ProviderId value object."""
from __future__ import annotations

from dataclasses import dataclass

from samotech_iptv.core.exceptions import ValidationError

__all__ = ["ProviderId"]


@dataclass(frozen=True)
class ProviderId:
    """Opaque identifier for a provider instance."""

    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValidationError("value", "ProviderId must not be blank")

    def __str__(self) -> str:
        return self.value
