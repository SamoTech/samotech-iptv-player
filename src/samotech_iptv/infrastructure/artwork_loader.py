"""Bounded artwork loading through the existing shared HTTP client."""

from __future__ import annotations

import asyncio
from collections import OrderedDict
from dataclasses import dataclass
from time import monotonic
from typing import TYPE_CHECKING
from urllib.parse import parse_qsl, urlsplit

from samotech_iptv.application.ports.artwork_port import ArtworkPort, ArtworkRequest

if TYPE_CHECKING:
    from samotech_iptv.infrastructure.network.http_client import AsyncHttpClient

__all__ = ["BoundedArtworkLoader", "is_safe_artwork_url"]

_MAX_ARTWORK_BYTES = 4 * 1024 * 1024
_MAX_CACHE_BYTES = 16 * 1024 * 1024
_MAX_CACHE_ENTRIES = 64
_CACHE_TTL_SECONDS = 20 * 60
_DISALLOWED_QUERY_KEYS = frozenset(
    {
        "api_key",
        "apikey",
        "auth",
        "authorization",
        "cookie",
        "key",
        "password",
        "passwd",
        "secret",
        "token",
        "user",
        "username",
    }
)


def is_safe_artwork_url(value: str) -> bool:
    """Return whether a URL is suitable for non-secret artwork retrieval."""
    try:
        parsed = urlsplit(value)
    except ValueError:
        return False
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or any(character.isspace() for character in value)
    ):
        return False
    return not any(
        key.casefold() in _DISALLOWED_QUERY_KEYS
        for key, _ in parse_qsl(parsed.query, keep_blank_values=True)
    )


@dataclass(frozen=True)
class _CacheEntry:
    payload: bytes
    expires_at: float


class BoundedArtworkLoader(ArtworkPort):
    """Load image bytes with provider-scoped stale-safe bounded caching."""

    def __init__(
        self,
        http_client: AsyncHttpClient,
        *,
        max_entries: int = _MAX_CACHE_ENTRIES,
        max_cache_bytes: int = _MAX_CACHE_BYTES,
        ttl_seconds: float = _CACHE_TTL_SECONDS,
        max_artwork_bytes: int = _MAX_ARTWORK_BYTES,
    ) -> None:
        if max_entries < 1 or max_cache_bytes < 1 or ttl_seconds <= 0 or max_artwork_bytes < 1:
            raise ValueError("Artwork cache limits must be positive")
        self._http_client = http_client
        self._max_entries = max_entries
        self._max_cache_bytes = max_cache_bytes
        self._ttl_seconds = ttl_seconds
        self._max_artwork_bytes = max_artwork_bytes
        self._cache: OrderedDict[tuple[str, str, str, str], _CacheEntry] = OrderedDict()
        self._cache_bytes = 0
        self._cache_lock = asyncio.Lock()

    @property
    def cache_entries(self) -> int:
        """Return the current bounded entry count for deterministic diagnostics/tests."""
        return len(self._cache)

    @property
    def cache_bytes(self) -> int:
        """Return the current bounded payload size for deterministic diagnostics/tests."""
        return self._cache_bytes

    async def load(self, request: ArtworkRequest) -> bytes | None:
        """Return cached/fetched image bytes, or ``None`` for unsafe/failed data."""
        if (
            not request.provider_id
            or not request.content_id
            or not is_safe_artwork_url(request.url)
        ):
            return None
        key = (request.provider_id, request.content_id, request.role.value, request.url)
        cached = await self._get_cached(key)
        if cached is not None:
            return cached
        try:
            payload = await self._http_client.get_bytes(
                request.url,
                max_bytes=self._max_artwork_bytes,
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            return None
        if not payload or len(payload) > self._max_artwork_bytes:
            return None
        await self._put_cached(key, payload)
        return payload

    def clear_provider(self, provider_id: str) -> None:
        """Remove all cached artwork for one provider without touching other providers."""
        if not provider_id:
            return
        for key in tuple(self._cache):
            if key[0] == provider_id:
                self._remove(key)

    def clear(self) -> None:
        """Remove all cached artwork."""
        self._cache.clear()
        self._cache_bytes = 0

    async def _get_cached(self, key: tuple[str, str, str, str]) -> bytes | None:
        async with self._cache_lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            if entry.expires_at <= monotonic():
                self._remove(key)
                return None
            self._cache.move_to_end(key)
            return entry.payload

    async def _put_cached(self, key: tuple[str, str, str, str], payload: bytes) -> None:
        async with self._cache_lock:
            self._remove(key)
            if len(payload) > self._max_cache_bytes:
                return
            self._cache[key] = _CacheEntry(payload, monotonic() + self._ttl_seconds)
            self._cache_bytes += len(payload)
            self._enforce_limits()

    def _enforce_limits(self) -> None:
        """Evict oldest entries until both cache limits hold."""
        while len(self._cache) > self._max_entries or self._cache_bytes > self._max_cache_bytes:
            _, entry = self._cache.popitem(last=False)
            self._cache_bytes -= len(entry.payload)

    def _remove(self, key: tuple[str, str, str, str]) -> None:
        entry = self._cache.pop(key, None)
        if entry is not None:
            self._cache_bytes -= len(entry.payload)
