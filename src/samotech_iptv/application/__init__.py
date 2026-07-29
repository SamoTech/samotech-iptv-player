"""Application layer — orchestration of business use-cases.

Contains:
- Port interfaces (``ports/``) — application-defined contracts for infrastructure
- Use-case classes (``use_cases/``)
- DTOs (``dtos/``) — request/response objects

Allowed dependencies: ``samotech_iptv.core``, ``samotech_iptv.domain``, stdlib.
Forbidden: infrastructure, presentation, providers, aiohttp, SQLite.
"""
from samotech_iptv.application.ports import (
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
