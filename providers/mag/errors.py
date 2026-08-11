"""MAG-specific error types (re-exported from base)."""

from ..base.errors import AuthError, NetworkError, ProviderError, StreamError

__all__ = ["ProviderError", "AuthError", "StreamError", "NetworkError"]
