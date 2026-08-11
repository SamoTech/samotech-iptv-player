"""HTTP session lifecycle manager.

Wraps an ``aiohttp.ClientSession`` and owns its lifecycle.  Provider adapters
obtain a session from ``AsyncHttpClient`` rather than creating one directly.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.core.logging import get_logger
from samotech_iptv.infrastructure.network.headers import HeadersBuilder
from samotech_iptv.infrastructure.network.timeouts import TimeoutConfig

if TYPE_CHECKING:
    from types import TracebackType

    from aiohttp import ClientSession

__all__ = ["HttpSession"]

_LOG = get_logger(__name__)


class HttpSession:
    """A thin lifecycle wrapper around ``aiohttp.ClientSession``."""

    def __init__(
        self,
        timeout: TimeoutConfig | None = None,
        default_headers: dict[str, str] | None = None,
        connector_limit: int = 20,
    ) -> None:
        self._timeout = timeout or TimeoutConfig()
        self._default_headers = default_headers or HeadersBuilder().accept_json().build()
        self._connector_limit = connector_limit
        self._session: ClientSession | None = None

    async def open(self) -> None:
        """Open the underlying aiohttp session."""
        import aiohttp  # noqa: PLC0415

        connector = aiohttp.TCPConnector(limit=self._connector_limit)
        self._session = aiohttp.ClientSession(
            timeout=self._timeout.to_aiohttp(),
            headers=self._default_headers,
            connector=connector,
        )
        _LOG.debug("HttpSession opened (limit=%d)", self._connector_limit)

    async def close(self) -> None:
        """Close the underlying aiohttp session."""
        if self._session is not None:
            await self._session.close()
            self._session = None
            _LOG.debug("HttpSession closed")

    async def __aenter__(self) -> HttpSession:
        await self.open()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.close()

    @property
    def raw(self) -> ClientSession:
        """Access the underlying ``aiohttp.ClientSession`` directly.

        Prefer ``AsyncHttpClient`` for all standard requests.
        """
        if self._session is None:
            raise RuntimeError("HttpSession is not open — call open() first")
        return self._session

    @property
    def is_open(self) -> bool:
        return self._session is not None
