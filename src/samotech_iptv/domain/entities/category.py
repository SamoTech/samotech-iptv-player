"""Category entity — a grouping of channels or VOD content."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ._catalogue_validation import validate_nonblank_text

if TYPE_CHECKING:
    from samotech_iptv.domain.value_objects.provider_id import ProviderId

__all__ = ["Category"]


@dataclass(frozen=True)
class Category:
    """A grouping of channels or VOD content from a provider."""

    id: str
    name: str
    provider_id: ProviderId
    parent_id: str | None = None

    def __post_init__(self) -> None:
        validate_nonblank_text(self.id, field="id", label="Category ID")
        validate_nonblank_text(self.name, field="name", label="Category name")
        if self.parent_id is not None:
            validate_nonblank_text(
                self.parent_id,
                field="parent_id",
                label="Parent category ID",
                when_supplied=True,
            )
