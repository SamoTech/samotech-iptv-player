"""Unit tests for the network infrastructure layer.

All aiohttp calls are mocked — no real network access.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from samotech_iptv.core.exceptions import (
    AuthenticationError,
    NetworkError,
    ProviderError,
)
from samotech_iptv.infrastructure.error_translation import translate_error
from samotech_iptv.infrastructure.network.exceptions import (
    HttpClientError,
    HttpConnectionError,
    HttpServerError,
    HttpTimeoutError,
)
from samotech_iptv.infrastructure.network.headers import HeadersBuilder
from samotech_iptv.infrastructure.network.retry_policy import RetryPolicy
from samotech_iptv.infrastructure.network.timeouts import TimeoutConfig

# ── RetryPolicy ──────────────────────────────────────────────────────────────────

class TestRetryPolicy:
    def test_default_should_retry_on_first_attempt_503(self) -> None:
        policy = RetryPolicy(max_attempts=3)
        assert policy.should_retry(0, 503) is True

    def test_no_retry_after_last_attempt(self) -> None:
        policy = RetryPolicy(max_attempts=3)
        assert policy.should_retry(2, 503) is False

    def test_no_retry_on_404(self) -> None:
        policy = RetryPolicy(max_attempts=3)
        assert policy.should_retry(0, 404) is False

    def test_retry_on_connection_failure(self) -> None:
        policy = RetryPolicy(max_attempts=3)
        assert policy.should_retry(0, None) is True  # None = connection error

    def test_no_retry_policy(self) -> None:
        policy = RetryPolicy.no_retry()
        assert policy.should_retry(0, 503) is False

    def test_wait_time_increases_with_attempt(self) -> None:
        policy = RetryPolicy(max_attempts=5, base_delay=1.0, jitter=False)
        assert policy.wait_time(0) == pytest.approx(1.0)
        assert policy.wait_time(1) == pytest.approx(2.0)
        assert policy.wait_time(2) == pytest.approx(4.0)

    def test_wait_time_capped_at_max_delay(self) -> None:
        policy = RetryPolicy(max_attempts=10, base_delay=1.0, max_delay=5.0, jitter=False)
        assert policy.wait_time(10) <= 5.0

    def test_invalid_max_attempts_raises(self) -> None:
        with pytest.raises(ValueError):
            RetryPolicy(max_attempts=0)

    def test_invalid_base_delay_raises(self) -> None:
        with pytest.raises(ValueError):
            RetryPolicy(base_delay=-1.0)

    @pytest.mark.asyncio
    async def test_sleep_calls_asyncio_sleep(self) -> None:
        policy = RetryPolicy(max_attempts=3, base_delay=0.01, jitter=False)
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await policy.sleep(0)
            mock_sleep.assert_called_once()


# ── TimeoutConfig ──────────────────────────────────────────────────────────────

class TestTimeoutConfig:
    def test_defaults_are_valid(self) -> None:
        cfg = TimeoutConfig()
        assert cfg.connect == 10.0
        assert cfg.read == 30.0
        assert cfg.total == 60.0

    def test_rejects_zero_connect(self) -> None:
        with pytest.raises(ValueError):
            TimeoutConfig(connect=0)

    def test_rejects_total_less_than_connect_plus_read(self) -> None:
        with pytest.raises(ValueError):
            TimeoutConfig(connect=10.0, read=30.0, total=5.0)


# ── HeadersBuilder ─────────────────────────────────────────────────────────────

class TestHeadersBuilder:
    def test_default_has_user_agent(self) -> None:
        headers = HeadersBuilder().build()
        assert "User-Agent" in headers

    def test_accept_json_set(self) -> None:
        headers = HeadersBuilder().accept_json().build()
        assert headers["Accept"] == "application/json"

    def test_custom_header(self) -> None:
        headers = HeadersBuilder().custom("X-Mac", "AA:BB:CC").build()
        assert headers["X-Mac"] == "AA:BB:CC"

    def test_bearer_token(self) -> None:
        headers = HeadersBuilder().authorization_bearer("tok123").build()
        assert headers["Authorization"] == "Bearer tok123"

    def test_multiple_cookies(self) -> None:
        headers = (
            HeadersBuilder()
            .cookie("session", "abc")
            .cookie("token", "xyz")
            .build()
        )
        assert "session=abc" in headers["Cookie"]
        assert "token=xyz" in headers["Cookie"]

    def test_build_returns_independent_copy(self) -> None:
        builder = HeadersBuilder()
        h1 = builder.build()
        builder.custom("X-Extra", "yes")
        h2 = builder.build()
        assert "X-Extra" not in h1
        assert "X-Extra" in h2


# ── Error translation ────────────────────────────────────────────────────────────

class TestErrorTranslation:
    def test_timeout_becomes_network_error(self) -> None:
        exc = HttpTimeoutError("timed out")
        result = translate_error(exc)
        assert isinstance(result, NetworkError)

    def test_connection_error_becomes_network_error(self) -> None:
        exc = HttpConnectionError("no route")
        result = translate_error(exc)
        assert isinstance(result, NetworkError)

    def test_401_becomes_authentication_error(self) -> None:
        exc = HttpClientError("unauthorized", status_code=401)
        result = translate_error(exc)
        assert isinstance(result, AuthenticationError)

    def test_403_becomes_authentication_error(self) -> None:
        exc = HttpClientError("forbidden", status_code=403)
        result = translate_error(exc)
        assert isinstance(result, AuthenticationError)

    def test_404_becomes_provider_error(self) -> None:
        exc = HttpClientError("not found", status_code=404)
        result = translate_error(exc)
        assert isinstance(result, ProviderError)

    def test_500_becomes_provider_error(self) -> None:
        exc = HttpServerError("oops", status_code=500)
        result = translate_error(exc)
        assert isinstance(result, ProviderError)

    def test_generic_exception_becomes_provider_error(self) -> None:
        result = translate_error(ValueError("something weird"))
        assert isinstance(result, ProviderError)

    def test_domain_error_passes_through(self) -> None:
        original = NetworkError("already domain")
        result = translate_error(original)
        assert result is original
