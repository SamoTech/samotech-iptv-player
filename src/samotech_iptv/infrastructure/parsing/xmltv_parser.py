"""Bounded and secure XMLTV programme parsing into canonical EPG entries."""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Protocol, cast

from defusedxml.common import DefusedXmlException
from defusedxml.ElementTree import ParseError, fromstring

from samotech_iptv.core.exceptions import ValidationError
from samotech_iptv.domain.entities.epg_entry import EPGEntry

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Mapping

    from samotech_iptv.domain.value_objects.channel_id import ChannelId

    class _ElementLike(Protocol):
        tag: str

        def get(self, key: str, default: str | None = None) -> str | None: ...

        def iter(self, tag: str | None = None) -> Iterable[_ElementLike]: ...

        def itertext(self) -> Iterator[str]: ...

        def __iter__(self) -> Iterator[_ElementLike]: ...


__all__ = ["XMLTVParser", "XMLTVParserError"]

_TIMESTAMP_RE = re.compile(r"^(?P<value>\d{14})(?:\s*(?P<timezone>Z|[+-]\d{4}))?$")


class XMLTVParserError(ValueError):
    """Raised when XMLTV data cannot be represented safely as programme entries."""


class XMLTVParser:
    """Parse a safe subset of XMLTV entries for explicitly mapped source channels."""

    def __init__(
        self,
        *,
        max_document_characters: int = 10_000_000,
        max_entries: int = 10_000,
    ) -> None:
        if max_document_characters <= 0:
            raise ValueError("max_document_characters must be positive")
        if max_entries <= 0:
            raise ValueError("max_entries must be positive")
        self._max_document_characters = max_document_characters
        self._max_entries = max_entries

    def parse(
        self,
        text: str,
        channel_mapping: Mapping[str, ChannelId],
    ) -> tuple[EPGEntry, ...]:
        """Return bounded canonical entries for explicitly mapped XMLTV channel IDs.

        XMLTV documents commonly include programmes for many channels. Entries with
        unmapped source channel IDs are ignored; any malformed entry for a mapped
        channel is rejected so a caller cannot silently display an incorrect guide.
        """
        if len(text) > self._max_document_characters:
            raise XMLTVParserError("XMLTV document exceeds the configured size limit")
        root = self._root(text)
        if self._local_name(root.tag) != "tv":
            raise XMLTVParserError("XMLTV document must have a tv root element")

        entries: list[EPGEntry] = []
        for programme in root.iter():
            if self._local_name(programme.tag) != "programme":
                continue
            source_channel_id = (programme.get("channel", "") or "").strip()
            channel_id = channel_mapping.get(source_channel_id)
            if channel_id is None:
                continue
            entries.append(self._entry(programme, channel_id, source_channel_id))
            if len(entries) >= self._max_entries:
                break
        return tuple(entries)

    @staticmethod
    def _root(text: str) -> _ElementLike:
        try:
            return cast("_ElementLike", fromstring(text))
        except (DefusedXmlException, ParseError) as exc:
            raise XMLTVParserError("XMLTV document is not well-formed or is unsafe") from exc

    @staticmethod
    def _entry(programme: _ElementLike, channel_id: ChannelId, source_channel_id: str) -> EPGEntry:
        start = XMLTVParser._timestamp(programme.get("start"), field="start")
        end = XMLTVParser._timestamp(programme.get("stop"), field="stop")
        title = XMLTVParser._required_child_text(programme, "title")
        try:
            return EPGEntry(
                id=XMLTVParser._entry_id(channel_id, source_channel_id, start, title),
                channel_id=channel_id,
                title=title,
                start=start,
                end=end,
                description=XMLTVParser._optional_child_text(programme, "desc"),
                category=XMLTVParser._optional_child_text(programme, "category"),
            )
        except ValidationError as exc:
            raise XMLTVParserError("Mapped XMLTV programme has an invalid schedule") from exc

    @staticmethod
    def _timestamp(value: str | None, *, field: str) -> datetime:
        if value is None:
            raise XMLTVParserError(f"Mapped XMLTV programme is missing {field}")
        match = _TIMESTAMP_RE.fullmatch(value.strip())
        if match is None:
            raise XMLTVParserError(f"Mapped XMLTV programme has an invalid {field} timestamp")
        timezone = match.group("timezone")
        timestamp = match.group("value")
        try:
            if timezone is None:
                return datetime.strptime(timestamp, "%Y%m%d%H%M%S").replace(tzinfo=UTC)
            normalized_timezone = "+0000" if timezone == "Z" else timezone
            return datetime.strptime(f"{timestamp} {normalized_timezone}", "%Y%m%d%H%M%S %z")
        except ValueError as exc:
            raise XMLTVParserError(
                f"Mapped XMLTV programme has an invalid {field} timestamp"
            ) from exc

    @staticmethod
    def _required_child_text(programme: _ElementLike, name: str) -> str:
        value = XMLTVParser._optional_child_text(programme, name)
        if value is None:
            raise XMLTVParserError(f"Mapped XMLTV programme is missing {name}")
        return value

    @staticmethod
    def _optional_child_text(programme: _ElementLike, name: str) -> str | None:
        for child in programme:
            if XMLTVParser._local_name(child.tag) != name:
                continue
            value = "".join(child.itertext()).strip()
            if value:
                return value
        return None

    @staticmethod
    def _entry_id(
        channel_id: ChannelId,
        source_channel_id: str,
        start: datetime,
        title: str,
    ) -> str:
        material = "\x00".join((source_channel_id, start.isoformat(), title)).encode()
        digest = hashlib.sha256(material).hexdigest()[:20]
        return f"{channel_id.value}:xmltv:{digest}"

    @staticmethod
    def _local_name(tag: str) -> str:
        return tag.rsplit("}", maxsplit=1)[-1]
