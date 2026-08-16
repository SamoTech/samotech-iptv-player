"""ServerInfo — provider-neutral non-secret server metadata."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from samotech_iptv.core.exceptions import ValidationError

from ._catalogue_validation import validate_nonblank_text

if TYPE_CHECKING:
    from samotech_iptv.domain.value_objects.provider_id import ProviderId

__all__ = ["ServerInfo"]


@dataclass(frozen=True)
class ServerInfo:
    """Optional server metadata; credential-bearing URLs are deliberately excluded."""

    provider_id: ProviderId
    name: str | None = None
    version: str | None = None
    timezone: str | None = None
    protocol: str | None = None

    def __post_init__(self) -> None:
        if not self.provider_id.value.strip():
            raise ValidationError("provider_id", "must not be blank")
        for field_name, value in (
            ("name", self.name),
            ("version", self.version),
            ("timezone", self.timezone),
            ("protocol", self.protocol),
        ):
            if value is not None:
                validate_nonblank_text(
                    value,
                    field=field_name,
                    label=field_name,
                    when_supplied=True,
                )
