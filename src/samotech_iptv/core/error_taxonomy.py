"""Credential-free user-facing error classification."""

from __future__ import annotations

from enum import StrEnum

from samotech_iptv.core.exceptions import (
    AuthenticationError,
    AuthorisationError,
    ConfigurationError,
    NetworkError,
    NotFoundError,
    ProviderError,
    SamotechError,
    StorageError,
    TimeoutError,
    ValidationError,
)

__all__ = ["UserErrorCode", "safe_user_message"]


class UserErrorCode(StrEnum):
    """Stable presentation categories for failures crossing the application boundary."""

    AUTHENTICATION = "authentication"
    AUTHORISATION = "authorisation"
    CONFIGURATION = "configuration"
    NETWORK = "network"
    TIMEOUT = "timeout"
    PROVIDER = "provider"
    STORAGE = "storage"
    NOT_FOUND = "not_found"
    INVALID_INPUT = "invalid_input"
    UNSUPPORTED = "unsupported"
    UNKNOWN = "unknown"


_MESSAGES = {
    UserErrorCode.AUTHENTICATION: "Authentication failed",
    UserErrorCode.AUTHORISATION: "The provider denied this action",
    UserErrorCode.CONFIGURATION: "The provider configuration is invalid",
    UserErrorCode.NETWORK: "The provider network is unavailable",
    UserErrorCode.TIMEOUT: "The provider request timed out",
    UserErrorCode.PROVIDER: "The provider returned an error",
    UserErrorCode.STORAGE: "Local storage is unavailable",
    UserErrorCode.NOT_FOUND: "The requested item was not found",
    UserErrorCode.INVALID_INPUT: "The supplied input is invalid",
    UserErrorCode.UNSUPPORTED: "This action is not supported by the provider",
    UserErrorCode.UNKNOWN: "The operation could not be completed",
}


def safe_user_message(error: BaseException, *, fallback: str | None = None) -> str:
    """Return a stable user message without including exception text or secrets."""
    code = classify_error(error)
    if fallback is not None and code is UserErrorCode.UNKNOWN:
        return fallback
    return _MESSAGES[code]


def classify_error(error: BaseException) -> UserErrorCode:
    """Classify known application failures without inspecting provider payloads."""
    if isinstance(error, AuthenticationError):
        return UserErrorCode.AUTHENTICATION
    if isinstance(error, AuthorisationError):
        return UserErrorCode.AUTHORISATION
    if isinstance(error, ConfigurationError):
        return UserErrorCode.CONFIGURATION
    if isinstance(error, NetworkError):
        return UserErrorCode.NETWORK
    if isinstance(error, TimeoutError):
        return UserErrorCode.TIMEOUT
    if isinstance(error, ProviderError):
        return UserErrorCode.PROVIDER
    if isinstance(error, StorageError):
        return UserErrorCode.STORAGE
    if isinstance(error, NotFoundError):
        return UserErrorCode.NOT_FOUND
    if isinstance(error, ValidationError):
        return UserErrorCode.INVALID_INPUT
    if isinstance(error, SamotechError):
        return UserErrorCode.UNKNOWN
    return UserErrorCode.UNKNOWN
