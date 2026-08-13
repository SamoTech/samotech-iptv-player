"""Catalogue retrieval helpers for the MAG provider."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import TYPE_CHECKING

from ..base.errors import AuthError, ProviderError
from .protocol_profile import MAGOperation

if TYPE_CHECKING:
    from .connection import MAGConnection
    from .session import MAGSession

log = logging.getLogger(__name__)

type MagRecord = dict[str, object]


class MAGCatalogue:
    """Load MAG catalogue records through the selected protocol profile."""

    def __init__(self, connection: MAGConnection, session: MAGSession) -> None:
        self._conn = connection
        self._sess = session
        self._live_commands: dict[str, str] = {}
        self._last_live_stats = {"received": 0, "accepted": 0, "rejected": 0}

    @property
    def live_catalogue_stats(self) -> dict[str, int]:
        """Return safe aggregate counts without retaining raw portal payloads."""
        return dict(self._last_live_stats)

    async def get_live_categories(self) -> list[MagRecord]:
        """Return live genre records only for profiles that explicitly support them."""
        if not self._sess.profile.uses_ordered_live_catalogue:
            raise ProviderError("Provider does not support category browsing")
        data = await self._sess.request(MAGOperation.LIVE_GENRES)
        return self._records_from_js_list(data)

    async def get_channels(self) -> list[MagRecord]:
        """Return live records through legacy or observed ordered-list behavior."""
        if not self._sess.profile.uses_ordered_live_catalogue:
            data = await self._sess.request(MAGOperation.CHANNELS)
            items = self._records_from_response(data)
            self._last_live_stats = {"received": len(items), "accepted": len(items), "rejected": 0}
            return items
        return await self._ordered_live_channels()

    async def _ordered_live_channels(self) -> list[MagRecord]:
        genres = await self.get_live_categories()
        received = accepted = rejected = 0
        self._live_commands.clear()
        records: list[MagRecord] = []
        seen: set[str] = set()
        for genre in genres:
            genre_id = str(genre.get("id") or "").strip()
            if not genre_id:
                rejected += 1
                continue
            page = 0
            while True:
                data = await self._sess.request(
                    MAGOperation.LIVE_ORDERED_LIST,
                    params={"genre": genre_id, "p": page},
                )
                envelope = self._js_payload(data)
                if envelope.get("error"):
                    raise AuthError("MAG catalogue response indicated an expired session")
                page_records = self._records(envelope.get("data", []))
                received += len(page_records)
                for record in page_records:
                    channel_id = str(record.get("id") or "").strip()
                    name = str(record.get("name") or record.get("title") or "").strip()
                    command = record.get("cmd")
                    if (
                        not channel_id
                        or not name
                        or not isinstance(command, str)
                        or not command.strip()
                    ):
                        rejected += 1
                        continue
                    if channel_id in seen:
                        continue
                    seen.add(channel_id)
                    self._live_commands[channel_id] = command
                    records.append(record)
                    accepted += 1
                total_items = self._as_nonnegative_int(
                    envelope.get("total_items"), len(page_records)
                )
                if not page_records or (page + 1) * len(page_records) >= total_items:
                    break
                page += 1
        self._last_live_stats = {"received": received, "accepted": accepted, "rejected": rejected}
        log.info("Retrieved MAG live records accepted=%d rejected=%d", accepted, rejected)
        return records

    async def live_command(self, channel_id: int) -> str | None:
        """Return a private loaded command, refreshing only if a compatible profile needs it."""
        key = str(channel_id)
        command = self._live_commands.get(key)
        if command is not None:
            return command
        if self._sess.profile.uses_channel_command_for_live_link:
            await self.get_channels()
            return self._live_commands.get(key)
        return None

    async def get_vod(self, page: int = 0, category_id: int | None = None) -> list[MagRecord]:
        params: dict[str, str | int] = {"p": page, "items_num": 100, "sortby": "added"}
        if category_id is not None:
            params["category"] = category_id
        return self._records_from_response(
            await self._sess.request(MAGOperation.VOD, params=params)
        )

    async def get_series(self, page: int = 0, category_id: int | None = None) -> list[MagRecord]:
        params: dict[str, str | int] = {"p": page, "items_num": 100, "sortby": "added"}
        if category_id is not None:
            params["category"] = category_id
        return self._records_from_response(
            await self._sess.request(MAGOperation.SERIES, params=params)
        )

    async def get_epg(
        self, channel_ids: list[int] | None = None, period: int = 3
    ) -> dict[int, list[MagRecord]]:
        params: dict[str, str | int] = {"period": period}
        if channel_ids:
            params["ch_id"] = ",".join(str(channel_id) for channel_id in channel_ids)
        raw = self._js_payload(await self._sess.request(MAGOperation.EPG, params=params))
        result: dict[int, list[MagRecord]] = {}
        for raw_channel_id, programmes in raw.items():
            try:
                result[int(str(raw_channel_id))] = self._records(programmes)
            except ValueError:
                continue
        return result

    @staticmethod
    def _records_from_response(data: object) -> list[MagRecord]:
        payload = MAGCatalogue._js_payload(data)
        if payload.get("error"):
            raise AuthError("MAG catalogue response indicated an expired session")
        return MAGCatalogue._records(payload.get("data", []))

    @staticmethod
    def _records_from_js_list(data: object) -> list[MagRecord]:
        if not isinstance(data, Mapping):
            return []
        return MAGCatalogue._records(data.get("js", []))

    @staticmethod
    def _js_payload(data: object) -> Mapping[str, object]:
        if not isinstance(data, Mapping):
            return {}
        payload = data.get("js", {})
        return payload if isinstance(payload, Mapping) else {}

    @staticmethod
    def _records(value: object) -> list[MagRecord]:
        if not isinstance(value, list):
            return []
        return [dict(record) for record in value if isinstance(record, Mapping)]

    @staticmethod
    def _as_nonnegative_int(value: object, fallback: int) -> int:
        try:
            return max(int(str(value)), 0)
        except (TypeError, ValueError):
            return fallback
