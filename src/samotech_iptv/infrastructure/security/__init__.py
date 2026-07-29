"""Security infrastructure package.

Provides:
- ``KeyringCredentialStore``: OS keyring-backed implementation of
  ``CredentialStorePort``.
"""
from samotech_iptv.infrastructure.security.keyring_credential_store import (
    KeyringCredentialStore,
)

__all__ = ["KeyringCredentialStore"]
