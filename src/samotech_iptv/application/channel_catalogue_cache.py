"""Application-local cache for already loaded safe channel DTO catalogues."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from samotech_iptv.application.dtos.channels import ChannelDTO

__all__ = ["ChannelCatalogueCache"]


class ChannelCatalogueCache:
    """Retain the latest complete browse result for local registered search."""

    def __init__(self) -> None:
        self._catalogues: dict[str, tuple[ChannelDTO, ...]] = {}

    def replace(self, provider_id: str, channels: Sequence[ChannelDTO]) -> None:
        """Replace one provider's safe in-memory catalogue snapshot."""
        self._catalogues[provider_id] = tuple(channels)

    def invalidate(self, provider_id: str) -> None:
        """Remove one provider snapshot without affecting other providers."""
        self._catalogues.pop(provider_id, None)

    def search(self, provider_id: str, query: str, limit: int) -> tuple[ChannelDTO, ...] | None:
        """Filter a cached catalogue, or return ``None`` when it is not loaded."""
        catalogue = self._catalogues.get(provider_id)
        if catalogue is None:
            return None
        if limit <= 0:
            return ()
        normalized_query = query.strip().casefold()
        if not normalized_query:
            return catalogue[:limit]
        return tuple(
            channel for channel in catalogue if normalized_query in channel.name.casefold()
        )[:limit]
