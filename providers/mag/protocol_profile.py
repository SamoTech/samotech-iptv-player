"""Evidence-based MAG/Stalker handshake request profiles.

The portal ecosystem has multiple observed handshake variants.  Profiles keep
request construction in the legacy protocol layer while leaving the adapter
responsible only for application lifecycle and translation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from urllib.parse import urlsplit, urlunsplit

from .constants import ENDPOINT_HANDSHAKE

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = [
    "LegacyMAGProtocolProfile",
    "MAGProtocolProfile",
    "StalkerQueryProtocolProfile",
]


@dataclass(frozen=True)
class MAGProtocolProfile:
    """Describe protocol-owned handshake request construction."""

    name: str
    handshake_endpoint: str = ENDPOINT_HANDSHAKE
    handshake_params: Mapping[str, str] = field(default_factory=dict)
    user_agent: str | None = None
    referer_suffix: str | None = None

    def handshake_request(self, portal_url: str) -> tuple[str, dict[str, str], dict[str, str]]:
        """Return endpoint, query parameters, and safe protocol headers."""
        headers: dict[str, str] = {}
        if self.user_agent:
            headers["X-User-Agent"] = self.user_agent
        if self.referer_suffix:
            parsed = urlsplit(portal_url)
            origin = urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))
            headers["Referer"] = f"{origin}{self.referer_suffix}"
        return self.handshake_endpoint, dict(self.handshake_params), headers


@dataclass(frozen=True)
class LegacyMAGProtocolProfile(MAGProtocolProfile):
    """Bare `/server/load.php` handshake used by the existing legacy client."""

    name: str = "legacy"


@dataclass(frozen=True)
class StalkerQueryProtocolProfile(MAGProtocolProfile):
    """Observed Stalker query/header handshake variant.

    This profile is deterministic and opt-in.  It is not selected for a real
    provider automatically because portal compatibility is not universal.
    """

    name: str = "stalker_query"
    handshake_params: Mapping[str, str] = field(
        default_factory=lambda: {
            "type": "stb",
            "action": "handshake",
            "token": "",
            "JsHttpRequest": "1-xml",
        }
    )
    user_agent: str | None = "Model: MAG254; Link: WiFi"
    referer_suffix: str | None = "/c/"
