"""Application layer — orchestration of business use-cases.

Contains:
- Port interfaces (application-defined contracts for infrastructure)
- Use-case classes
- DTOs (request/response objects)

Allowed dependencies: ``samotech_iptv.core``, ``samotech_iptv.domain``, stdlib.
Forbidden: infrastructure, presentation, providers, aiohttp, SQLite.

Application services depend ONLY on interfaces defined in ``ports``.
"""

from samotech_iptv.application.ports import (
    ProviderPort,
    PlayerPort,
    StoragePort,
    CredentialStorePort,
    NotificationPort,
)

__all__ = [
    "ProviderPort",
    "PlayerPort",
    "StoragePort",
    "CredentialStorePort",
    "NotificationPort",
]
