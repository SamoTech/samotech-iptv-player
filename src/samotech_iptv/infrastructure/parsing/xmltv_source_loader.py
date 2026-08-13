"""Local-only text loading for configured XMLTV guide sources."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Protocol
from urllib.parse import unquote, urlsplit

__all__ = ["LocalXMLTVSourceLoader", "XMLTVSourceError", "XMLTVSourceLoaderPort"]


class XMLTVSourceError(ValueError):
    """Raised when a configured XMLTV source cannot be loaded safely."""


class XMLTVSourceLoaderPort(Protocol):
    """Boundary for loading text from an already validated local XMLTV source."""

    async def load(self, source: str) -> str:
        """Return XMLTV document text or raise ``XMLTVSourceError``."""


class LocalXMLTVSourceLoader:
    """Load XMLTV text from a local path or a local ``file:`` URI only."""

    async def load(self, source: str) -> str:
        """Read the configured local XMLTV source without a network transport path."""
        path = self._local_path(source)
        try:
            return await asyncio.to_thread(path.read_text, encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise XMLTVSourceError("Unable to read configured XMLTV source") from exc

    @staticmethod
    def _local_path(source: str) -> Path:
        parsed = urlsplit(source)
        scheme = parsed.scheme.casefold()
        if scheme not in {"", "file"}:
            raise XMLTVSourceError("XMLTV source must use a local path or file URI")
        if scheme == "file":
            if parsed.netloc or parsed.query or parsed.fragment:
                raise XMLTVSourceError("XMLTV source must identify a local file")
            return Path(unquote(parsed.path))
        return Path(source)
