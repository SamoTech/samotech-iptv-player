"""Parse extended M3U playlists into canonical channel and stream entities."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import TYPE_CHECKING

from samotech_iptv.core.exceptions import ValidationError
from samotech_iptv.core.logging import get_logger
from samotech_iptv.domain.entities.channel import Channel
from samotech_iptv.domain.entities.stream import Stream
from samotech_iptv.domain.value_objects.channel_id import ChannelId
from samotech_iptv.domain.value_objects.stream_id import StreamId
from samotech_iptv.domain.value_objects.stream_uri import StreamURI
from samotech_iptv.domain.value_objects.url import URL

if TYPE_CHECKING:
    from samotech_iptv.domain.value_objects.provider_id import ProviderId

__all__ = ["M3UParser", "M3UParserError", "ParsedM3UPlaylist"]

_ATTRIBUTE_RE = re.compile(r"([\w-]+)=(?:\"([^\"]*)\"|'([^']*)'|([^\s,]+))")
_SAFE_IDENTIFIER_RE = re.compile(r"[^a-z0-9]+")
_LOG = get_logger(__name__)


class M3UParserError(ValueError):
    """Raised when an extended M3U document cannot be represented safely."""


@dataclass(frozen=True)
class ParsedM3UPlaylist:
    """Canonical content produced from one extended M3U document.

    Channel and stream entries are ordered exactly as they appeared in the
    source playlist. Each channel's ``stream_id`` is the ID of its companion
    ``Stream`` entity.
    """

    channels: tuple[Channel, ...]
    streams: tuple[Stream, ...]

    def stream_for(self, channel: Channel) -> Stream:
        """Return the stream associated with a parsed channel.

        Raises:
            KeyError: If the supplied channel was not produced by this result.
        """
        for stream in self.streams:
            if stream.id == channel.stream_id:
                return stream
        raise KeyError(f"No stream was parsed for channel {channel.id.value!r}")


@dataclass(frozen=True)
class _PendingEntry:
    """Extended-M3U metadata waiting for its following stream URL."""

    line_number: int
    attributes: dict[str, str]
    name: str


class M3UParser:
    """Translate an extended M3U playlist into canonical channel and stream entities."""

    def parse(self, text: str, provider_id: ProviderId) -> ParsedM3UPlaylist:
        """Parse a playlist string using the supplied canonical provider ID.

        The parser supports ``#EXTINF`` attributes including ``tvg-id``,
        ``tvg-name``, ``tvg-logo``, ``group-title``, and ``tvg-chno``. A stream
        URI must follow every ``#EXTINF`` entry. Supported non-HTTP media
        transports are preserved in the domain ``StreamURI`` value object for
        later protocol classification and player-capability negotiation.
        """
        lines = text.lstrip("\ufeff").splitlines()
        if not lines or not lines[0].strip().upper().startswith("#EXTM3U"):
            raise M3UParserError("An extended M3U playlist must start with #EXTM3U")

        channels: list[Channel] = []
        streams: list[Stream] = []
        pending: _PendingEntry | None = None
        occurrences: dict[str, int] = {}

        for line_number, raw_line in enumerate(lines[1:], start=2):
            line = raw_line.strip()
            if not line:
                continue
            if line.upper().startswith("#EXTINF:"):
                if pending is not None:
                    raise M3UParserError(f"Line {pending.line_number} has no following stream URL")
                pending = self._parse_extinf(line, line_number)
                continue
            if line.startswith("#"):
                continue
            if pending is None:
                raise M3UParserError(
                    f"Line {line_number} contains a stream URL without #EXTINF metadata"
                )

            channel, stream = self._to_domain(pending, line, provider_id, occurrences)
            channels.append(channel)
            streams.append(stream)
            pending = None

        if pending is not None:
            raise M3UParserError(f"Line {pending.line_number} has no following stream URL")
        return ParsedM3UPlaylist(channels=tuple(channels), streams=tuple(streams))

    @staticmethod
    def _parse_extinf(line: str, line_number: int) -> _PendingEntry:
        try:
            metadata, name = M3UParser._split_extinf_metadata_and_name(line)
        except ValueError as exc:
            raise M3UParserError(
                f"Line {line_number} is missing the channel-name separator"
            ) from exc
        attributes = {
            key.lower(): double_quoted or single_quoted or unquoted
            for key, double_quoted, single_quoted, unquoted in _ATTRIBUTE_RE.findall(metadata)
        }
        display_name = name.strip() or attributes.get("tvg-name", "").strip()
        if not display_name:
            raise M3UParserError(f"Line {line_number} has no channel name")
        return _PendingEntry(
            line_number=line_number,
            attributes=attributes,
            name=display_name,
        )

    @staticmethod
    def _split_extinf_metadata_and_name(line: str) -> tuple[str, str]:
        """Split EXTINF fields at the first comma outside a quoted attribute value."""
        quote: str | None = None
        escaped = False
        for index, character in enumerate(line):
            if quote is not None:
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == quote:
                    quote = None
                continue
            if character in {"'", '"'}:
                quote = character
                continue
            if character == ",":
                return line[:index], line[index + 1 :]
        raise ValueError("EXTINF separator not found")

    @staticmethod
    def _to_domain(
        entry: _PendingEntry,
        raw_stream_url: str,
        provider_id: ProviderId,
        occurrences: dict[str, int],
    ) -> tuple[Channel, Stream]:
        attributes = entry.attributes
        base_identifier = attributes.get("tvg-id") or attributes.get("tvg-name") or entry.name
        identifier = M3UParser._next_identifier(base_identifier, occurrences)
        channel_id = ChannelId(f"{provider_id.value}:{identifier}")
        stream_id = StreamId(channel_id.value)
        stream_url = M3UParser._stream_uri(raw_stream_url, entry.line_number)
        logo_url = M3UParser._optional_logo_url(attributes.get("tvg-logo"), entry.line_number)

        channel = Channel(
            id=channel_id,
            name=entry.name,
            provider_id=provider_id,
            stream_id=stream_id,
            category_id=attributes.get("group-title") or None,
            logo_url=logo_url,
            epg_channel_id=attributes.get("tvg-id") or None,
            number=M3UParser._channel_number(attributes.get("tvg-chno"), entry.line_number),
        )
        stream = Stream(
            id=stream_id,
            url=stream_url,
            container=M3UParser._container_for(stream_url),
        )
        return channel, stream

    @staticmethod
    def _next_identifier(value: str, occurrences: dict[str, int]) -> str:
        normalized = _SAFE_IDENTIFIER_RE.sub("-", value.lower()).strip("-") or "channel"
        occurrence = occurrences.get(normalized, 0) + 1
        occurrences[normalized] = occurrence
        return normalized if occurrence == 1 else f"{normalized}-{occurrence}"

    @staticmethod
    def _stream_uri(value: str, line_number: int) -> StreamURI:
        try:
            return StreamURI(value)
        except ValidationError as exc:
            raise M3UParserError(f"Line {line_number} has an invalid stream URL") from exc

    @staticmethod
    def _optional_logo_url(value: str | None, line_number: int) -> URL | None:
        if not value:
            return None
        try:
            return URL(value)
        except ValidationError:
            _LOG.warning("Ignoring invalid optional M3U logo URL at line=%d", line_number)
            return None

    @staticmethod
    def _channel_number(value: str | None, line_number: int) -> int | None:
        if not value:
            return None
        try:
            return int(value)
        except ValueError as exc:
            raise M3UParserError(f"Line {line_number} has an invalid tvg-chno value") from exc

    @staticmethod
    def _container_for(url: StreamURI) -> str:
        suffix = PurePosixPath(url.value.split("?", maxsplit=1)[0]).suffix.lstrip(".").lower()
        return suffix or "unknown"
