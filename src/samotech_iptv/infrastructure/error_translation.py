"""Error translation layer — maps infrastructure exceptions to domain errors.

Infrastructure details (HTTP status codes, keyring failures, timeouts)
should NEVER leak into the application or domain layers.  Every adapter
must pass exceptions through this module before re-raising.

Translation table::

    HttpTimeoutError     →  NetworkError   ("request timed out")
    HttpConnectionError  →  NetworkError   ("connection failed")
    HttpServerError      →  ProviderError  ("provider returned 5xx")
    HttpClientError 401  →  AuthenticationError
    HttpClientError 403  →  AuthenticationError
    HttpClientError 4xx  →  ProviderError
    StorageError         →  StorageError   (pass-through, already domain)
    Exception (other)    →  ProviderError  ("unexpected error")
"""
from __future__ import annotations

from samotech_iptv.core.exceptions import (
    AuthenticationError,
    NetworkError,
    ProviderError,
    SamotechError,
)
from samotech_iptv.core.logging import get_logger
from samotech_iptv.infrastructure.network.exceptions import (
    HttpClientError,
    HttpConnectionError,
    HttpServerError,
    HttpTimeoutError,
)

__all__ = ["translate_error", "translate_and_raise"]

_log = get_logger(__name__)


def translate_error(exc: Exception) -> SamotechError:
    """Map an infrastructure exception to the appropriate domain error.

    Args:
        exc: Any exception raised inside an infrastructure adapter.

    Returns:
        A ``SamotechError`` subclass that is safe to surface upward.
    """
    if isinstance(exc, SamotechError):
        # Already a domain error — pass through
        return exc

    if isinstance(exc, HttpTimeoutError):
        _log.debug("Translating HttpTimeoutError -> NetworkError")
        return NetworkError(f"Request timed out: {exc}")

    if isinstance(exc, HttpConnectionError):
        _log.debug("Translating HttpConnectionError -> NetworkError")
        return NetworkError(f"Connection failed: {exc}")

    if isinstance(exc, HttpClientError):
        status = exc.status_code
        if status in (401, 403):
            _log.debug("Translating HttpClientError %d -> AuthenticationError", status)
            return AuthenticationError(f"Authentication failed (HTTP {status}): {exc}")
        _log.debug("Translating HttpClientError %d -> ProviderError", status)
        return ProviderError(f"Provider client error (HTTP {status}): {exc}")

    if isinstance(exc, HttpServerError):
        _log.debug("Translating HttpServerError %d -> ProviderError",
                   exc.status_code)
        return ProviderError(f"Provider server error (HTTP {exc.status_code}): {exc}")

    _log.warning("Translating unexpected %s -> ProviderError", type(exc).__name__)
    return ProviderError(f"Unexpected provider error: {exc}")


def translate_and_raise(exc: Exception) -> None:
    """Translate ``exc`` and immediately raise the domain error.

    Convenience wrapper for the common ``raise translate_error(exc)`` pattern.
    """
    raise translate_error(exc) from exc
