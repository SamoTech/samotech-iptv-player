"""Provider registry — register and resolve provider instances at runtime.

The registry is intentionally thin:
  - It holds ``InfraProviderMetadata`` (not live instances).
  - Instantiation is delegated to ``ProviderFactory``.
  - It is in-memory only; persistence comes in Phase B.3 (SQLite).
"""
from __future__ import annotations

from typing import Optional, Sequence

from samotech_iptv.core.exceptions import NotFoundError
from samotech_iptv.core.logging import get_logger
from samotech_iptv.infrastructure.providers.provider_metadata import InfraProviderMetadata

__all__ = ["ProviderRegistry"]

_log = get_logger(__name__)


class ProviderRegistry:
    """In-memory registry of provider metadata.

    Usage::

        registry = ProviderRegistry()
        registry.register(InfraProviderMetadata(
            provider_id="mag1",
            provider_type="mag",
            base_url="http://example.com",
        ))
        meta = registry.get("mag1")
        all_meta = registry.list_all()
        registry.deregister("mag1")
    """

    def __init__(self) -> None:
        self._providers: dict[str, InfraProviderMetadata] = {}

    def register(self, metadata: InfraProviderMetadata) -> None:
        """Add or replace a provider entry."""
        self._providers[metadata.provider_id] = metadata
        _log.info("Registered provider id=%s type=%s",
                  metadata.provider_id, metadata.provider_type)

    def deregister(self, provider_id: str) -> bool:
        """Remove a provider entry.  Returns True if it existed."""
        existed = provider_id in self._providers
        self._providers.pop(provider_id, None)
        if existed:
            _log.info("Deregistered provider id=%s", provider_id)
        return existed

    def get(self, provider_id: str) -> InfraProviderMetadata:
        """Return metadata for a provider, raising ``NotFoundError`` if absent."""
        try:
            return self._providers[provider_id]
        except KeyError:
            raise NotFoundError("Provider", provider_id) from None

    def find(self, provider_id: str) -> Optional[InfraProviderMetadata]:
        """Return metadata or None (never raises)."""
        return self._providers.get(provider_id)

    def list_all(self) -> Sequence[InfraProviderMetadata]:
        """Return all registered providers (insertion order)."""
        return list(self._providers.values())

    def list_by_type(self, provider_type: str) -> Sequence[InfraProviderMetadata]:
        """Return all providers of a given type."""
        return [
            m for m in self._providers.values()
            if m.provider_type == provider_type
        ]

    def list_active(self) -> Sequence[InfraProviderMetadata]:
        """Return only active providers."""
        return [m for m in self._providers.values() if m.is_active]

    def __len__(self) -> int:
        return len(self._providers)

    def __contains__(self, provider_id: str) -> bool:
        return provider_id in self._providers
