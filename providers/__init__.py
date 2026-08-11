"""
SamoTech IPTV Player — Provider Package
Exposes the registry and base interfaces.
"""

from .base import AuthError, BaseProvider, ProviderError, StreamError
from .registry import ProviderRegistry

__all__ = [
    "BaseProvider",
    "ProviderError",
    "AuthError",
    "StreamError",
    "ProviderRegistry",
]
