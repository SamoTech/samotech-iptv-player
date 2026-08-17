"""
Secure credential storage for the MAG provider.

Secrets are never persisted in plaintext.  The OS credential manager
(keyring) is used when available; callers must supply secrets explicitly
when running in a headless / CI environment.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from samotech_iptv.core.safe_logging import sanitize_url

log = logging.getLogger(__name__)

_keyring: Any | None
try:
    import keyring as _keyring

    _KEYRING_AVAILABLE = True
except ImportError:
    _keyring = None
    _KEYRING_AVAILABLE = False

SERVICE_NAME = "samotech-iptv-player"


@dataclass
class MAGCredentials:
    """
    Holds authorised credentials for a MAG/Stalker portal.

    All fields whose names end in *_secret* are write-only when retrieved
    from the OS keyring and are *never* logged.
    """

    portal_url: str
    mac_address: str  # Authorised MAC address for this subscription
    serial_number: str = ""
    device_id: str = ""
    device_id2: str = ""
    mag_model: str = ""
    signature: str = ""
    auth_mode: str = "mac_only"
    login: str = field(default="", repr=False, compare=False)
    password: str = field(default="", repr=False, compare=False)
    authorization_key: str = field(default="", repr=False, compare=False)
    profile_required: bool = False
    profile_second_step: bool = False
    profile_hd: str = ""
    _token: str = field(default="", repr=False, compare=False)

    @classmethod
    def from_keyring(cls, portal_url: str) -> MAGCredentials:
        """Load credentials from the OS keyring for *portal_url*."""
        if not _KEYRING_AVAILABLE or _keyring is None:
            raise RuntimeError("keyring is not installed. Install it with: pip install keyring")
        mac = _keyring.get_password(SERVICE_NAME, f"{portal_url}:mac")
        if not mac:
            raise ValueError(
                "No MAG credentials found in the OS keyring. "
                "Store them first with MAGCredentials.save_to_keyring()."
            )
        serial = _keyring.get_password(SERVICE_NAME, f"{portal_url}:serial") or ""
        model = _keyring.get_password(SERVICE_NAME, f"{portal_url}:model") or ""
        return cls(portal_url=portal_url, mac_address=mac, serial_number=serial, mag_model=model)

    def save_to_keyring(self) -> None:
        """Persist credentials to the OS keyring (never plaintext on disk)."""
        if not _KEYRING_AVAILABLE or _keyring is None:
            raise RuntimeError("keyring is not installed.")
        _keyring.set_password(SERVICE_NAME, f"{self.portal_url}:mac", self.mac_address)
        if self.serial_number:
            _keyring.set_password(SERVICE_NAME, f"{self.portal_url}:serial", self.serial_number)
        if self.mag_model:
            _keyring.set_password(SERVICE_NAME, f"{self.portal_url}:model", self.mag_model)
        log.info("Credentials saved to OS keyring")

    def delete_from_keyring(self) -> None:
        if not _KEYRING_AVAILABLE or _keyring is None:
            raise RuntimeError("keyring is not installed.")
        try:
            _keyring.delete_password(SERVICE_NAME, f"{self.portal_url}:mac")
            _keyring.delete_password(SERVICE_NAME, f"{self.portal_url}:serial")
        except Exception as exc:  # noqa: BLE001
            log.warning(
                "Unable to delete MAG credentials from keyring error_type=%s",
                type(exc).__name__,
            )

    @property
    def token(self) -> str:
        return self._token

    @token.setter
    def token(self, value: str) -> None:
        self._token = value

    def __repr__(self) -> str:
        return (
            f"MAGCredentials(portal_url={sanitize_url(self.portal_url)!r}, "
            f"mac_address=<redacted>, token=<{'set' if self._token else 'unset'}>)"
        )
