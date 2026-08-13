"""Catalogue retrieval helpers for the MAG provider."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import TYPE_CHECKING

from ..base.errors import AuthError
from .protocol_profile import MAGOperation

if TYPE_CHECKING:
    from .connection import MAGConnection
    from .session import MAGSession

log = logging.getLogger(__name__)

type MagRecord = dict[str, object]


class MAGCatalogue:
    def __init__(self, connection: MAGConnection, session: MAGSession) -> None:
        # The connection remains constructor-injected for legacy compatibility;
        # profile-owned requests are issued through the session.
        self._conn = connection
        self._sess = session

    async def get_channels(self) -> list[MagRecord]:
        """Return the portal's live-TV records through the selected profile."""
        log.info("Fetching MAG channel catalogue")
        data = await self._sess.request(MAGOperation.CHANNELS)
        items = self._records_from_response(data)
        log.info("Retrieved %d MAG channels", len(items))
        return items

    async def get_vod(self, page: int = 0, category_id: int | None = None) -> list[MagRecord]:
        """Return a page of MAG VOD records through the selected profile."""
        params: dict[str, str | int] = {"p": page, "items_num": 100, "sortby": "added"}
        if category_id is not None:
            params["category"] = category_id
        data = await self._sess.request(MAGOperation.VOD, params=params)
        return self._records_from_response(data)

    async def get_series(self, page: int = 0, category_id: int | None = None) -> list[MagRecord]:
        """Return a page of MAG series records through the selected profile."""
        params: dict[str, str | int] = {"p": page, "items_num": 100, "sortby": "added"}
        if category_id is not None:
            params["category"] = category_id
        data = await self._sess.request(MAGOperation.SERIES, params=params)
        return self._records_from_response(data)

    async def get_epg(
        self,
        channel_ids: list[int] | None = None,
        period: int = 3,
    ) -> dict[int, list[MagRecord]]:
        """Return EPG records keyed by numeric MAG channel ID."""
        params: dict[str, str | int] = {"period": period}
        if channel_ids:
            params["ch_id"] = ",".join(str(channel_id) for channel_id in channel_ids)
        data = await self._sess.request(MAGOperation.EPG, params=params)
        raw = self._js_payload(data)
        result: dict[int, list[MagRecord]] = {}
        for raw_channel_id, programmes in raw.items():
            try:
                channel_id = int(str(raw_channel_id))
            except ValueError:
                continue
            result[channel_id] = self._records(programmes)
        log.info("MAG EPG fetched for %d channels", len(result))
        return result

    @staticmethod
    def _records_from_response(data: object) -> list[MagRecord]:
        """Extract list-shaped payload data and classify session errors."""
        payload = MAGCatalogue._js_payload(data)
        error = payload.get("error")
        if error:
            raise AuthError("MAG catalogue response indicated an expired session")
        return MAGCatalogue._records(payload.get("data", []))

    @staticmethod
    def _js_payload(data: object) -> Mapping[str, object]:
        """Return a MAG ``js`` envelope as an empty mapping when malformed."""
        if not isinstance(data, Mapping):
            return {}
        payload = data.get("js", {})
        return payload if isinstance(payload, Mapping) else {}

    @staticmethod
    def _records(value: object) -> list[MagRecord]:
        """Normalize a list of external mapping records into mutable dictionaries."""
        if not isinstance(value, list):
            return []
        return [dict(record) for record in value if isinstance(record, Mapping)]
