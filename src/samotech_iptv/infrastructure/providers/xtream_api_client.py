"""HTTP-backed Xtream-compatible API client with no retained provider session state."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, cast

from samotech_iptv.core.exceptions import ProviderError

if TYPE_CHECKING:
    from collections.abc import Sequence

    from samotech_iptv.domain.value_objects.url import URL
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

    async def vod_info(self, stream_id: str) -> Mapping[str, object]:
        """Return one validated VOD detail response without retaining provider data."""
        return await self._detail_record("get_vod_info", "vod_id", stream_id, "VOD")

    async def series_info(self, series_id: str) -> Mapping[str, object]:
        """Return one validated Series detail response without retaining provider data."""
        return await self._detail_record("get_series_info", "series_id", series_id, "series")

    async def live_categories(self) -> Sequence[Mapping[str, object]]:
        """Return raw live category records for canonical translation."""
        return await self._stream_records("get_live_categories", "live-category")

    async def vod_categories(self) -> Sequence[Mapping[str, object]]:
        """Return raw VOD category records for canonical translation."""
        return await self._stream_records("get_vod_categories", "VOD-category")

    async def series_categories(self) -> Sequence[Mapping[str, object]]:
        """Return raw series category records for canonical translation."""
        return await self._stream_records("get_series_categories", "series-category")

    def live_stream_url(self, stream_id: str, extension: str) -> URL:
        """Build the credential-safe playback URL for one live stream."""
        return self._request_builder.stream_url("live", stream_id, extension)

    def vod_stream_url(self, stream_id: str, extension: str) -> URL:
        """Build the credential-safe playback URL for one validated VOD stream."""
        return self._request_builder.stream_url("movie", stream_id, extension)

    def episode_stream_url(self, episode_id: str, extension: str) -> URL:
        """Build the credential-safe playback URL for one validated episode stream."""
        return self._request_builder.stream_url("series", episode_id, extension)

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

    async def _detail_record(
        self, action: str, identifier_name: str, identifier: str, label: str
    ) -> Mapping[str, object]:
        payload = await self._http_client.get_json(
            str(self._request_builder.player_api(action, **{identifier_name: identifier}))
        )
        if not isinstance(payload, Mapping):
            raise ProviderError(f"Xtream {label} detail response must be an object")
        return payload
