"""DTO translation helpers for the MAG provider adapter.

Translates legacy ``dict`` payloads returned by ``MAGProvider`` methods
into clean domain entities and application DTOs.

No protocol logic lives here — only field mapping.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from samotech_iptv.application.dtos.auth import AuthenticateResponse
from samotech_iptv.application.dtos.channels import ChannelDTO
from samotech_iptv.application.dtos.categories import CategoryDTO
from samotech_iptv.application.dtos.epg import EPGEntryDTO
from samotech_iptv.application.dtos.stream import ResolveStreamResponse

__all__ = ["MagDtoTranslator"]


class MagDtoTranslator:
    """Stateless helper — all methods are static."""

    @staticmethod
    def channel(raw: dict[str, Any]) -> ChannelDTO:
        """Map a raw MAG channel dict to a ``ChannelDTO``.

        MAG field reference::

            id          int     channel numeric ID
            name        str     display name
            logo        str     URL to logo image
            tv_genre_id int     category ID
            cmd         str     stream command
            number      int     channel number / LCN
        """
        return ChannelDTO(
            id=str(raw.get("id", "")),
            name=str(raw.get("name") or raw.get("title") or "").strip(),
            logo_url=str(raw.get("logo") or raw.get("logo_small") or ""),
            category_id=str(raw.get("tv_genre_id") or raw.get("category_id") or ""),
            stream_id=str(raw.get("id", "")),
            number=int(raw.get("number") or raw.get("ch_num") or 0),
            is_favorite=bool(raw.get("fav") or False),
        )

    @staticmethod
    def channels(raw_list: list[dict[str, Any]]) -> list[ChannelDTO]:
        return [MagDtoTranslator.channel(r) for r in raw_list]

    @staticmethod
    def category(raw: dict[str, Any], category_type: str = "live") -> CategoryDTO:
        """Map a raw MAG category dict to a ``CategoryDTO``."""
        return CategoryDTO(
            id=str(raw.get("id", "")),
            name=str(raw.get("title") or raw.get("name") or "").strip(),
            category_type=category_type,
            parent_id=str(raw.get("parent_id") or "") or None,
        )

    @staticmethod
    def categories(
        raw_list: list[dict[str, Any]], category_type: str = "live"
    ) -> list[CategoryDTO]:
        return [MagDtoTranslator.category(r, category_type) for r in raw_list]

    @staticmethod
    def epg_entry(
        raw: dict[str, Any], channel_id: int
    ) -> EPGEntryDTO:
        """Map a single EPG programme dict to an ``EPGEntryDTO``.

        MAG EPG field reference::

            id          int
            name        str     programme title
            descr       str     description
            start_timestamp   int  UNIX timestamp
            stop_timestamp    int  UNIX timestamp
        """
        start_ts = int(raw.get("start_timestamp") or raw.get("time") or 0)
        stop_ts = int(raw.get("stop_timestamp") or raw.get("time_to") or 0)
        return EPGEntryDTO(
            channel_id=str(channel_id),
            title=str(raw.get("name") or raw.get("title") or "").strip(),
            description=str(raw.get("descr") or raw.get("description") or ""),
            start=datetime.fromtimestamp(start_ts, tz=timezone.utc) if start_ts else None,
            end=datetime.fromtimestamp(stop_ts, tz=timezone.utc) if stop_ts else None,
        )

    @staticmethod
    def epg(
        raw_epg: dict[int, list[dict[str, Any]]]
    ) -> dict[str, list[EPGEntryDTO]]:
        """Map the full EPG response dict.

        Returns a channel-id-str → list[EPGEntryDTO] mapping.
        """
        result: dict[str, list[EPGEntryDTO]] = {}
        for ch_id, programmes in raw_epg.items():
            result[str(ch_id)] = [
                MagDtoTranslator.epg_entry(p, ch_id) for p in programmes
            ]
        return result

    @staticmethod
    def auth_response(portal_url: str, token: str) -> AuthenticateResponse:
        return AuthenticateResponse(
            provider_id=portal_url,
            token=token,
            success=bool(token),
        )

    @staticmethod
    def stream_response(url: str, stream_id: str) -> ResolveStreamResponse:
        return ResolveStreamResponse(
            stream_id=stream_id,
            url=url,
        )
