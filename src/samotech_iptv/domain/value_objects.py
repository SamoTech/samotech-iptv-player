"""Value objects — immutable, self-validating primitives.

Value objects have no identity; two instances with equal values are
interchangeable.  They validate their own invariants on construction.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from samotech_iptv.core.exceptions import ValidationError

__all__ = ["ProviderId", "ChannelId", "StreamId", "Credential", "URL"]

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
_URL_RE = re.compile(r"^https?://\S+", re.IGNORECASE)


@dataclass(frozen=True)
class ProviderId:
    """Opaque identifier for a provider instance."""

    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValidationError("value", "ProviderId must not be blank")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class ChannelId:
    """Opaque identifier for a channel."""

    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValidationError("value", "ChannelId must not be blank")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class StreamId:
    """Opaque identifier for a stream."""

    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValidationError("value", "StreamId must not be blank")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class URL:
    """A validated HTTP/HTTPS URL."""

    value: str

    def __post_init__(self) -> None:
        if not _URL_RE.match(self.value):
            raise ValidationError("value", f"Invalid URL: {self.value!r}")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Credential:
    """A username / password pair.  Password is never logged or repr'd.

    .. warning::
        Do not serialise this object to logs or JSON.  Pass it only to
        ``CredentialStorePort`` implementations.
    """

    username: str
    _password: str

    def __post_init__(self) -> None:
        if not self.username.strip():
            raise ValidationError("username", "Username must not be blank")
        if not self._password:
            raise ValidationError("_password", "Password must not be empty")

    @property
    def password(self) -> str:  # noqa: D102
        return self._password

    def __repr__(self) -> str:
        return f"Credential(username={self.username!r}, password='***')"

    def __str__(self) -> str:
        return f"Credential(username={self.username!r})"
