"""Translate Xtream-compatible DTOs into canonical domain objects."""

from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.core.exceptions import ValidationError
from samotech_iptv.domain.entities.channel import Channel
from samotech_iptv.domain.value_objects.channel_id import ChannelId
from samotech_iptv.domain.value_objects.stream_id import StreamId
from samotech_iptv.domain.value_objects.url import URL

if TYPE_CHECKING:
    from collections.abc import Mapping

    from samotech_iptv.domain.value_objects.provider_id import ProviderId

__all__ = ["XtreamDomainTranslator"]


class XtreamDomainTranslator:
    """Stateless mappings from Xtream API records to canonical entities."""

    @staticmethod
    def channel(raw: Mapping[str, object], provider_id: ProviderId) -> Channel:
        """Map a live-stream record returned by ``get_live_streams``."""
        stream_id = XtreamDomainTranslator._required_text(raw, "stream_id")
        name = XtreamDomainTranslator._required_text(raw, "name")
        logo = str(raw.get("stream_icon") or "").strip()
        category_id = str(raw.get("category_id") or "").strip() or None
        epg_channel_id = str(raw.get("epg_channel_id") or "").strip() or None
        number = XtreamDomainTranslator._optional_int(raw.get("num"))
        return Channel(
            id=ChannelId(f"{provider_id.value}:{stream_id}"),
            name=name,
            provider_id=provider_id,
            stream_id=StreamId(stream_id),
            category_id=category_id,
            logo_url=URL(logo) if logo else None,
            epg_channel_id=epg_channel_id,
            number=number,
        )

    @staticmethod
    def _required_text(raw: Mapping[str, object], field: str) -> str:
        value = str(raw.get(field) or "").strip()
        if not value:
            raise ValidationError(field, f"Xtream response is missing {field}")
        return value

    @staticmethod
    def _optional_int(value: object) -> int | None:
        if value in (None, ""):
            return None
        try:
            return int(str(value))
        except ValueError as exc:
            raise ValidationError("num", "Xtream channel number must be an integer") from exc
