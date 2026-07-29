"""
Abstract base class every provider must implement.

A provider is *stateful*: it is instantiated with a config dict, used as an
async context manager (which opens / closes the underlying HTTP session), and
then its catalogue/stream methods are called.

Example
-------
    async with ProviderRegistry.get("mag")(config) as prov:
        channels = await prov.get_channels()
"""
from __future__ import annotations

import abc
from typing import Any


class BaseProvider(abc.ABC):
    """Provider-agnostic interface for IPTV middleware adapters."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    # ── lifecycle ────────────────────────────────────────────────────────────

    @abc.abstractmethod
    async def connect(self) -> None:
        """Open the underlying transport (HTTP session, WebSocket …)."""

    @abc.abstractmethod
    async def close(self) -> None:
        """Release all resources cleanly."""

    async def __aenter__(self) -> "BaseProvider":
        await self.connect()
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    # ── authentication ───────────────────────────────────────────────────────

    @abc.abstractmethod
    async def authenticate(self) -> None:
        """Authenticate with the portal using authorised credentials."""

    @abc.abstractmethod
    async def refresh_token(self) -> None:
        """Refresh / renew the session token without full re-auth."""

    # ── profile ──────────────────────────────────────────────────────────────

    @abc.abstractmethod
    async def get_profile(self) -> dict[str, Any]:
        """Return subscriber / account profile information."""

    # ── catalogues ───────────────────────────────────────────────────────────

    @abc.abstractmethod
    async def get_channels(self) -> list[dict[str, Any]]:
        """Return the live-TV channel catalogue."""

    @abc.abstractmethod
    async def get_vod(self, page: int = 0, category_id: int | None = None) -> list[dict[str, Any]]:
        """Return VOD movie catalogue, optionally filtered by category."""

    @abc.abstractmethod
    async def get_series(self, page: int = 0, category_id: int | None = None) -> list[dict[str, Any]]:
        """Return series catalogue, optionally filtered by category."""

    # ── EPG ──────────────────────────────────────────────────────────────────

    @abc.abstractmethod
    async def get_epg(
        self,
        channel_ids: list[int] | None = None,
        period: int = 3,
    ) -> dict[int, list[dict[str, Any]]]:
        """
        Return EPG data keyed by channel ID.

        Parameters
        ----------
        channel_ids:
            Restrict to specific channels; *None* returns all available.
        period:
            Lookahead in days (default 3).
        """

    # ── stream resolution ────────────────────────────────────────────────────

    @abc.abstractmethod
    async def get_stream_url(self, stream_id: int, stream_type: str = "live") -> str:
        """
        Resolve the playback URL for *stream_id*.

        Parameters
        ----------
        stream_type:
            One of ``"live"``, ``"vod"``, ``"series"``.
        """
