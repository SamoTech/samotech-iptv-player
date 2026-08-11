"""Timeout configuration for HTTP requests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import aiohttp

__all__ = ["TimeoutConfig"]


@dataclass(frozen=True)
class TimeoutConfig:
    """Immutable timeout settings for an HTTP request.

    All values are in seconds.  Pass an instance to ``AsyncHttpClient``
    or ``HttpSession`` at construction time.

    Attributes:
        connect:   Maximum seconds to wait for TCP handshake.
        read:      Maximum seconds to wait for the first byte of the response.
        total:     Hard wall-clock ceiling for the entire request/response cycle.
    """

    connect: float = 10.0
    read: float = 30.0
    total: float = 60.0

    def __post_init__(self) -> None:
        for field, val in (
            ("connect", self.connect),
            ("read", self.read),
            ("total", self.total),
        ):
            if val <= 0:
                raise ValueError(f"TimeoutConfig.{field} must be > 0, got {val}")
        if self.total < self.connect + self.read:
            raise ValueError(
                "TimeoutConfig.total must be >= connect + read "
                f"({self.connect + self.read}), got {self.total}"
            )

    def to_aiohttp(self) -> aiohttp.ClientTimeout:
        """Convert to ``aiohttp.ClientTimeout``.

        Import is deferred to avoid a hard dependency at module level when
        aiohttp is not installed (e.g. during unit tests that mock it).
        """
        import aiohttp  # noqa: PLC0415

        return aiohttp.ClientTimeout(
            sock_connect=self.connect,
            sock_read=self.read,
            total=self.total,
        )
