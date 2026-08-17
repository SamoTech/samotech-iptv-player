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

_BODY_READ_CHUNK_SIZE = 64 * 1024
_MAX_RESPONSE_BYTES = 16 * 1024 * 1024


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


async def _read_bounded_body(response: aiohttp.ClientResponse) -> bytes:
    """Read one response through a hard byte bound without retaining oversize data."""
    body = bytearray()
    async for chunk in response.content.iter_chunked(_BODY_READ_CHUNK_SIZE):
        if len(body) + len(chunk) > _MAX_RESPONSE_BYTES:
            raise NetworkError("MAG response exceeded the configured size limit")
        body.extend(chunk)
    return bytes(body)


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
        log.debug("HTTP session opened")

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
        diagnostic_stage: str = "AUTHENTICATION",
    ) -> JSON:
        """Issue an authenticated GET relative to the configured or approved profile base."""
        url = _sanitise_url(base_url or self._portal_url, path)
        return await self._request_with_retry(
            "GET",
            url,
            params=params,
            headers=headers,
            diagnostic_stage=diagnostic_stage,
        )

    async def post(
        self,
        path: str,
        *,
        data: Mapping[str, str | int] | None = None,
        headers: dict[str, str] | None = None,
        base_url: str | None = None,
        diagnostic_stage: str = "AUTHENTICATION",
    ) -> JSON:
        """Issue one authenticated form POST relative to an approved profile base."""
        url = _sanitise_url(base_url or self._portal_url, path)
        return await self._request_with_retry(
            "POST",
            url,
            params=None,
            data={key: str(value) for key, value in (data or {}).items()},
            headers=headers,
            diagnostic_stage=diagnostic_stage,
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
                body = await _read_bounded_body(response)
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
        except (TimeoutError, aiohttp.ClientError):
            raise NetworkError("MAG protocol probe did not complete") from None

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
                body = await _read_bounded_body(response)
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
        except (TimeoutError, aiohttp.ClientError):
            raise NetworkError("MAG handshake probe did not complete") from None

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        *,
        params: Mapping[str, str | int] | None = None,
        data: Mapping[str, str | int] | None = None,
        headers: dict[str, str] | None = None,
        diagnostic_stage: str,
    ) -> JSON:
        session = self._session
        if session is None or session.closed:
            raise RuntimeError("Call open() before making requests")

        delay = RETRY_BASE_DELAY
        safe_path = urlparse(url).path or "/"
        attempts_made = 0
        for attempt in range(1, self._max_retries + 1):
            attempts_made = attempt
            request_started = time.perf_counter()
            body_failure_logged = False
            try:
                log.debug(
                    "%s %s (attempt %d/%d)",
                    method,
                    safe_path,
                    attempt,
                    self._max_retries,
                )
                async with session.request(
                    method,
                    url,
                    params=params,
                    data={key: str(value) for key, value in (data or {}).items()} or None,
                    headers=headers,
                    allow_redirects=True,
                ) as response:
                    content_type = response.headers.get("Content-Type", "").split(";", 1)[0]
                    content_length = getattr(response, "content_length", None)
                    transfer_encoding = (
                        "chunked"
                        if "chunked" in response.headers.get("Transfer-Encoding", "").casefold()
                        else "identity"
                    )
                    log.info(
                        "[IPTV] PROVIDER=MAG OPERATION=HTTP_REQUEST STAGE=%s_HTTP_RESPONSE "
                        "METHOD=%s PATH=%s ATTEMPT=%d/%d TOTAL_TIMEOUT=%ss HTTP_STATUS=%d "
                        "CONTENT_TYPE=%s CONTENT_LENGTH=%s TRANSFER_ENCODING=%s "
                        "ELAPSED=%.3fs RESULT=STARTED",
                        diagnostic_stage,
                        method,
                        safe_path,
                        attempt,
                        self._max_retries,
                        self._timeout.total if self._timeout.total is not None else "<none>",
                        response.status,
                        content_type or "<missing>",
                        content_length if content_length is not None else "<missing>",
                        transfer_encoding,
                        time.perf_counter() - request_started,
                    )
                    body = bytearray()
                    chunk_count = 0
                    first_chunk_elapsed: float | None = None
                    last_chunk_elapsed: float | None = None
                    try:
                        async for chunk in response.content.iter_chunked(_BODY_READ_CHUNK_SIZE):
                            if not chunk:
                                continue
                            chunk_elapsed = time.perf_counter() - request_started
                            if first_chunk_elapsed is None:
                                first_chunk_elapsed = chunk_elapsed
                            last_chunk_elapsed = chunk_elapsed
                            if len(body) + len(chunk) > _MAX_RESPONSE_BYTES:
                                raise NetworkError(
                                    "MAG response exceeded the configured size limit"
                                )
                            body.extend(chunk)
                            chunk_count += 1
                    except (TimeoutError, aiohttp.ClientError) as exc:
                        body_failure_logged = True
                        error_kind = (
                            "TIMEOUT"
                            if isinstance(exc, TimeoutError)
                            else (
                                "PAYLOAD_ERROR"
                                if isinstance(exc, aiohttp.ClientPayloadError)
                                else "NETWORK_ERROR"
                            )
                        )
                        elapsed = time.perf_counter() - request_started
                        last_chunk_age = (
                            elapsed - last_chunk_elapsed if last_chunk_elapsed is not None else None
                        )
                        log.warning(
                            "[IPTV] PROVIDER=MAG OPERATION=HTTP_REQUEST STAGE=%s_BODY_INCOMPLETE "
                            "METHOD=%s PATH=%s ATTEMPT=%d/%d TOTAL_TIMEOUT=%ss HTTP_STATUS=%d "
                            "CONTENT_TYPE=%s CONTENT_LENGTH=%s TRANSFER_ENCODING=%s "
                            "RECEIVED_BYTES=%d CHUNKS=%d "
                            "FIRST_BODY_BYTE=%s LAST_CHUNK_AGE=%s BODY_ELAPSED=%.3fs "
                            "RESULT=FAIL ERROR=%s",
                            diagnostic_stage,
                            method,
                            safe_path,
                            attempt,
                            self._max_retries,
                            self._timeout.total if self._timeout.total is not None else "<none>",
                            response.status,
                            content_type or "<missing>",
                            content_length if content_length is not None else "<missing>",
                            transfer_encoding,
                            len(body),
                            chunk_count,
                            (
                                f"{first_chunk_elapsed:.3f}s"
                                if first_chunk_elapsed is not None
                                else "<none>"
                            ),
                            f"{last_chunk_age:.3f}s" if last_chunk_age is not None else "<none>",
                            elapsed,
                            error_kind,
                        )
                        raise
                    response_size = len(body)
                    log.info(
                        "[IPTV] PROVIDER=MAG OPERATION=HTTP_REQUEST STAGE=%s_BODY_COMPLETE "
                        "METHOD=%s PATH=%s ATTEMPT=%d/%d TOTAL_TIMEOUT=%ss RESPONSE_BYTES=%d "
                        "CHUNKS=%d FIRST_BODY_BYTE=%s LAST_BODY_BYTE=%s BODY_ELAPSED=%.3fs "
                        "RESULT=RECEIVED",
                        diagnostic_stage,
                        method,
                        safe_path,
                        attempt,
                        self._max_retries,
                        self._timeout.total if self._timeout.total is not None else "<none>",
                        response_size,
                        chunk_count,
                        (
                            f"{first_chunk_elapsed:.3f}s"
                            if first_chunk_elapsed is not None
                            else "<none>"
                        ),
                        (
                            f"{last_chunk_elapsed:.3f}s"
                            if last_chunk_elapsed is not None
                            else "<none>"
                        ),
                        time.perf_counter() - request_started,
                    )
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
                    except (json.JSONDecodeError, UnicodeDecodeError):
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
                        raise NetworkError("MAG response was not valid JSON") from None
                    log.debug("Response %d from %s", response.status, safe_path)
                    return cast("JSON", data)
            except aiohttp.ClientResponseError as exc:
                if 400 <= exc.status < 500:
                    raise NetworkError(f"HTTP {exc.status} from {safe_path}") from None
                log.warning("HTTP %d on attempt %d path=%s", exc.status, attempt, safe_path)
            except (TimeoutError, aiohttp.ClientError) as exc:
                error_kind = (
                    "TIMEOUT"
                    if isinstance(exc, TimeoutError)
                    else (
                        "PAYLOAD_ERROR"
                        if isinstance(exc, aiohttp.ClientPayloadError)
                        else "NETWORK_ERROR"
                    )
                )
                if not body_failure_logged:
                    log.warning(
                        "[IPTV] PROVIDER=MAG OPERATION=HTTP_REQUEST STAGE=%s_BODY_INCOMPLETE "
                        "METHOD=%s PATH=%s ATTEMPT=%d/%d TOTAL_TIMEOUT=%ss HTTP_STATUS=<none> "
                        "CONTENT_TYPE=<none> CONTENT_LENGTH=<none> TRANSFER_ENCODING=<none> "
                        "RECEIVED_BYTES=0 CHUNKS=0 FIRST_BODY_BYTE=<none> "
                        "LAST_CHUNK_AGE=<none> BODY_ELAPSED=%.3fs RESULT=FAIL ERROR=%s",
                        diagnostic_stage,
                        method,
                        urlparse(url).path or "/",
                        attempt,
                        self._max_retries,
                        self._timeout.total if self._timeout.total is not None else "<none>",
                        time.perf_counter() - request_started,
                        error_kind,
                    )
                log.warning(
                    "Network error on attempt %d path=%s error_type=%s",
                    attempt,
                    safe_path,
                    type(exc).__name__,
                )

            if method.upper() == "POST":
                break
            if attempt < self._max_retries:
                jitter = delay * 0.1
                sleep_for = min(delay + jitter, RETRY_MAX_DELAY)
                log.info("Retrying in %.1fs …", sleep_for)
                await asyncio.sleep(sleep_for)
                delay = min(delay * 2, RETRY_MAX_DELAY)

        raise NetworkError(
            f"Request {method} {safe_path} failed after {attempts_made} attempts"
        ) from None
