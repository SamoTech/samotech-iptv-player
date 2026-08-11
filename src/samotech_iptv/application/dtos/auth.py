"""Authentication DTOs."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["AuthenticateRequest", "AuthenticateResponse"]


@dataclass(frozen=True)
class AuthenticateRequest:
    provider_id: str
    username: str
    password: str


@dataclass(frozen=True)
class AuthenticateResponse:
    success: bool
    provider_id: str
    error: str | None = None
