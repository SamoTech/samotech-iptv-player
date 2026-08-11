"""Local and remote source loading for extended M3U playlists."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Protocol
from urllib.parse import unquote, urlsplit

from samotech_iptv.core.exceptions import ValidationError
from samotech_iptv.domain.value_objects.url import URL
from samotech_iptv.infrastructure.network.exceptions import HttpError

if TYPE_CHECKING:
    from samotech_iptv.infrastructure.network.http_client import AsyncHttpClient

__all__ = ["M3USourceLoader", "M3USourceLoaderPort", "M3USourceError"]


class M3USourceError(ValueError):
    """Raised when an M3U source cannot be loaded safely."""


class M3USourceLoaderPort(Protocol):
    """Boundary for loading playlist text from a configured source."""

    async def load(self, source: str) -> str:
        """Return source text or raise ``M3USourceError``."""


class M3USourceLoader:
    """Load M3U content from local paths, file URIs, or remote HTTP(S) URLs."""

    def __init__(self, http_client: AsyncHttpClient) -> None:
        self._http_client = http_client

    async def load(self, source: str) -> str:
        """Load a local file or HTTP(S) playlist source through its proper boundary."""
        parsed = urlsplit(source)
        if parsed.scheme.casefold() in {"http", "https"}:
            return await self._load_remote(source)
        if parsed.scheme and parsed.scheme.casefold() != "file":
            raise M3USourceError(f"Unsupported M3U source scheme: {parsed.scheme!r}")
        return await self._load_local(self._local_path(source, parsed.scheme.casefold()))

    async def _load_remote(self, source: str) -> str:
        try:
            remote_url = URL(source)
            return await self._http_client.get_text(str(remote_url))
        except asyncio.CancelledError:
            raise
        except (HttpError, ValidationError) as exc:
            raise M3USourceError(f"Unable to load remote M3U source: {source!r}") from exc

    @staticmethod
    async def _load_local(path: Path) -> str:
        try:
            return await asyncio.to_thread(path.read_text, encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise M3USourceError(f"Unable to read local M3U source: {path!s}") from exc

    @staticmethod
    def _local_path(source: str, scheme: str) -> Path:
        if scheme == "file":
            return Path(unquote(urlsplit(source).path))
        return Path(source)
