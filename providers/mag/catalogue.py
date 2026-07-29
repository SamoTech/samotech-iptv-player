"""
Catalogue retrieval helpers for the MAG provider.
"""
from __future__ import annotations

import logging
from typing import Any

from .constants import (
    ENDPOINT_CHANNELS,
    ENDPOINT_VOD,
    ENDPOINT_SERIES,
    ENDPOINT_EPG,
)
from .connection import MAGConnection
from .session import MAGSession

log = logging.getLogger(__name__)


class MAGCatalogue:
    def __init__(self, connection: MAGConnection, session: MAGSession) -> None:
        self._conn = connection
        self._sess = session

    async def get_channels(self) -> list[dict[str, Any]]:
        log.info("Fetching channel catalogue")
        data = await self._conn.get(ENDPOINT_CHANNELS, headers=self._sess.get_headers())
        items: list[dict] = (data.get("js") or {}).get("data", [])
        log.info("Retrieved %d channels", len(items))
        return items

    async def get_vod(self, page: int = 0, category_id: int | None = None) -> list[dict[str, Any]]:
        log.info("Fetching VOD catalogue (page=%d, category=%s)", page, category_id)
        params: dict[str, Any] = {"p": page, "items_num": 100, "sortby": "added"}
        if category_id is not None:
            params["category"] = category_id
        data = await self._conn.get(ENDPOINT_VOD, params=params, headers=self._sess.get_headers())
        items: list[dict] = (data.get("js") or {}).get("data", [])
        log.info("Retrieved %d VOD items", len(items))
        return items

    async def get_series(self, page: int = 0, category_id: int | None = None) -> list[dict[str, Any]]:
        log.info("Fetching series catalogue (page=%d, category=%s)", page, category_id)
        params: dict[str, Any] = {"p": page, "items_num": 100, "sortby": "added"}
        if category_id is not None:
            params["category"] = category_id
        data = await self._conn.get(ENDPOINT_SERIES, params=params, headers=self._sess.get_headers())
        items: list[dict] = (data.get("js") or {}).get("data", [])
        log.info("Retrieved %d series", len(items))
        return items

    async def get_epg(
        self,
        channel_ids: list[int] | None = None,
        period: int = 3,
    ) -> dict[int, list[dict[str, Any]]]:
        log.info("Fetching EPG (channels=%s, period=%d days)", channel_ids, period)
        params: dict[str, Any] = {"period": period}
        if channel_ids:
            params["ch_id"] = ",".join(str(c) for c in channel_ids)
        data = await self._conn.get(ENDPOINT_EPG, params=params, headers=self._sess.get_headers())
        raw: dict = data.get("js") or {}
        result: dict[int, list[dict]] = {}
        for ch_id_str, programmes in raw.items():
            try:
                result[int(ch_id_str)] = programmes if isinstance(programmes, list) else []
            except ValueError:
                pass
        log.info("EPG fetched for %d channels", len(result))
        return result
