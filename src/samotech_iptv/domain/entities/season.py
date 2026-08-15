from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from samotech_iptv.core.exceptions import ValidationError

from ._catalogue_validation import validate_nonblank_text

if TYPE_CHECKING:
    from samotech_iptv.domain.value_objects.provider_id import ProviderId

__all__ = ["Season"]


@dataclass(frozen=True)
class Season:
    """A provider-scoped season belonging to one canonical series."""

    id: str
    series_id: str
    provider_id: ProviderId
    number: int
    title: str | None = None

    def __post_init__(self) -> None:
        validate_nonblank_text(self.id, field="id", label="Season ID")
        validate_nonblank_text(self.series_id, field="series_id", label="Series ID")
        if self.number < 1:
            raise ValidationError("number", "Season number must be >= 1")
        if self.title is not None:
            validate_nonblank_text(
                self.title,
                field="title",
                label="Season title",
                when_supplied=True,
            )
