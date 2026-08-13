"""Translate Xtream-compatible DTOs into canonical domain objects."""

from __future__ import annotations

from base64 import b64decode
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from samotech_iptv.core.exceptions import ValidationError
from samotech_iptv.core.logging import get_logger
from samotech_iptv.domain.entities.category import Category
from samotech_iptv.domain.entities.channel import Channel
from samotech_iptv.domain.entities.epg_entry import EPGEntry
from samotech_iptv.domain.entities.movie import Movie
from samotech_iptv.domain.entities.series import Series
from samotech_iptv.domain.value_objects.channel_id import ChannelId
from samotech_iptv.domain.value_objects.stream_id import StreamId
from samotech_iptv.domain.value_objects.url import URL

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from samotech_iptv.domain.value_objects.provider_id import ProviderId

__all__ = ["XtreamDomainTranslator"]

_LOG = get_logger(__name__)


class XtreamDomainTranslator:
    """Stateless mappings from Xtream API records to canonical entities."""

    @staticmethod
    def categories(
        raw_records: Sequence[Mapping[str, object]], provider_id: ProviderId
    ) -> list[Category]:
        """Map a single Xtream category family to canonical category entities."""
        return [XtreamDomainTranslator.category(record, provider_id) for record in raw_records]

    @staticmethod
    def category(raw: Mapping[str, object], provider_id: ProviderId) -> Category:
        """Map an Xtream category record while preserving its content-facing identifier."""
        return Category(
            id=XtreamDomainTranslator._required_text(raw, "category_id"),
            name=XtreamDomainTranslator._required_text(raw, "category_name"),
            provider_id=provider_id,
            parent_id=str(raw.get("parent_id") or "").strip() or None,
        )

    @staticmethod
    def channel(
        raw: Mapping[str, object], provider_id: ProviderId, record_index: int | None = None
    ) -> Channel:
        """Map a live-stream record while tolerating invalid optional logo metadata."""
        stream_id = XtreamDomainTranslator._required_text(raw, "stream_id")
        name = XtreamDomainTranslator._required_text(raw, "name")
        logo = XtreamDomainTranslator._optional_logo(
            raw.get("stream_icon"), provider_id, name, record_index
        )
        category_id = str(raw.get("category_id") or "").strip() or None
        epg_channel_id = str(raw.get("epg_channel_id") or "").strip() or None
        number = XtreamDomainTranslator._optional_int(raw.get("num"))
        return Channel(
            id=ChannelId(f"{provider_id.value}:{stream_id}"),
            name=name,
            provider_id=provider_id,
            stream_id=StreamId(stream_id),
            category_id=category_id,
            logo_url=logo,
            epg_channel_id=epg_channel_id,
            number=number,
        )

    @staticmethod
    def _optional_logo(
        value: object,
        provider_id: ProviderId,
        channel_name: str,
        record_index: int | None,
    ) -> URL | None:
        """Validate optional logo metadata without allowing it to abort a channel."""
        logo = str(value or "").replace("\u00a0", " ").strip()
        if not logo:
            return None
        try:
            return URL(logo)
        except ValidationError:
            _LOG.warning(
                "[IPTV][WARN] Provider=%s Record=%s Field=logo_url Reason=invalid URL "
                "Action=ignored Channel=%s",
                provider_id.value,
                record_index if record_index is not None else "unknown",
                XtreamDomainTranslator._safe_label(channel_name),
            )
            return None

    @staticmethod
    def _safe_label(value: str) -> str:
        """Keep diagnostic labels short and free from control characters."""
        return " ".join(value.split())[:120]

    @staticmethod
    def movie(raw: Mapping[str, object], provider_id: ProviderId) -> Movie:
        """Map a VOD record returned by ``get_vod_streams`` to a canonical movie."""
        stream_id = XtreamDomainTranslator._required_text(raw, "stream_id")
        title = XtreamDomainTranslator._required_text(raw, "name")
        poster = str(raw.get("stream_icon") or "").strip()
        return Movie(
            id=f"{provider_id.value}:{stream_id}",
            title=title,
            provider_id=provider_id,
            stream_id=StreamId(stream_id),
            category_id=str(raw.get("category_id") or "").strip() or None,
            poster_url=URL(poster) if poster else None,
            plot=str(raw.get("plot") or "").strip() or None,
        )

    @staticmethod
    def series(raw: Mapping[str, object], provider_id: ProviderId) -> Series:
        """Map a series record returned by ``get_series`` to a canonical series."""
        series_id = XtreamDomainTranslator._required_text(raw, "series_id")
        title = XtreamDomainTranslator._required_text(raw, "name")
        poster = str(raw.get("cover") or raw.get("cover_big") or "").strip()
        return Series(
            id=f"{provider_id.value}:{series_id}",
            title=title,
            provider_id=provider_id,
            category_id=str(raw.get("category_id") or "").strip() or None,
            poster_url=URL(poster) if poster else None,
            plot=str(raw.get("plot") or "").strip() or None,
        )

    @staticmethod
    def epg_entries(
        raw_records: Sequence[Mapping[str, object]], channel_id: ChannelId
    ) -> list[EPGEntry]:
        """Map Xtream short-EPG records for a channel to canonical EPG entries."""
        return [XtreamDomainTranslator.epg_entry(record, channel_id) for record in raw_records]

    @staticmethod
    def epg_entry(raw: Mapping[str, object], channel_id: ChannelId) -> EPGEntry:
        """Map one Xtream short-EPG record to a canonical programme entry."""
        start_timestamp = XtreamDomainTranslator._required_timestamp(raw, "start_timestamp")
        end_timestamp = XtreamDomainTranslator._required_timestamp(raw, "stop_timestamp")
        title = XtreamDomainTranslator._decoded_required_text(raw, "title")
        entry_id = str(raw.get("id") or f"{channel_id.value}:{start_timestamp}:{title}").strip()
        return EPGEntry(
            id=entry_id,
            channel_id=channel_id,
            title=title,
            start=datetime.fromtimestamp(start_timestamp, tz=UTC),
            end=datetime.fromtimestamp(end_timestamp, tz=UTC),
            description=XtreamDomainTranslator._decoded_optional_text(raw.get("description")),
            category=str(raw.get("category") or "").strip() or None,
        )

    @staticmethod
    def _required_text(raw: Mapping[str, object], field: str) -> str:
        value = str(raw.get(field) or "").strip()
        if not value:
            raise ValidationError(field, f"Xtream response is missing {field}")
        return value

    @staticmethod
    def _decoded_required_text(raw: Mapping[str, object], field: str) -> str:
        value = XtreamDomainTranslator._decoded_optional_text(raw.get(field))
        if not value:
            raise ValidationError(field, f"Xtream response is missing {field}")
        return value

    @staticmethod
    def _decoded_optional_text(value: object) -> str | None:
        text = str(value or "").strip()
        if not text:
            return None
        try:
            decoded = b64decode(text, validate=True).decode("utf-8").strip()
        except (UnicodeDecodeError, ValueError):
            return text
        return decoded or text

    @staticmethod
    def _required_timestamp(raw: Mapping[str, object], field: str) -> int:
        value = raw.get(field)
        if value in (None, "", 0, "0"):
            raise ValidationError(field, f"Xtream response is missing {field}")
        try:
            return int(str(value))
        except (TypeError, ValueError) as exc:
            raise ValidationError(field, "Xtream timestamp must be an integer") from exc

    @staticmethod
    def _optional_int(value: object) -> int | None:
        if value in (None, ""):
            return None
        try:
            return int(str(value))
        except ValueError as exc:
            raise ValidationError("num", "Xtream channel number must be an integer") from exc
