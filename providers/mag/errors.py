"""MAG-specific error types (re-exported from base)."""
from ..base.errors import ProviderError, AuthError, StreamError, NetworkError

__all__ = ["ProviderError", "AuthError", "StreamError", "NetworkError"]
