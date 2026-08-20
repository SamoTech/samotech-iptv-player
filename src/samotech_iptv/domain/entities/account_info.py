"""AccountInfo — provider-neutral non-secret account status."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from math import floor
from typing import TYPE_CHECKING, Literal

from samotech_iptv.core.exceptions import ValidationError

from ._catalogue_validation import validate_nonblank_text

if TYPE_CHECKING:
    from datetime import datetime

    from samotech_iptv.domain.value_objects.provider_id import ProviderId

__all__ = [
    "AccountExpiration",
    "AccountInfo",
    "AccountStatus",
    "SubscriptionStatus",
]


class AccountStatus(StrEnum):
    """Provider-reported account access status; never inferred from playback."""

    ACTIVE = "active"
    EXPIRED = "expired"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


class SubscriptionStatus(StrEnum):
    """Optional provider-reported subscription classification."""

    ACTIVE = "active"
    TRIAL = "trial"
    EXPIRED = "expired"
    BLOCKED = "blocked"
    NOT_AVAILABLE = "not_available"


@dataclass(frozen=True)
class AccountExpiration:
    """Typed expiration information with no network or playback-derived semantics."""

    expires_at: datetime | None
    timezone: str | None = None

    def remaining_at(self, reference: datetime) -> timedelta | None:
        """Return provider expiration remaining at an explicit reference instant when known."""
        if self.expires_at is None:
            return None
        if reference.tzinfo is None or self.expires_at.tzinfo is None:
            raise ValidationError("expiration", "requires timezone-aware datetimes")
        return self.expires_at - reference

    def is_expired_at(self, reference: datetime) -> bool | None:
        """Return an explicit expiration result, or unknown when the provider gave no date."""
        remaining = self.remaining_at(reference)
        return None if remaining is None else remaining <= timedelta()

    def days_remaining_at(self, reference: datetime) -> int | None:
        """Return completed non-negative 24-hour periods remaining when known."""
        remaining = self.remaining_at(reference)
        return None if remaining is None else max(0, floor(remaining.total_seconds() / 86_400))

    def hours_remaining_at(self, reference: datetime) -> int | None:
        """Return completed non-negative hours remaining when known."""
        remaining = self.remaining_at(reference)
        return None if remaining is None else max(0, floor(remaining.total_seconds() / 3_600))


@dataclass(frozen=True)
class AccountInfo:
    """Optional account status returned by a provider without secret material."""

    provider_id: ProviderId
    status: AccountStatus | Literal["active", "expired", "blocked", "unknown"]
    expires_at: datetime | None = None
    active_connections: int | None = None
    max_connections: int | None = None
    message: str | None = None
    subscription_status: (
        SubscriptionStatus | Literal["active", "trial", "expired", "blocked", "not_available"]
    ) = SubscriptionStatus.NOT_AVAILABLE
    is_trial: bool | None = None
    expiration_timezone: str | None = None

    def __post_init__(self) -> None:
        if not self.provider_id.value.strip():
            raise ValidationError("provider_id", "must not be blank")
        try:
            object.__setattr__(self, "status", AccountStatus(self.status))
        except ValueError as exc:
            raise ValidationError("status", "must be a known account status") from exc
        try:
            object.__setattr__(
                self,
                "subscription_status",
                SubscriptionStatus(self.subscription_status),
            )
        except ValueError as exc:
            raise ValidationError(
                "subscription_status", "must be a known subscription status"
            ) from exc
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
        if self.expiration_timezone is not None:
            validate_nonblank_text(
                self.expiration_timezone,
                field="expiration_timezone",
                label="Expiration timezone",
                when_supplied=True,
            )
        if self.is_trial is True and self.subscription_status is not SubscriptionStatus.TRIAL:
            object.__setattr__(self, "subscription_status", SubscriptionStatus.TRIAL)

    @property
    def expiration(self) -> AccountExpiration:
        """Expose expiration as typed data for UI, health, diagnostics, and warnings."""
        return AccountExpiration(self.expires_at, self.expiration_timezone)
