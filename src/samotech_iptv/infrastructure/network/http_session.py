"""HTTP session lifecycle manager.

Wraps an ``aiohttp.ClientSession`` and owns its lifecycle.
Provider adapters obtain a session from ``AsyncHttpClient`` rather than
creating ``aiohttp.ClientSession`` directly.
"""
from __future__ import annotations

from typing import Any, Optional

from samotech_iptv.core.logging import get_logger
from samotech_iptv.infrastructure.network.timeouts import TimeoutConfig
from samotech_iptv.infrastructure.network.headers import HeadersBuilder

__all__ = ["HttpSession"]

_log = get_logger(__name__)


class HttpSession:
    """A thin wrapper around ``aiohttp.ClientSession``.

    Lifecycle::

        session = HttpSession(timeout=TimeoutConfig())
        await session.open()
        # ... use session.get / session.post ...
        await session.close()

    Or via async context manager::

        async with HttpSession() as session:
            resp = await session.get("https://example.com")
    """

    def __init__(
        self,
        timeout: Optional[TimeoutConfig] = None,
        default_headers: Optional[dict[str, str]] = None,
        connector_limit: int = 20,
    ) -> None:
        self._timeout = timeout or TimeoutConfig()
        self._default_headers = default_headers or HeadersBuilder().accept_json().build()
        self._connector_limit = connector_limit
        self._session: Any = None  # aiohttp.ClientSession — deferred import

    async def open(self) -> None:
        """Open the underlying aiohttp session."""
        import aiohttp  # noqa: PLC0415

        connector = aiohttp.TCPConnector(limit=self._connector_limit)
        self._session = aiohttp.ClientSession(
            timeout=self._timeout.to_aiohttp(),
            headers=self._default_headers,
            connector=connector,
        )
        _log.debug("HttpSession opened (limit=%d)", self._connector_limit)

    async def close(self) -> None:
        """Close the underlying aiohttp session."""
        if self._session is not None:
            await self._session.close()
            self._session = None
            _log.debug("HttpSession closed")

    async def __aenter__(self) -> "HttpSession":
        await self.open()
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    @property
    def raw(self) -> Any:
        """Access the underlying ``aiohttp.ClientSession`` directly.

        Prefer ``AsyncHttpClient`` for all standard requests.
        """
        if self._session is None:
            raise RuntimeError("HttpSession is not open — call open() first")
        return self._session

    @property
    def is_open(self) -> bool:
        return self._session is not None
