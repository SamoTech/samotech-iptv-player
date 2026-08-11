"""Retry policy with exponential backoff and jitter.

No networking code lives here — this module is pure logic and is fully
testable without aiohttp or any I/O.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from random import SystemRandom

__all__ = ["RetryPolicy"]

_DEFAULT_RETRYABLE_STATUSES: frozenset[int] = frozenset({429, 500, 502, 503, 504})
_SYSTEM_RANDOM = SystemRandom()


@dataclass(frozen=True)
class RetryPolicy:
    """Defines how many times and how long to wait between retried HTTP requests.

    Attributes:
        max_attempts:      Total attempts including the first try (minimum 1).
        base_delay:        Initial wait in seconds before the first retry.
        max_delay:         Upper cap on computed wait time.
        exponential_base:  Multiplier applied each retry (default 2 = doubling).
        jitter:            When True adds ±25 % random noise to reduce thundering herds.
        retryable_statuses: HTTP status codes that trigger a retry.
    """

    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_statuses: frozenset[int] = field(
        default_factory=lambda: _DEFAULT_RETRYABLE_STATUSES
    )

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("RetryPolicy.max_attempts must be >= 1")
        if self.base_delay <= 0:
            raise ValueError("RetryPolicy.base_delay must be > 0")
        if self.max_delay < self.base_delay:
            raise ValueError("RetryPolicy.max_delay must be >= base_delay")

    def should_retry(self, attempt: int, status_code: int | None) -> bool:
        """Return True if another attempt should be made.

        Args:
            attempt:     The 0-based index of the attempt just completed.
            status_code: The HTTP status that was received, or None for
                         connection-level failures.
        """
        if attempt >= self.max_attempts - 1:
            return False
        if status_code is None:
            return True  # connection-level failures always retry
        return status_code in self.retryable_statuses

    def wait_time(self, attempt: int) -> float:
        """Compute the number of seconds to sleep before the next attempt.

        Args:
            attempt: 0-based index of the attempt that just *failed*.
        """
        delay = min(
            self.base_delay * (self.exponential_base ** attempt),
            self.max_delay,
        )
        if self.jitter:
            noise = delay * 0.25
            delay = delay + _SYSTEM_RANDOM.uniform(-noise, noise)
        return max(delay, 0.0)

    async def sleep(self, attempt: int) -> None:
        """Async sleep for the computed wait time.  Cancellation-safe."""
        await asyncio.sleep(self.wait_time(attempt))

    @classmethod
    def no_retry(cls) -> RetryPolicy:
        """A policy that never retries."""
        return cls(max_attempts=1, base_delay=1.0, max_delay=1.0)

    @classmethod
    def aggressive(cls) -> RetryPolicy:
        """A policy suitable for flaky endpoints (5 attempts, 2 s base)."""
        return cls(max_attempts=5, base_delay=2.0, max_delay=30.0)
