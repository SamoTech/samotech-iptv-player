from __future__ import annotations

import asyncio

import pytest

from samotech_iptv.application.ports.artwork_port import ArtworkRequest, ArtworkRole
from samotech_iptv.infrastructure.artwork_loader import (
    BoundedArtworkLoader,
    is_safe_artwork_url,
)


class FakeHttpClient:
    def __init__(self, payload: bytes = b"image-bytes") -> None:
        self.payload = payload
        self.calls: list[str] = []
        self.fail = False

    async def get_bytes(self, url: str, *, max_bytes: int) -> bytes:
        self.calls.append(url)
        if self.fail:
            raise RuntimeError("network failure")
        if len(self.payload) > max_bytes:
            raise RuntimeError("too large")
        return self.payload


def request(
    provider_id: str = "provider-a",
    content_id: str = "movie-1",
    url: str = "https://assets.example.test/movie.jpg",
) -> ArtworkRequest:
    return ArtworkRequest(provider_id, content_id, ArtworkRole.POSTER, url)


def test_artwork_url_policy_rejects_credentials_and_secret_query_keys() -> None:
    assert is_safe_artwork_url("https://assets.example.test/poster.jpg") is True
    assert is_safe_artwork_url("http://assets.example.test/poster.jpg?size=small") is True
    assert is_safe_artwork_url("https://user:password@assets.example.test/poster.jpg") is False
    assert is_safe_artwork_url("https://assets.example.test/poster.jpg?token=secret") is False
    assert is_safe_artwork_url("https://assets.example.test/poster.jpg?api_key=secret") is False
    assert is_safe_artwork_url("file:///tmp/poster.jpg") is False


@pytest.mark.asyncio
async def test_artwork_loader_caches_by_provider_content_role_and_url() -> None:
    client = FakeHttpClient()
    loader = BoundedArtworkLoader(client, max_entries=2, max_cache_bytes=32, ttl_seconds=60)

    first = await loader.load(request())
    second = await loader.load(request())

    assert first == b"image-bytes"
    assert second == first
    assert client.calls == ["https://assets.example.test/movie.jpg"]
    assert loader.cache_entries == 1
    assert loader.cache_bytes == len(b"image-bytes")


@pytest.mark.asyncio
async def test_artwork_loader_evicts_lru_entries_and_invalidates_one_provider() -> None:
    client = FakeHttpClient()
    loader = BoundedArtworkLoader(client, max_entries=2, max_cache_bytes=32, ttl_seconds=60)

    await loader.load(request(content_id="movie-1"))
    await loader.load(request(content_id="movie-2"))
    await loader.load(request(content_id="movie-3"))
    assert loader.cache_entries == 2
    assert loader.cache_bytes <= 32

    loader.clear_provider("provider-a")
    assert loader.cache_entries == 0
    assert loader.cache_bytes == 0

    await loader.load(request(provider_id="provider-b"))
    loader.clear_provider("provider-a")
    assert loader.cache_entries == 1


@pytest.mark.asyncio
async def test_artwork_loader_expires_entries_and_does_not_cache_failures() -> None:
    client = FakeHttpClient()
    loader = BoundedArtworkLoader(client, ttl_seconds=0.01)

    await loader.load(request())
    await asyncio.sleep(0.02)
    await loader.load(request())
    assert len(client.calls) == 2

    client.fail = True
    assert await loader.load(request(content_id="failed")) is None
    assert await loader.load(request(content_id="failed")) is None
    assert client.calls[-2:] == [
        "https://assets.example.test/movie.jpg",
        "https://assets.example.test/movie.jpg",
    ]


@pytest.mark.asyncio
async def test_artwork_loader_rejects_unsafe_and_oversized_payloads_without_cache() -> None:
    client = FakeHttpClient(payload=b"0123456789")
    loader = BoundedArtworkLoader(client, max_artwork_bytes=4)

    assert (
        await loader.load(request(url="https://assets.example.test/poster.jpg?password=x")) is None
    )
    assert client.calls == []
    assert await loader.load(request()) is None
    assert loader.cache_entries == 0
