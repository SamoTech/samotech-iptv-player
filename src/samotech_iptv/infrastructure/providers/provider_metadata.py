"""Runtime metadata for a registered provider instance.

Distinct from ``application.dtos.provider.ProviderMetadata`` (which is a
read-only DTO for the presentation layer).  This dataclass is mutable so
the registry can update last-seen / error state without round-tripping
through the domain layer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

__all__ = ["InfraProviderMetadata"]


@dataclass
class InfraProviderMetadata:
    """Mutable runtime state for a registered provider.

    Attributes:
        provider_id:   Stable string ID (matches ``ProviderId.value``).
        provider_type: Discriminator string used by the factory
                       (e.g. ``"mag"``, ``"xtream"``, ``"m3u"``).
        base_url:      Base URL of the remote service.
        is_active:     Whether the provider is eligible for use.
        capabilities:  Set of capability names this provider supports.
        last_error:    Most recent error message, if any.  Session tokens
                       are held only by the live provider adapter.
    """

    provider_id: str
    provider_type: str
    base_url: str
    is_active: bool = True
    capabilities: frozenset[str] = field(
        default_factory=lambda: frozenset()
    )
    last_error: Optional[str] = None
