"""
Low-level HTTP connection manager for the MAG provider.

All I/O is fully asynchronous (asyncio + aiohttp).
Implements:
  - configurable timeouts
  - retries with exponential backoff
  - structured logging
  - TLS verification (never disabled except in explicit dev mode)
  - sanitised request construction
"""
from __future__ import annotations

import asyncio
import logging
import ssl
from typing import Any, Optional
from urllib.parse import urljoin, urlparse

import aiohttp

from .constants import (
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT_S,
    RETRY_BASE_DELAY,
    RETRY_MAX_DELAY,
    USER_AGENT,
)
from ..base.errors import NetworkError

log = logging.getLogger(__name__)


def _sanitise_url(base: str, path: str) -> str:
    """Join base portal URL with an endpoint path safely."""
    parsed = urlparse(base)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Portal URL must use http or https, got: {parsed.scheme!r}")
    return urljoin(base.rstrip("/") + "/", path.lstrip("/"))


class MAGConnection:
    """
    Manages a persistent aiohttp ClientSession for portal communication.

    Parameters
    ----------
    portal_url:
        Authorised portal base URL (must be http or https).
    timeout_s:
        Per-request timeout in seconds.
    max_retries:
        Number of times to retry a failed request before raising.
    dev_mode:
        When *True*, TLS certificate verification is relaxed.
        **Only for local development / self-signed test servers.**
    """

    def __init__(
        self,
        portal_url: str,
        timeout_s: float = DEFAULT_TIMEOUT_S,
        max_retries: int = DEFAULT_MAX_RETRIES,
        dev_mode: bool = False,
    ) -> None:
        self._portal_url = portal_url
        self._timeout = aiohttp.ClientTimeout(total=timeout_s)
        self._max_retries = max_retries
        self._dev_mode = dev_mode
        self._session: Optional[aiohttp.ClientSession] = None

    async def open(self) -> None:
        if self._session and not self._session.closed:
            return
        if self._dev_mode:
            log.warning(
                "TLS verification is DISABLED (dev_mode=True). "
                "Do NOT use this setting in production."
            )
            ssl_context: ssl.SSLContext | bool = False
        else:
            ssl_context = ssl.create_default_context()

        connector = aiohttp.TCPConnector(ssl=ssl_context)
        self._session = aiohttp.ClientSession(
            headers={"User-Agent": USER_AGENT},
            connector=connector,
            timeout=self._timeout,
        )
        log.debug("HTTP session opened for %s", self._portal_url)

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
            log.debug("HTTP session closed")

    async def get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        url = _sanitise_url(self._portal_url, path)
        return await self._request_with_retry("GET", url, params=params, headers=headers)

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        assert self._session, "Call open() before making requests"
        delay = RETRY_BASE_DELAY
        last_exc: Exception | None = None
        for attempt in range(1, self._max_retries + 1):
            try:
                log.debug("%s %s (attempt %d/%d)", method, url, attempt, self._max_retries)
                async with self._session.request(
                    method,
                    url,
                    params=params,
                    headers=headers,
                    allow_redirects=True,
                ) as resp:
                    resp.raise_for_status()
                    data = await resp.json(content_type=None)
                    log.debug("Response %d from %s", resp.status, url)
                    return data
            except aiohttp.ClientResponseError as exc:
                if 400 <= exc.status < 500:
                    raise NetworkError(
                        f"HTTP {exc.status} from {url}: {exc.message}"
                    ) from exc
                log.warning("HTTP %d on attempt %d — %s", exc.status, attempt, exc.message)
                last_exc = exc
            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                log.warning("Network error on attempt %d: %s", attempt, exc)
                last_exc = exc

            if attempt < self._max_retries:
                jitter = delay * 0.1
                sleep_for = min(delay + jitter, RETRY_MAX_DELAY)
                log.info("Retrying in %.1fs …", sleep_for)
                await asyncio.sleep(sleep_for)
                delay = min(delay * 2, RETRY_MAX_DELAY)

        raise NetworkError(
            f"Request to {url} failed after {self._max_retries} attempts"
        ) from last_exc
