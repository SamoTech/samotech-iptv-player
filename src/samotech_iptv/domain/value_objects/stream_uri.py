"""StreamURI value object — validated URI for a provider-independent media stream."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit

from samotech_iptv.core.exceptions import ValidationError
from samotech_iptv.core.safe_logging import safe_label

from .stream_protocol import StreamTransport

__all__ = ["StreamURI"]

_SUPPORTED_SCHEMES = frozenset(transport.value for transport in StreamTransport) - {
    StreamTransport.UNKNOWN.value
}


@dataclass(frozen=True)
class StreamURI:
    """A whitespace-free URI using a transport the domain can represent."""

    value: str

    def __post_init__(self) -> None:
        try:
            parsed = urlsplit(self.value)
        except ValueError:
            raise ValidationError(
                "value", f"Invalid stream URI: {safe_label(self.value)}"
            ) from None

        if (
            parsed.scheme.casefold() not in _SUPPORTED_SCHEMES
            or not parsed.netloc
            or any(character.isspace() for character in self.value)
        ):
            raise ValidationError("value", f"Invalid stream URI: {safe_label(self.value)}")

    def __str__(self) -> str:
        return self.value
