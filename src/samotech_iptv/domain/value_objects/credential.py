"""Credential value object — username/password pair, never logged."""
from __future__ import annotations

from dataclasses import dataclass

from samotech_iptv.core.exceptions import ValidationError

__all__ = ["Credential"]


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
    def password(self) -> str:
        return self._password

    def __repr__(self) -> str:
        return f"Credential(username={self.username!r}, password='***')"

    def __str__(self) -> str:
        return f"Credential(username={self.username!r})"
