"""Network infrastructure package.

Provides a reusable, provider-agnostic async HTTP client built on aiohttp.
All provider adapters MUST use these services rather than creating their
own aiohttp sessions.

Public surface::

    from samotech_iptv.infrastructure.network import (
        AsyncHttpClient,
        HttpSession,
        RetryPolicy,
        TimeoutConfig,
        HeadersBuilder,
        HttpError,
        HttpTimeoutError,
        HttpClientError,
        HttpServerError,
    )
"""
from samotech_iptv.infrastructure.network.http_client import AsyncHttpClient
from samotech_iptv.infrastructure.network.http_session import HttpSession
from samotech_iptv.infrastructure.network.retry_policy import RetryPolicy
from samotech_iptv.infrastructure.network.timeouts import TimeoutConfig
from samotech_iptv.infrastructure.network.headers import HeadersBuilder
from samotech_iptv.infrastructure.network.exceptions import (
    HttpError,
    HttpTimeoutError,
    HttpClientError,
    HttpServerError,
    HttpConnectionError,
)

__all__ = [
    "AsyncHttpClient",
    "HttpSession",
    "RetryPolicy",
    "TimeoutConfig",
    "HeadersBuilder",
    "HttpError",
    "HttpTimeoutError",
    "HttpClientError",
    "HttpServerError",
    "HttpConnectionError",
]
