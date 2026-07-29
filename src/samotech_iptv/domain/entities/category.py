"""Category entity — a grouping of channels or VOD content."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from samotech_iptv.core.exceptions import ValidationError
from samotech_iptv.domain.value_objects.provider_id import ProviderId

__all__ = ["Category"]


@dataclass(frozen=True)
class Category:
    """A grouping of channels or VOD content from a provider."""

    id: str
    name: str
    provider_id: ProviderId
    parent_id: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValidationError("name", "Category name must not be blank")
