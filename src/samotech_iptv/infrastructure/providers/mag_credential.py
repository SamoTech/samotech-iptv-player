"""MAG-specific credential model.

A Stalker/MAG handshake authenticates the subscriber identity represented by a
MAC address.  That identity is distinct from the short-lived session token
returned by the portal.  This model is intentionally infrastructure-specific
and is never exposed through the application provider ports.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from samotech_iptv.core.exceptions import ValidationError

if TYPE_CHECKING:
    from collections.abc import Mapping

    from samotech_iptv.domain.value_objects.credential import Credential

__all__ = ["MagCredential"]


@dataclass(frozen=True, repr=False)
class MagCredential:
    """Connection identity required by the legacy MAG provider.

    The application-level ``Credential.username`` is the subscriber MAC
    address for MAG providers.  The generic password is retained by the
    credential store but is not sent to the current Stalker handshake, whose
    protocol authenticates using the MAC address and optional device IDs.
    """

    portal_url: str
    mac_address: str
    serial_number: str = ""
    device_id: str = ""
    device_id2: str = ""
    mag_model: str = ""
    signature: str = ""
    auth_mode: str = "mac_only"
    login: str = ""
    password: str = ""
    authorization_key: str = ""
    profile_required: bool = False
    profile_second_step: bool = False

    def __post_init__(self) -> None:
        if not self.portal_url.strip():
            raise ValidationError("portal_url", "MAG portal URL must not be blank")
        if not self.mac_address.strip():
            raise ValidationError("mac_address", "MAG MAC address must not be blank")

    @classmethod
    def from_application_credential(
        cls,
        credential: Credential,
        portal_url: str,
        device_identity: Mapping[str, str] | None = None,
    ) -> MagCredential:
        """Build MAG credentials from the canonical application credential.

        ``device_identity`` is optional provider configuration and contains
        only protocol identifiers, never a session token.
        """
        identity = device_identity or {}
        return cls(
            portal_url=portal_url,
            mac_address=credential.username,
            serial_number=identity.get("serial_number", ""),
            device_id=identity.get("device_id", ""),
            device_id2=identity.get("device_id2", ""),
            mag_model=identity.get("mag_model", ""),
            signature=identity.get("signature", ""),
            auth_mode=identity.get("mag_auth_mode", identity.get("auth_mode", "mac_only")),
            login=identity.get("login", ""),
            password=identity.get("password", ""),
            authorization_key=identity.get("authorization_key", ""),
            profile_required=bool(identity.get("profile_required", False)),
            profile_second_step=bool(identity.get("profile_second_step", False)),
        )

    def as_legacy_config(self, *, timeout_s: float, max_retries: int) -> dict[str, object]:
        """Return the narrowly scoped configuration required by ``MAGProvider``."""
        return {
            "portal_url": self.portal_url,
            "mac_address": self.mac_address,
            "serial_number": self.serial_number,
            "device_id": self.device_id,
            "device_id2": self.device_id2,
            "mag_model": self.mag_model,
            "signature": self.signature,
            "auth_mode": self.auth_mode,
            "mag_auth_mode": self.auth_mode,
            "login": self.login,
            "password": self.password,
            "authorization_key": self.authorization_key,
            "profile_required": self.profile_required,
            "profile_second_step": self.profile_second_step,
            "timeout_s": timeout_s,
            "max_retries": max_retries,
            "protocol_profile": "auto",
            "use_keyring": False,
        }

    def __repr__(self) -> str:
        return (
            "MagCredential("
            f"portal_url={self.portal_url!r}, mac_address=<redacted>, "
            "device_identity=<redacted>)"
        )
