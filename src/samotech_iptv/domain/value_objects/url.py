"""URL value object — a validated HTTP/HTTPS URL."""

from __future__ import annotations

import re
from dataclasses import dataclass

from samotech_iptv.core.exceptions import ValidationError

__all__ = ["URL"]

_URL_RE = re.compile(r"^https?://\S+", re.IGNORECASE)


@dataclass(frozen=True)
class URL:
    """A validated HTTP/HTTPS URL."""

    value: str

    def __post_init__(self) -> None:
        if not _URL_RE.match(self.value):
            raise ValidationError("value", f"Invalid URL: {self.value!r}")

    def __str__(self) -> str:
        return self.value
