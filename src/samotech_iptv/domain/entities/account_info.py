"""AccountInfo — provider-neutral non-secret account status."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from samotech_iptv.core.exceptions import ValidationError

from ._catalogue_validation import validate_nonblank_text

if TYPE_CHECKING:
    from datetime import datetime

    from samotech_iptv.domain.value_objects.provider_id import ProviderId

__all__ = ["AccountInfo"]


@dataclass(frozen=True)
class AccountInfo:
    """Optional account status returned by a provider without secret material."""

    provider_id: ProviderId
    status: Literal["active", "expired", "blocked", "unknown"]
    expires_at: datetime | None = None
    active_connections: int | None = None
    max_connections: int | None = None
    message: str | None = None

    def __post_init__(self) -> None:
        if not self.provider_id.value.strip():
            raise ValidationError("provider_id", "must not be blank")
        if self.active_connections is not None and self.active_connections < 0:
            raise ValidationError("active_connections", "must not be negative")
        if self.max_connections is not None and self.max_connections < 0:
            raise ValidationError("max_connections", "must not be negative")
        if self.message is not None:
            validate_nonblank_text(
                self.message,
                field="message",
                label="Account message",
                when_supplied=True,
            )
