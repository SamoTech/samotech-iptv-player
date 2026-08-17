"""Load M3U source text through local-file or shared HTTP boundaries."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Protocol
from urllib.parse import unquote, urlsplit

from samotech_iptv.core.diagnostics import log_exception
from samotech_iptv.core.exceptions import ValidationError
from samotech_iptv.core.logging import get_logger
from samotech_iptv.core.safe_logging import sanitize_url
from samotech_iptv.domain.value_objects.url import URL
from samotech_iptv.infrastructure.network.exceptions import HttpError
from samotech_iptv.infrastructure.network.timeouts import TimeoutConfig

if TYPE_CHECKING:
    from samotech_iptv.infrastructure.network.http_client import AsyncHttpClient

__all__ = ["M3USourceError", "M3USourceLoader", "M3USourceLoaderPort"]

_LOG = get_logger(__name__)
_M3U_REMOTE_TIMEOUT = TimeoutConfig(connect=20.0, read=180.0, total=240.0)


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
        if self._is_windows_drive_path(source):
            return await self._load_local(Path(source))
        parsed = urlsplit(source)
        if parsed.scheme.casefold() in {"http", "https"}:
            return await self._load_remote(source)
        if parsed.scheme and parsed.scheme.casefold() != "file":
            _LOG.error("M3U source stage=scheme unsupported scheme=%s", parsed.scheme)
            raise M3USourceError(f"Unsupported M3U source scheme: {parsed.scheme!r}")
        return await self._load_local(self._local_path(source, parsed.scheme.casefold()))

    async def _load_remote(self, source: str) -> str:
        safe_source = self._redact_source(source)
        _LOG.debug("M3U source stage=http_request source=%s", safe_source)
        try:
            remote_url = URL(source)
            text = await self._http_client.get_text(
                str(remote_url),
                timeout=_M3U_REMOTE_TIMEOUT,
            )
            _LOG.debug(
                "M3U source stage=content_retrieval source=%s bytes=%d", safe_source, len(text)
            )
            return text
        except asyncio.CancelledError:
            raise
        except (HttpError, ValidationError) as exc:
            log_exception(_LOG, "M3U source stage=http_or_url", exc, source=safe_source)
            raise M3USourceError("Unable to load remote M3U source") from exc
        except Exception as exc:  # noqa: BLE001
            log_exception(_LOG, "M3U source stage=unexpected_transport", exc, source=safe_source)
            raise M3USourceError("Unable to load remote M3U source") from exc

    @staticmethod
    async def _load_local(path: Path) -> str:
        try:
            text = await asyncio.to_thread(path.read_text, encoding="utf-8")
            _LOG.debug(
                "M3U source stage=content_retrieval source_kind=local_file bytes=%d", len(text)
            )
            return text
        except (OSError, UnicodeDecodeError) as exc:
            log_exception(_LOG, "M3U source stage=local_read", exc, source_kind="local_file")
            raise M3USourceError("Unable to read local M3U source") from exc

    @staticmethod
    def _local_path(source: str, scheme: str) -> Path:
        if M3USourceLoader._is_windows_drive_path(source):
            return Path(source)
        if scheme == "file":
            path = unquote(urlsplit(source).path)
            if sys.platform == "win32" and path.startswith("/") and len(path) >= 3:
                path = path[1:]
            return Path(path)
        return Path(source)

    @staticmethod
    def _is_windows_drive_path(source: str) -> bool:
        return len(source) >= 3 and source[1] == ":" and source[2] in {"/", "\\"}

    @staticmethod
    def _redact_source(source: str) -> str:
        """Keep only the safe origin/path portion of a potentially tokenized source."""
        parsed = urlsplit(source)
        if not parsed.scheme or not parsed.netloc:
            return "<local-source>"
        return sanitize_url(source)
