"""ProviderSession — safe runtime session state without secrets or tokens."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from samotech_iptv.core.exceptions import ValidationError

if TYPE_CHECKING:
    from datetime import datetime

    from samotech_iptv.domain.value_objects.provider_id import ProviderId

__all__ = ["ProviderSession"]


@dataclass(frozen=True)
class ProviderSession:
    """Normalized provider session status; credentials and tokens never belong here."""

    provider_id: ProviderId
    state: Literal["no_session", "authenticating", "authenticated", "expired", "failed"]
    established_at: datetime | None = None
    expires_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.provider_id.value.strip():
            raise ValidationError("provider_id", "must not be blank")
        if self.established_at is None and self.expires_at is not None:
            raise ValidationError("expires_at", "requires established_at when supplied")
        if (
            self.established_at is not None
            and self.expires_at is not None
            and self.expires_at <= self.established_at
        ):
            raise ValidationError("expires_at", "must be after established_at")
