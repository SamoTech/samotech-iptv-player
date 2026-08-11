"""Translate MAG protocol records into canonical domain objects."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from samotech_iptv.core.exceptions import ValidationError
from samotech_iptv.domain.entities.channel import Channel
from samotech_iptv.domain.entities.epg_entry import EPGEntry
from samotech_iptv.domain.value_objects.channel_id import ChannelId
from samotech_iptv.domain.value_objects.stream_id import StreamId
from samotech_iptv.domain.value_objects.url import URL

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from samotech_iptv.domain.value_objects.provider_id import ProviderId

__all__ = ["MagDomainTranslator"]


class MagDomainTranslator:
    """Stateless mapping helper for raw MAG protocol responses."""

    @staticmethod
    def channel(raw: Mapping[str, object], provider_id: ProviderId) -> Channel:
        """Map one MAG channel response record to a domain ``Channel``."""
        channel_id = MagDomainTranslator._required_text(raw, "id")
        name = str(raw.get("name") or raw.get("title") or "").strip()
        if not name:
            raise ValidationError("name", "MAG channel response has no display name")

        logo = str(raw.get("logo") or raw.get("logo_small") or "").strip()
        number = MagDomainTranslator._optional_int(raw.get("number") or raw.get("ch_num"))
        category_id = (
            str(raw.get("tv_genre_id") or raw.get("category_id") or "").strip() or None
        )
        epg_channel_id = str(raw.get("xmltv_id") or raw.get("epg_id") or "").strip() or None

        return Channel(
            id=ChannelId(channel_id),
            name=name,
            provider_id=provider_id,
            stream_id=StreamId(str(raw.get("stream_id") or channel_id)),
            category_id=category_id,
            logo_url=URL(logo) if logo else None,
            epg_channel_id=epg_channel_id,
            number=number,
        )

    @staticmethod
    def channels(
        raw_records: Sequence[Mapping[str, object]], provider_id: ProviderId
    ) -> list[Channel]:
        """Map a MAG channel collection to canonical channel entities."""
        return [MagDomainTranslator.channel(record, provider_id) for record in raw_records]

    @staticmethod
    def epg_entries(
        raw_records: Sequence[Mapping[str, object]], channel_id: ChannelId
    ) -> list[EPGEntry]:
        """Map MAG EPG records for one channel to canonical EPG entities."""
        return [MagDomainTranslator.epg_entry(record, channel_id) for record in raw_records]

    @staticmethod
    def epg_entry(raw: Mapping[str, object], channel_id: ChannelId) -> EPGEntry:
        """Map one MAG programme record to a domain ``EPGEntry``."""
        start_timestamp = MagDomainTranslator._required_timestamp(raw, "start_timestamp", "time")
        end_timestamp = MagDomainTranslator._required_timestamp(raw, "stop_timestamp", "time_to")
        title = str(raw.get("name") or raw.get("title") or "").strip()
        if not title:
            raise ValidationError("title", "MAG EPG response has no programme title")

        entry_id = str(raw.get("id") or f"{channel_id}:{start_timestamp}:{title}")
        return EPGEntry(
            id=entry_id,
            channel_id=channel_id,
            title=title,
            start=datetime.fromtimestamp(start_timestamp, tz=UTC),
            end=datetime.fromtimestamp(end_timestamp, tz=UTC),
            description=str(raw.get("descr") or raw.get("description") or "").strip() or None,
            category=str(raw.get("category") or "").strip() or None,
        )

    @staticmethod
    def stream_url(raw_url: str) -> URL:
        """Validate and wrap a resolved MAG stream URL."""
        return URL(raw_url)

    @staticmethod
    def _required_text(raw: Mapping[str, object], key: str) -> str:
        value = str(raw.get(key) or "").strip()
        if not value:
            raise ValidationError(key, f"MAG response is missing {key}")
        return value

    @staticmethod
    def _required_timestamp(raw: Mapping[str, object], *keys: str) -> int:
        for key in keys:
            value = raw.get(key)
            if value not in (None, "", 0, "0"):
                try:
                    return int(str(value))
                except (TypeError, ValueError) as exc:
                    raise ValidationError(key, "MAG timestamp must be an integer") from exc
        raise ValidationError(keys[0], "MAG EPG response is missing a timestamp")

    @staticmethod
    def _optional_int(value: object) -> int | None:
        if value in (None, ""):
            return None
        try:
            return int(str(value))
        except (TypeError, ValueError) as exc:
            raise ValidationError("number", "MAG channel number must be an integer") from exc
