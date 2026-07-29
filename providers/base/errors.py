"""Shared exception hierarchy for all providers."""


class ProviderError(Exception):
    """Base for all provider-level errors."""


class AuthError(ProviderError):
    """Authentication / authorisation failure."""


class StreamError(ProviderError):
    """Stream URL resolution failure."""


class NetworkError(ProviderError):
    """Transient network-level error (DNS, timeout, TCP reset …)."""
