"""Provider-related domain events."""
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from samotech_iptv.core.events import DomainEvent
from samotech_iptv.domain.value_objects.provider_id import ProviderId

__all__ = ["ProviderAuthenticatedEvent", "ProviderRefreshFailedEvent"]


@dataclass(frozen=True)
class ProviderAuthenticatedEvent(DomainEvent):
    """Raised after a successful provider authentication."""

    event_name: ClassVar[str] = "provider.authenticated"
    provider_id: ProviderId = ProviderId("unknown")


@dataclass(frozen=True)
class ProviderRefreshFailedEvent(DomainEvent):
    """Raised when a session refresh fails."""

    event_name: ClassVar[str] = "provider.refresh_failed"
    provider_id: ProviderId = ProviderId("unknown")
    reason: str = ""
