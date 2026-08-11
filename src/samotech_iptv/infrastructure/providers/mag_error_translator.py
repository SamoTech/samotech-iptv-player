"""Error translation for the MAG provider adapter.

Maps the legacy ``providers.base.errors`` hierarchy into core domain
exceptions so nothing provider-specific leaks past the adapter boundary.

Translation table::

    providers.base.errors.AuthError    ->  core.exceptions.AuthenticationError
    providers.base.errors.StreamError  ->  core.exceptions.ProviderError
    providers.base.errors.NetworkError ->  core.exceptions.NetworkError
    providers.base.errors.ProviderError-> core.exceptions.ProviderError
    Any other Exception                ->  core.exceptions.ProviderError
"""

from __future__ import annotations

from typing import NoReturn

from samotech_iptv.core.exceptions import (
    AuthenticationError,
    NetworkError,
    ProviderError,
    SamotechError,
)
from samotech_iptv.core.logging import get_logger

__all__ = ["translate_mag_error", "translate_mag_and_raise"]

_log = get_logger(__name__)


def translate_mag_error(exc: Exception) -> SamotechError:
    """Translate a legacy MAG provider exception to a domain error.

    This function performs a *lazy* import of the legacy error classes so
    that the infrastructure layer never creates a hard import-time
    dependency on the legacy ``providers`` package structure.
    """
    # Pass-through: already a clean domain error
    if isinstance(exc, SamotechError):
        return exc

    # Lazy import to avoid hard coupling at module load time
    try:
        from providers.base.errors import (
            AuthError as LegacyAuthError,
        )
        from providers.base.errors import (
            NetworkError as LegacyNetworkError,
        )
        from providers.base.errors import (
            ProviderError as LegacyProviderError,
        )
    except ImportError:
        # Legacy package not importable in isolated test environments
        _log.debug("providers.base not importable — treating as ProviderError")
        return ProviderError(f"MAG provider error: {exc}")

    if isinstance(exc, LegacyAuthError):
        _log.debug("Translating LegacyAuthError -> AuthenticationError")
        return AuthenticationError(f"MAG authentication failed: {exc}")

    if isinstance(exc, LegacyNetworkError):
        _log.debug("Translating LegacyNetworkError -> NetworkError")
        return NetworkError(f"MAG network error: {exc}")

    if isinstance(exc, LegacyProviderError):
        _log.debug("Translating LegacyProviderError -> ProviderError")
        return ProviderError(f"MAG provider error: {exc}")

    _log.warning("Translating unexpected %s -> ProviderError", type(exc).__name__)
    return ProviderError(f"Unexpected MAG error: {exc}")


def translate_mag_and_raise(exc: Exception) -> NoReturn:
    """Translate and immediately raise.  Convenience for ``except`` blocks."""
    raise translate_mag_error(exc) from exc
