"""Base exception hierarchy.

All application exceptions inherit from ``SamotechError`` so callers
can catch the entire family with a single ``except SamotechError``.
"""

from __future__ import annotations

__all__ = [
    "SamotechError",
    "ConfigurationError",
    "ValidationError",
    "NotFoundError",
    "AuthenticationError",
    "AuthorisationError",
    "NetworkError",
    "TimeoutError",
    "ProviderError",
    "StorageError",
]


class SamotechError(Exception):
    """Root exception for all application errors."""


class ConfigurationError(SamotechError):
    """Invalid or missing configuration value."""


class ValidationError(SamotechError):
    """Domain validation rule violated."""

    def __init__(self, field: str, message: str) -> None:
        self.field = field
        super().__init__(f"{field}: {message}")


class NotFoundError(SamotechError):
    """Requested resource does not exist."""

    def __init__(self, resource: str, identifier: object) -> None:
        self.resource = resource
        self.identifier = identifier
        super().__init__(f"{resource} not found: {identifier!r}")


class AuthenticationError(SamotechError):
    """Credentials rejected by the provider."""


class AuthorisationError(SamotechError):
    """Authenticated user lacks required permission."""


class NetworkError(SamotechError):
    """Network-level failure (DNS, TCP, TLS)."""


class TimeoutError(SamotechError):  # noqa: A001
    """Operation exceeded its time limit."""


class ProviderError(SamotechError):
    """Provider-specific error (wraps underlying cause)."""


class StorageError(SamotechError):
    """Persistence layer failure."""
