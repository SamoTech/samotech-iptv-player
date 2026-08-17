"""URL value object — a validated HTTP/HTTPS URL."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit

from samotech_iptv.core.exceptions import ValidationError
from samotech_iptv.core.safe_logging import safe_label

__all__ = ["URL"]


@dataclass(frozen=True)
class URL:
    """A validated HTTP/HTTPS URL."""

    value: str

    def __post_init__(self) -> None:
        try:
            parsed = urlsplit(self.value)
        except ValueError:
            raise ValidationError("value", f"Invalid URL: {safe_label(self.value)}") from None

        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.netloc
            or any(character.isspace() for character in self.value)
        ):
            raise ValidationError("value", f"Invalid URL: {safe_label(self.value)}")

    def __str__(self) -> str:
        return self.value
