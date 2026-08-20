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

    def _service_path(self) -> str:
        """Return the configured non-endpoint path prefix without its trailing slash."""
        path = urlsplit(self.base_url.value).path.rstrip("/")
        return "" if path in {"", "/"} else path

    def player_api(self, action: str | None = None, **parameters: str) -> URL:
        """Build a ``player_api.php`` request URL with encoded credentials and action."""
        parsed = urlsplit(self.base_url.value)
        endpoint = urlunsplit(
            (parsed.scheme, parsed.netloc, f"{self._service_path()}/player_api.php", "", "")
        )
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
        quoted_kind = quote(kind, safe="")
        quoted_username = quote(self.credential.username, safe="")
        quoted_password = quote(self.credential.password, safe="")
        quoted_stream_id = quote(stream_id, safe="")
        quoted_extension = quote(extension, safe="")
        path = (
            f"{self._service_path()}/{quoted_kind}/{quoted_username}/"
            f"{quoted_password}/{quoted_stream_id}.{quoted_extension}"
        )
        return URL(urlunsplit((parsed.scheme, parsed.netloc, path, "", "")))
