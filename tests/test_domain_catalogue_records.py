"""Tests for catalogue grouping and provider domain-record invariants."""

from __future__ import annotations

import pytest

from samotech_iptv.core.exceptions import ValidationError
from samotech_iptv.domain.entities.category import Category
from samotech_iptv.domain.entities.playlist import Playlist
from samotech_iptv.domain.entities.provider import Provider
from samotech_iptv.domain.value_objects.channel_id import ChannelId
from samotech_iptv.domain.value_objects.provider_id import ProviderId
from samotech_iptv.domain.value_objects.url import URL


@pytest.fixture
def provider_id() -> ProviderId:
    """Return a reusable valid provider identity."""
    return ProviderId("catalogue-provider")


def test_category_accepts_valid_hierarchical_metadata(provider_id: ProviderId) -> None:
    """Categories retain valid provider ownership and optional parent linkage."""
    category = Category(
        id="sports-football",
        name="Football",
        provider_id=provider_id,
        parent_id="sports",
    )

    assert category.parent_id == "sports"


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("id", " ", "Category ID"),
        ("name", " ", "Category name"),
        ("parent_id", " ", "Parent category ID"),
    ],
)
def test_category_rejects_blank_required_or_supplied_text(
    provider_id: ProviderId, field: str, value: str, message: str
) -> None:
    """Category identifiers and labels cannot be blank, including an optional parent."""
    values: dict[str, object] = {
        "id": "sports-football",
        "name": "Football",
        "provider_id": provider_id,
        "parent_id": "sports",
    }
    values[field] = value

    with pytest.raises(ValidationError, match=message):
        Category(**values)  # type: ignore[arg-type]


def test_category_uses_value_semantics(provider_id: ProviderId) -> None:
    """Equivalent immutable Category records compare and hash equally."""
    first = Category(id="sports", name="Sports", provider_id=provider_id)
    second = Category(id="sports", name="Sports", provider_id=provider_id)

    assert first == second
    assert hash(first) == hash(second)


def test_playlist_accepts_valid_ordered_channel_references(provider_id: ProviderId) -> None:
    """Playlists preserve an ordered tuple of valid channel identifiers."""
    playlist = Playlist(
        id="weekend-sports",
        name="Weekend sports",
        provider_id=provider_id,
        channel_ids=(ChannelId("sports-1"), ChannelId("sports-2")),
    )

    assert playlist.channel_ids == (ChannelId("sports-1"), ChannelId("sports-2"))


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("id", " ", "Playlist ID"),
        ("name", " ", "Playlist name"),
    ],
)
def test_playlist_rejects_blank_required_text(
    provider_id: ProviderId, field: str, value: str, message: str
) -> None:
    """Playlist identifiers and names cannot be blank."""
    values: dict[str, object] = {
        "id": "weekend-sports",
        "name": "Weekend sports",
        "provider_id": provider_id,
    }
    values[field] = value

    with pytest.raises(ValidationError, match=message):
        Playlist(**values)  # type: ignore[arg-type]


def test_playlist_uses_value_semantics(provider_id: ProviderId) -> None:
    """Equivalent immutable Playlist records compare and hash equally."""
    first = Playlist(id="favorites", name="Favorites", provider_id=provider_id)
    second = Playlist(id="favorites", name="Favorites", provider_id=provider_id)

    assert first == second
    assert hash(first) == hash(second)


def test_provider_accepts_complete_valid_metadata(provider_id: ProviderId) -> None:
    """Providers accept valid discriminator, endpoint, and capability metadata."""
    provider = Provider(
        id=provider_id,
        name="Example provider",
        type="m3u",
        base_url=URL("https://iptv.example.test"),
        capabilities=("channels", "vod"),
    )

    assert provider.type == "m3u"


def test_provider_rejects_blank_type(provider_id: ProviderId) -> None:
    """The provider factory discriminator cannot be blank."""
    with pytest.raises(ValidationError, match="Provider type"):
        Provider(
            id=provider_id,
            name="Example provider",
            type=" ",
            base_url=URL("https://iptv.example.test"),
        )


def test_provider_uses_value_semantics(provider_id: ProviderId) -> None:
    """Equivalent immutable Provider records compare and hash equally."""
    first = Provider(
        id=provider_id,
        name="Example provider",
        type="m3u",
        base_url=URL("https://iptv.example.test"),
    )
    second = Provider(
        id=provider_id,
        name="Example provider",
        type="m3u",
        base_url=URL("https://iptv.example.test"),
    )

    assert first == second
    assert hash(first) == hash(second)
