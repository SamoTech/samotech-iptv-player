"""Async HTTP client with retry, timeout, and structured logging.

This is the primary entry point for all outbound HTTP traffic.
Provider adapters must use this class instead of creating their own
aiohttp sessions.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, cast

from samotech_iptv.core.diagnostics import redact_url
from samotech_iptv.core.logging import get_logger

if TYPE_CHECKING:
    from types import TracebackType

    from samotech_iptv.core.typing import JSON
from samotech_iptv.infrastructure.network.exceptions import (
    HttpClientError,
    HttpConnectionError,
    HttpServerError,
    HttpTimeoutError,
)
from samotech_iptv.infrastructure.network.http_session import HttpSession
from samotech_iptv.infrastructure.network.retry_policy import RetryPolicy
from samotech_iptv.infrastructure.network.timeouts import TimeoutConfig

__all__ = ["AsyncHttpClient"]

_log = get_logger(__name__)


class AsyncHttpClient:
    """Provider-agnostic async HTTP client.

    Features:
    - Automatic retry with exponential backoff via ``RetryPolicy``
    - Configurable connection and read timeouts via ``TimeoutConfig``
    - Structured logging of every request / response / retry
    - Cancellation-safe: ``asyncio.CancelledError`` is never swallowed
    - Translates aiohttp errors into the ``HttpError`` hierarchy

    Usage as context manager (recommended)::

        async with AsyncHttpClient() as client:
            data = await client.get_json("https://example.com/api")

    Usage with explicit lifecycle::

        client = AsyncHttpClient()
        await client.open()
        try:
            data = await client.get_json("https://example.com/api")
        finally:
            await client.close()
    """

    def __init__(
        self,
        timeout: TimeoutConfig | None = None,
        retry_policy: RetryPolicy | None = None,
        default_headers: dict[str, str] | None = None,
    ) -> None:
        self._timeout = timeout or TimeoutConfig()
        self._retry = retry_policy or RetryPolicy()
        self._session = HttpSession(
            timeout=self._timeout,
            default_headers=default_headers,
        )

    # ------------------------------------------------------------------ lifecycle

    async def open(self) -> None:
        await self._session.open()

    async def close(self) -> None:
        await self._session.close()

    async def __aenter__(self) -> AsyncHttpClient:
        await self.open()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.close()

    # ------------------------------------------------------------------ requests

    async def get_json(
        self,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> JSON:
        """Perform a GET request and return parsed JSON.

        Args:
            url:     Absolute URL.
            params:  Query string parameters.
            headers: Additional per-request headers (merged with defaults).

        Returns:
            Parsed JSON body (dict, list, etc.).

        Raises:
            HttpClientError:     4xx response.
            HttpServerError:     5xx response.
            HttpTimeoutError:    Request timed out.
            HttpConnectionError: TCP-level failure.
        """
        return cast(
            "JSON",
            await self._request_with_retry("GET", url, params=params, headers=headers),
        )

    async def post_json(
        self,
        url: str,
        *,
        json: JSON | None = None,
        data: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> JSON:
        """Perform a POST request and return parsed JSON."""
        return cast(
            "JSON",
            await self._request_with_retry("POST", url, json=json, data=data, headers=headers),
        )

    async def get_text(
        self,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        timeout: TimeoutConfig | None = None,
    ) -> str:
        """Perform a GET request and return the raw response body as text."""
        return cast(
            "str",
            await self._request_with_retry(
                "GET",
                url,
                params=params,
                headers=headers,
                as_text=True,
                timeout=timeout,
            ),
        )

    async def get_bytes(
        self,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        timeout: TimeoutConfig | None = None,
        max_bytes: int = 4 * 1024 * 1024,
    ) -> bytes:
        """Perform a GET request for bounded binary content."""
        result = await self._request_with_retry(
            "GET",
            url,
            params=params,
            headers=headers,
            as_bytes=True,
            timeout=timeout,
            max_bytes=max_bytes,
        )
        return cast("bytes", result)

    # ------------------------------------------------------------------ internals

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        json: JSON | None = None,
        data: dict[str, str] | None = None,
        as_text: bool = False,
        as_bytes: bool = False,
        timeout: TimeoutConfig | None = None,
        max_bytes: int = 4 * 1024 * 1024,
    ) -> JSON | str | bytes:
        last_exc: Exception = RuntimeError("No attempts made")

        for attempt in range(self._retry.max_attempts):
            try:
                result = await self._single_request(
                    method,
                    url,
                    params=params,
                    headers=headers,
                    json=json,
                    data=data,
                    as_text=as_text,
                    as_bytes=as_bytes,
                    timeout=timeout,
                    max_bytes=max_bytes,
                )
                if attempt > 0:
                    _log.info("%s %s succeeded on attempt %d", method, redact_url(url), attempt + 1)
                return result

            except asyncio.CancelledError:
                raise  # never swallow cancellation

            except HttpTimeoutError as exc:
                last_exc = exc
                _log.warning(
                    "%s %s timed out (attempt %d/%d)",
                    method,
                    redact_url(url),
                    attempt + 1,
                    self._retry.max_attempts,
                )
                if not self._retry.should_retry(attempt, None):
                    raise

            except HttpConnectionError as exc:
                last_exc = exc
                _log.warning(
                    "%s %s connection error (attempt %d/%d): %s",
                    method,
                    redact_url(url),
                    attempt + 1,
                    self._retry.max_attempts,
                    exc,
                )
                if not self._retry.should_retry(attempt, None):
                    raise

            except HttpServerError as exc:
                last_exc = exc
                _log.warning(
                    "%s %s server error %s (attempt %d/%d)",
                    method,
                    redact_url(url),
                    exc.status_code,
                    attempt + 1,
                    self._retry.max_attempts,
                )
                if not self._retry.should_retry(attempt, exc.status_code):
                    raise

            except HttpClientError:
                raise  # 4xx are never retried

            await self._retry.sleep(attempt)

        raise last_exc

    async def _single_request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        json: JSON | None = None,
        data: dict[str, str] | None = None,
        as_text: bool = False,
        as_bytes: bool = False,
        timeout: TimeoutConfig | None = None,
        max_bytes: int = 4 * 1024 * 1024,
    ) -> JSON | str | bytes:
        try:
            import aiohttp  # noqa: PLC0415

            _log.debug(
                "%s %s params=%s",
                method,
                redact_url(url),
                "<redacted>" if params else None,
            )
            async with self._session.raw.request(
                method,
                url,
                params=params,
                headers=headers,
                json=json,
                data=data,
                timeout=timeout.to_aiohttp() if timeout is not None else None,
            ) as resp:
                if resp.status >= 500:
                    body = await resp.text()
                    raise HttpServerError(
                        f"{method} {url} -> {resp.status}: {body[:200]}",
                        status_code=resp.status,
                    )
                if resp.status >= 400:
                    body = await resp.text()
                    raise HttpClientError(
                        f"{method} {url} -> {resp.status}: {body[:200]}",
                        status_code=resp.status,
                    )
                _log.debug("%s %s -> %d", method, redact_url(url), resp.status)
                if as_text:
                    return await resp.text()
                if as_bytes:
                    binary_body = await resp.read()
                    if len(binary_body) > max_bytes:
                        raise HttpClientError("Binary response exceeded the configured size limit")
                    return binary_body
                return cast("JSON", await resp.json(content_type=None))

        except TimeoutError as exc:
            raise HttpTimeoutError(f"{method} {redact_url(url)} timed out") from exc
        except aiohttp.ClientConnectorError as exc:
            raise HttpConnectionError(f"Cannot connect to {redact_url(url)}") from exc
        except aiohttp.ClientError as exc:
            raise HttpConnectionError(f"{method} {redact_url(url)} client error") from exc
