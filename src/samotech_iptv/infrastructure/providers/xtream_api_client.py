"""HTTP-backed Xtream-compatible API client with no retained provider session state."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, cast

from samotech_iptv.core.exceptions import ProviderError

if TYPE_CHECKING:
    from collections.abc import Sequence

    from samotech_iptv.infrastructure.network.http_client import AsyncHttpClient
    from samotech_iptv.infrastructure.providers.xtream_request_builder import XtreamRequestBuilder

__all__ = ["XtreamApiClient"]


class XtreamApiClient:
    """Retrieve Xtream API DTOs through the shared asynchronous HTTP client."""

    def __init__(self, http_client: AsyncHttpClient, request_builder: XtreamRequestBuilder) -> None:
        self._http_client = http_client
        self._request_builder = request_builder

    async def authenticate(self) -> bool:
        """Return whether a standard authentication response reports an active user."""
        payload = await self._http_client.get_json(str(self._request_builder.player_api()))
        if not isinstance(payload, Mapping):
            raise ProviderError("Xtream authentication response must be an object")
        user_info = payload.get("user_info")
        if not isinstance(user_info, Mapping):
            return False
        return str(user_info.get("auth") or user_info.get("status") or "").casefold() in {
            "1",
            "true",
            "active",
        }

    async def live_streams(self) -> Sequence[Mapping[str, object]]:
        """Return raw live-stream records for canonical adapter translation."""
        return await self._stream_records("get_live_streams", "live-stream")

    async def vod_streams(self) -> Sequence[Mapping[str, object]]:
        """Return raw VOD records for canonical movie translation."""
        return await self._stream_records("get_vod_streams", "VOD")

    async def series(self) -> Sequence[Mapping[str, object]]:
        """Return raw series records for canonical series translation."""
        return await self._stream_records("get_series", "series")

    async def short_epg(self, stream_id: str) -> Sequence[Mapping[str, object]]:
        """Return validated short-EPG records for one Xtream live stream."""
        payload = await self._http_client.get_json(
            str(self._request_builder.player_api("get_short_epg", stream_id=stream_id))
        )
        if not isinstance(payload, Mapping):
            raise ProviderError("Xtream short-EPG response must be an object")
        listings = payload.get("epg_listings")
        if not isinstance(listings, list) or not all(
            isinstance(item, Mapping) for item in listings
        ):
            raise ProviderError("Xtream short-EPG response must include a list of objects")
        return cast("Sequence[Mapping[str, object]]", listings)

    async def _stream_records(self, action: str, label: str) -> Sequence[Mapping[str, object]]:
        payload = await self._http_client.get_json(str(self._request_builder.player_api(action)))
        if not isinstance(payload, list) or not all(isinstance(item, Mapping) for item in payload):
            raise ProviderError(f"Xtream {label} response must be a list of objects")
        return cast("Sequence[Mapping[str, object]]", payload)
