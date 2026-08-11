"""HTTP-layer exception hierarchy.

All exceptions in this module are infrastructure-internal.
Callers should catch ``samotech_iptv.core.exceptions.NetworkError``
or ``ProviderError`` which are produced by the error translation layer.
"""

from __future__ import annotations

__all__ = [
    "HttpError",
    "HttpTimeoutError",
    "HttpClientError",
    "HttpServerError",
    "HttpConnectionError",
]


class HttpError(Exception):
    """Base class for all HTTP infrastructure errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.args[0]!r}, status={self.status_code})"


class HttpConnectionError(HttpError):
    """Raised when a TCP connection cannot be established."""


class HttpTimeoutError(HttpError):
    """Raised when a request exceeds configured timeout limits."""


class HttpClientError(HttpError):
    """Raised for 4xx HTTP responses."""


class HttpServerError(HttpError):
    """Raised for 5xx HTTP responses."""
