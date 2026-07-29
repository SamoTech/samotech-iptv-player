"""Compatibility shim — Phase A import surface for application ports.

All public names re-exported from the new ``ports/`` package.

.. deprecated::
    Import directly from ``samotech_iptv.application.ports.<module>``
    or from ``samotech_iptv.application.ports`` (the package).
"""
from samotech_iptv.application.ports import (  # noqa: F401
    ProviderPort,
    PlayerPort,
    StoragePort,
    CredentialStorePort,
    NotificationPort,
    AuthenticationProvider,
    CatalogProvider,
    EPGProvider,
    SearchProvider,
    PlaybackProvider,
    SessionProvider,
    CapabilityProvider,
)

__all__ = [
    "ProviderPort", "PlayerPort", "StoragePort",
    "CredentialStorePort", "NotificationPort",
    "AuthenticationProvider", "CatalogProvider", "EPGProvider",
    "SearchProvider", "PlaybackProvider", "SessionProvider", "CapabilityProvider",
]
