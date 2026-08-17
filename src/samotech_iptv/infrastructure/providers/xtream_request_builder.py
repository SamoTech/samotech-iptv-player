"""Credential-safe request construction for Xtream-compatible player APIs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from urllib.parse import quote, urlencode, urlsplit, urlunsplit

from samotech_iptv.domain.value_objects.url import URL

if TYPE_CHECKING:
    from samotech_iptv.domain.value_objects.credential import Credential

__all__ = ["XtreamRequestBuilder"]


@dataclass(frozen=True)
class XtreamRequestBuilder:
    """Build Xtream API endpoints without retaining session or response state."""

    base_url: URL
    credential: Credential

    def player_api(self, action: str | None = None, **parameters: str) -> URL:
        """Build a ``player_api.php`` request URL with encoded credentials and action."""
        parsed = urlsplit(self.base_url.value)
        endpoint = urlunsplit((parsed.scheme, parsed.netloc, "/player_api.php", "", ""))
        query: dict[str, str] = {
            "username": self.credential.username,
            "password": self.credential.password,
        }
        if action is not None:
            query["action"] = action
        query.update(parameters)
        return URL(f"{endpoint}?{urlencode(query)}")

    def stream_url(self, kind: str, stream_id: str, extension: str) -> URL:
        """Build a canonical Xtream HTTP(S) playback URL for a supplied stream descriptor."""
        parsed = urlsplit(self.base_url.value)
        path = (
            f"/{quote(kind, safe='')}/{quote(self.credential.username, safe='')}/"
            f"{quote(self.credential.password, safe='')}/{quote(stream_id, safe='')}."
            f"{quote(extension, safe='')}"
        )
        return URL(urlunsplit((parsed.scheme, parsed.netloc, path, "", "")))
