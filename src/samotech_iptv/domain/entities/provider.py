"""Provider entity — metadata describing a registered content provider."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ._catalogue_validation import validate_nonblank_text

if TYPE_CHECKING:
    from samotech_iptv.domain.value_objects.provider_id import ProviderId
    from samotech_iptv.domain.value_objects.url import URL

__all__ = ["Provider"]


@dataclass(frozen=True)
class Provider:
    """Metadata describing a registered content provider."""

    id: ProviderId
    name: str
    type: str
    base_url: URL
    is_active: bool = True
    capabilities: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        validate_nonblank_text(self.name, field="name", label="Provider name")
        validate_nonblank_text(self.type, field="type", label="Provider type")
