"""Low-level asynchronous HTTP transport for the MAG provider."""

from __future__ import annotations

import asyncio
import json
import logging
import ssl
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, cast
from urllib.parse import urljoin, urlparse, urlunsplit

import aiohttp

if TYPE_CHECKING:
    from collections.abc import Mapping

    from samotech_iptv.core.typing import JSON

from ..base.errors import NetworkError
from .constants import (
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT_S,
    RETRY_BASE_DELAY,
    RETRY_MAX_DELAY,
    USER_AGENT,
)

log = logging.getLogger(__name__)


@dataclass(frozen=True, repr=False)
class MAGProbeResponse:
    """One transient handshake-probe response.

    The payload is deliberately excluded from ``repr`` and must be consumed only
    for structural classification. Discovery results retain safe metadata, never
    this response body or any token value.
    """

    status: int
    content_type: str
    response_size: int
    elapsed_seconds: float
    payload: JSON | None = field(default=None, repr=False)
    malformed_json: bool = False
    redirect_count: int = 0
    server: str = ""
    allow: str = ""
    www_authenticate: bool = False


def _sanitise_url(base: str, path: str) -> str:
    """Join a portal base URL and endpoint while preserving configured app paths."""
    parsed = urlparse(base)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Portal URL must use http or https, got: {parsed.scheme!r}")
    base_path = parsed.path or "/"
    endpoint = path.lstrip("/")
    if endpoint == base_path.rsplit("/", 1)[-1] and not base_path.endswith("/"):
        directory_base = base
    else:
        directory_path = base_path if base_path.endswith("/") else f"{base_path}/"
        directory_base = urlunsplit((parsed.scheme, parsed.netloc, directory_path, "", ""))
    return urljoin(directory_base, endpoint)


class MAGConnection:
    """Manage a persistent aiohttp session for MAG portal communication."""

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
        self._session: aiohttp.ClientSession | None = None

    @property
    def portal_url(self) -> str:
        """Return the configured portal URL for profile-owned request construction."""
        return self._portal_url

    async def open(self) -> None:
        """Open the underlying HTTP session if it is not already active."""
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
        """Close the active HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            log.debug("HTTP session closed")

    async def get(
        self,
        path: str,
        *,
        params: Mapping[str, str | int] | None = None,
        headers: dict[str, str] | None = None,
        base_url: str | None = None,
    ) -> JSON:
        """Issue an authenticated GET relative to the configured or approved profile base."""
        url = _sanitise_url(base_url or self._portal_url, path)
        return await self._request_with_retry("GET", url, params=params, headers=headers)

    async def post(
        self,
        path: str,
        *,
        data: Mapping[str, str | int] | None = None,
        headers: dict[str, str] | None = None,
        base_url: str | None = None,
    ) -> JSON:
        """Issue one authenticated form POST relative to an approved profile base."""
        url = _sanitise_url(base_url or self._portal_url, path)
        return await self._request_with_retry(
            "POST",
            url,
            data={key: str(value) for key, value in (data or {}).items()},
            headers=headers,
        )

    async def probe(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, str | int] | None = None,
        data: Mapping[str, str | int] | None = None,
        headers: dict[str, str] | None = None,
        base_url: str | None = None,
    ) -> MAGProbeResponse:
        """Make one transient safe probe using a source-backed HTTP method."""
        session = self._session
        if session is None or session.closed:
            raise RuntimeError("Call open() before making requests")
        url = _sanitise_url(base_url or self._portal_url, path)
        started = time.perf_counter()
        try:
            async with session.request(
                method,
                url,
                params=params,
                data={key: str(value) for key, value in (data or {}).items()} or None,
                headers=headers,
                allow_redirects=True,
            ) as response:
                body = await response.read()
                content_type = response.headers.get("Content-Type", "").split(";", 1)[0]
                payload: JSON | None = None
                malformed_json = False
                if body:
                    try:
                        payload = cast("JSON", json.loads(body))
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        malformed_json = True
                return MAGProbeResponse(
                    status=response.status,
                    content_type=content_type or "<missing>",
                    response_size=len(body),
                    elapsed_seconds=time.perf_counter() - started,
                    payload=payload,
                    malformed_json=malformed_json,
                    redirect_count=len(response.history),
                    server=response.headers.get("Server", ""),
                    allow=response.headers.get("Allow", ""),
                    www_authenticate="WWW-Authenticate" in response.headers,
                )
        except (TimeoutError, aiohttp.ClientError) as exc:
            raise NetworkError("MAG protocol probe did not complete") from exc

    async def probe_get(
        self,
        path: str,
        *,
        params: Mapping[str, str | int] | None = None,
        headers: dict[str, str] | None = None,
        base_url: str | None = None,
    ) -> MAGProbeResponse:
        """Make exactly one transient handshake probe without logging its response body.

        This API intentionally does not retry, raise on HTTP status, or retain the
        raw URL in its result. Callers must convert the result into a safe discovery
        classification and discard the payload immediately.
        """
        session = self._session
        if session is None or session.closed:
            raise RuntimeError("Call open() before making requests")
        url = _sanitise_url(base_url or self._portal_url, path)
        started = time.perf_counter()
        try:
            async with session.request(
                "GET",
                url,
                params=params,
                headers=headers,
                allow_redirects=True,
            ) as response:
                body = await response.read()
                content_type = response.headers.get("Content-Type", "").split(";", 1)[0]
                payload: JSON | None = None
                malformed_json = False
                if body:
                    try:
                        payload = cast("JSON", json.loads(body))
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        malformed_json = True
                return MAGProbeResponse(
                    status=response.status,
                    content_type=content_type or "<missing>",
                    response_size=len(body),
                    elapsed_seconds=time.perf_counter() - started,
                    payload=payload,
                    malformed_json=malformed_json,
                    redirect_count=len(response.history),
                    server=response.headers.get("Server", ""),
                    allow=response.headers.get("Allow", ""),
                    www_authenticate="WWW-Authenticate" in response.headers,
                )
        except (TimeoutError, aiohttp.ClientError) as exc:
            raise NetworkError("MAG handshake probe did not complete") from exc

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        *,
        params: Mapping[str, str | int] | None = None,
        data: Mapping[str, str | int] | None = None,
        headers: dict[str, str] | None = None,
    ) -> JSON:
        session = self._session
        if session is None or session.closed:
            raise RuntimeError("Call open() before making requests")

        delay = RETRY_BASE_DELAY
        last_exc: Exception | None = None
        for attempt in range(1, self._max_retries + 1):
            try:
                log.debug("%s %s (attempt %d/%d)", method, url, attempt, self._max_retries)
                async with session.request(
                    method,
                    url,
                    params=params,
                    data={key: str(value) for key, value in (data or {}).items()} or None,
                    headers=headers,
                    allow_redirects=True,
                ) as response:
                    body = await response.read()
                    content_type = response.headers.get("Content-Type", "").split(";", 1)[0]
                    safe_path = urlparse(url).path or "/"
                    response_size = len(body)
                    if response.status >= 400:
                        log.warning(
                            "[IPTV] PROVIDER=MAG OPERATION=HTTP_REQUEST STAGE=AUTHENTICATION "
                            "METHOD=%s PATH=%s HTTP_STATUS=%d CONTENT_TYPE=%s RESPONSE_BYTES=%d "
                            "RESULT=FAIL ERROR=HTTP_STATUS",
                            method,
                            safe_path,
                            response.status,
                            content_type or "<missing>",
                            response_size,
                        )
                    elif not body:
                        log.warning(
                            "[IPTV] PROVIDER=MAG OPERATION=HTTP_REQUEST STAGE=AUTHENTICATION "
                            "METHOD=%s PATH=%s HTTP_STATUS=%d CONTENT_TYPE=%s RESPONSE_BYTES=0 "
                            "RESULT=FAIL ERROR=EMPTY_SESSION_RESPONSE",
                            method,
                            safe_path,
                            response.status,
                            content_type or "<missing>",
                        )
                        raise NetworkError("MAG response was empty")
                    else:
                        log.debug(
                            "[IPTV] PROVIDER=MAG OPERATION=HTTP_REQUEST STAGE=HTTP_RESPONSE "
                            "METHOD=%s PATH=%s HTTP_STATUS=%d CONTENT_TYPE=%s RESPONSE_BYTES=%d "
                            "RESULT=RECEIVED",
                            method,
                            safe_path,
                            response.status,
                            content_type or "<missing>",
                            response_size,
                        )
                    response.raise_for_status()
                    try:
                        data = json.loads(body)
                    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                        log.warning(
                            "[IPTV] PROVIDER=MAG OPERATION=HTTP_REQUEST STAGE=AUTHENTICATION "
                            "METHOD=%s PATH=%s HTTP_STATUS=%d CONTENT_TYPE=%s RESPONSE_BYTES=%d "
                            "RESULT=FAIL ERROR=MALFORMED_JSON",
                            method,
                            safe_path,
                            response.status,
                            content_type or "<missing>",
                            response_size,
                        )
                        raise NetworkError("MAG response was not valid JSON") from exc
                    log.debug("Response %d from %s", response.status, safe_path)
                    return cast("JSON", data)
            except aiohttp.ClientResponseError as exc:
                if 400 <= exc.status < 500:
                    raise NetworkError(f"HTTP {exc.status} from {url}: {exc.message}") from exc
                log.warning("HTTP %d on attempt %d — %s", exc.status, attempt, exc.message)
                last_exc = exc
            except (TimeoutError, aiohttp.ClientError) as exc:
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
