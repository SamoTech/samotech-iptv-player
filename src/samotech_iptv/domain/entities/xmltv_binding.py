"""Canonical non-secret XMLTV source binding records."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

from samotech_iptv.core.exceptions import ValidationError

if TYPE_CHECKING:
    from samotech_iptv.domain.value_objects.channel_id import ChannelId
    from samotech_iptv.domain.value_objects.provider_id import ProviderId

__all__ = ["XMLTVBinding", "XMLTVChannelMapping"]


@dataclass(frozen=True)
class XMLTVChannelMapping:
    """Explicit association from one XMLTV source channel to one canonical channel."""

    source_channel_id: str
    channel_id: ChannelId

    def __post_init__(self) -> None:
        if not self.source_channel_id or self.source_channel_id != self.source_channel_id.strip():
            raise ValidationError(
                "source_channel_id", "XMLTV source channel ID must be non-empty and trimmed"
            )
        if len(self.source_channel_id) > 512:
            raise ValidationError(
                "source_channel_id", "XMLTV source channel ID exceeds the supported length"
            )


@dataclass(frozen=True)
class XMLTVBinding:
    """A registered provider's local XMLTV source and explicit channel mappings.

    The source is deliberately restricted to a local path or a local ``file:`` URI.
    Remote and tokenized sources require an independent secure-storage and redacted-
    transport design before they can be introduced safely.
    """

    provider_id: ProviderId
    source: str
    mappings: tuple[XMLTVChannelMapping, ...]

    def __post_init__(self) -> None:
        if not self.source or self.source != self.source.strip():
            raise ValidationError("source", "XMLTV source must be non-empty and trimmed")
        if self._is_windows_drive_path(self.source):
            parsed = None
        else:
            parsed = urlsplit(self.source)
        if parsed is not None and parsed.scheme.casefold() not in {"", "file"}:
            raise ValidationError("source", "XMLTV source must be a local path or file URI")
        if (
            parsed is not None
            and parsed.scheme.casefold() == "file"
            and (parsed.netloc or parsed.query or parsed.fragment)
        ):
            raise ValidationError("source", "XMLTV file URI must identify a local file only")
        if not self.mappings:
            raise ValidationError(
                "mappings", "XMLTV binding must contain at least one channel mapping"
            )
        source_channel_ids = [mapping.source_channel_id for mapping in self.mappings]
        if len(source_channel_ids) != len(set(source_channel_ids)):
            raise ValidationError("mappings", "XMLTV source channel IDs must be unique")

    @staticmethod
    def _is_windows_drive_path(source: str) -> bool:
        return len(source) >= 3 and source[1] == ":" and source[2] in {"/", "\\"}

    @property
    def channel_mapping(self) -> dict[str, ChannelId]:
        """Return the parser-ready mapping without exposing source text elsewhere."""
        return {mapping.source_channel_id: mapping.channel_id for mapping in self.mappings}
