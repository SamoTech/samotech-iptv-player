"""Tests for domain value-object validation, secrecy, and value semantics."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from samotech_iptv.core.exceptions import ValidationError
from samotech_iptv.domain.value_objects.channel_id import ChannelId
from samotech_iptv.domain.value_objects.credential import Credential
from samotech_iptv.domain.value_objects.provider_id import ProviderId
from samotech_iptv.domain.value_objects.stream_id import StreamId
from samotech_iptv.domain.value_objects.url import URL

if TYPE_CHECKING:
    from collections.abc import Callable


_AUTH_VALUE = "test-only-secret"  # noqa: S105


@pytest.mark.parametrize(
    ("factory", "label"),
    [
        (ChannelId, "ChannelId"),
        (ProviderId, "ProviderId"),
        (StreamId, "StreamId"),
    ],
)
def test_identifier_value_objects_accept_nonblank_values(
    factory: Callable[[str], object], label: str
) -> None:
    """Every identifier value object accepts an opaque nonblank identifier."""
    value_object = factory("opaque-identifier")

    assert str(value_object) == "opaque-identifier"
    assert label in type(value_object).__name__


@pytest.mark.parametrize(
    ("factory", "label"),
    [
        (ChannelId, "ChannelId"),
        (ProviderId, "ProviderId"),
        (StreamId, "StreamId"),
    ],
)
def test_identifier_value_objects_reject_blank_values(
    factory: Callable[[str], object], label: str
) -> None:
    """Every identifier value object rejects blank input at construction time."""
    with pytest.raises(ValidationError, match=label):
        factory(" ")


@pytest.mark.parametrize(
    "factory",
    [ChannelId, ProviderId, StreamId],
)
def test_identifier_value_objects_use_value_semantics(factory: Callable[[str], object]) -> None:
    """Equivalent immutable identifier values compare and hash equally."""
    first = factory("opaque-identifier")
    second = factory("opaque-identifier")

    assert first == second
    assert hash(first) == hash(second)


def test_credential_accepts_valid_values_and_hides_the_password() -> None:
    """Credentials expose a password only through their explicit property, never string output."""
    secret = _AUTH_VALUE
    credential = Credential(username="subscriber", _password=secret)

    assert credential.password == secret
    assert secret not in repr(credential)
    assert secret not in str(credential)
    assert "subscriber" in repr(credential)


@pytest.mark.parametrize(
    ("username", "password", "message"),
    [
        (" ", "test-only-secret", "Username"),
        ("subscriber", "", "Password"),
    ],
)
def test_credential_rejects_missing_authentication_metadata(
    username: str, password: str, message: str
) -> None:
    """Credentials reject blank usernames and empty passwords."""
    with pytest.raises(ValidationError, match=message):
        Credential(username=username, _password=password)


def test_credential_uses_value_semantics() -> None:
    """Equivalent immutable Credential records compare and hash equally."""
    first = Credential(username="subscriber", _password=_AUTH_VALUE)
    second = Credential(username="subscriber", _password=_AUTH_VALUE)

    assert first == second
    assert hash(first) == hash(second)


@pytest.mark.parametrize(
    "value",
    [
        "https://portal.example.test",
        "http://stream.example.test/live/channel.m3u8?token=test#fragment",
    ],
)
def test_url_accepts_complete_http_urls(value: str) -> None:
    """The URL value object accepts complete HTTP(S) endpoints without whitespace."""
    url = URL(value)

    assert str(url) == value


@pytest.mark.parametrize(
    "value",
    [
        "not-a-url",
        "ftp://files.example.test/list.m3u",
        "https://",
        "http:///missing-authority",
        "https://portal.example.test trailing-text",
        "https://[invalid-host",
    ],
)
def test_url_rejects_malformed_or_non_http_values(value: str) -> None:
    """URLs must be complete, HTTP(S), authority-bearing, and whitespace-free."""
    with pytest.raises(ValidationError, match="Invalid URL"):
        URL(value)


def test_url_uses_value_semantics() -> None:
    """Equivalent immutable URL values compare and hash equally."""
    first = URL("https://portal.example.test")
    second = URL("https://portal.example.test")

    assert first == second
    assert hash(first) == hash(second)
