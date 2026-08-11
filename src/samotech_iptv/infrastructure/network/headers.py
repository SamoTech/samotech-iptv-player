"""HTTP header builder helpers.

Provides a fluent builder for constructing request headers.
No networking code here.
"""
from __future__ import annotations

from samotech_iptv.core.constants import APP_NAME
from samotech_iptv.version import __version__

__all__ = ["HeadersBuilder"]

_DEFAULT_USER_AGENT = f"{APP_NAME}/{__version__}"


class HeadersBuilder:
    """Fluent builder for HTTP request headers.

    Usage::

        headers = (
            HeadersBuilder()
            .user_agent("MyApp/1.0")
            .accept_json()
            .authorization_bearer(token)
            .custom("X-Mac", mac_address)
            .build()
        )
    """

    def __init__(self) -> None:
        self._headers: dict[str, str] = {
            "User-Agent": _DEFAULT_USER_AGENT,
        }

    def user_agent(self, value: str) -> HeadersBuilder:
        self._headers["User-Agent"] = value
        return self

    def accept_json(self) -> HeadersBuilder:
        self._headers["Accept"] = "application/json"
        return self

    def content_type_json(self) -> HeadersBuilder:
        self._headers["Content-Type"] = "application/json"
        return self

    def content_type_form(self) -> HeadersBuilder:
        self._headers["Content-Type"] = "application/x-www-form-urlencoded"
        return self

    def authorization_bearer(self, token: str) -> HeadersBuilder:
        self._headers["Authorization"] = f"Bearer {token}"
        return self

    def cookie(self, name: str, value: str) -> HeadersBuilder:
        existing = self._headers.get("Cookie", "")
        pair = f"{name}={value}"
        self._headers["Cookie"] = f"{existing}; {pair}" if existing else pair
        return self

    def custom(self, name: str, value: str) -> HeadersBuilder:
        self._headers[name] = value
        return self

    def build(self) -> dict[str, str]:
        """Return an immutable snapshot of the current headers."""
        return dict(self._headers)
