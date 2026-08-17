"""Development diagnostics for structured, timed provider-operation traces."""

from __future__ import annotations

import logging
import time
import traceback
from contextlib import contextmanager
from typing import TYPE_CHECKING

from samotech_iptv.core.logging import get_logger
from samotech_iptv.core.safe_logging import (
    safe_label,
    sanitize_exception,
    sanitize_url,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

__all__ = [
    "DiagnosticTrace",
    "log_exception",
    "redact_url",
    "safe_label",
]

_LOG = get_logger("diagnostics")

redact_url = sanitize_url


def log_exception(
    logger: logging.Logger, message: str, exc: BaseException, **fields: object
) -> None:
    """Log a safe exception summary and a redacted traceback only in debug mode."""
    safe_fields = " ".join(f"{key}={safe_label(value)}" for key, value in fields.items())
    if logger.isEnabledFor(logging.DEBUG):
        logger.error(
            "%s error_type=%s message=%s %s\\nFULL TRACEBACK:\\n%s",
            message,
            type(exc).__name__,
            sanitize_exception(exc),
            safe_fields,
            safe_label(traceback.format_exc(), limit=10000),
        )
    else:
        logger.error(
            "%s error_type=%s %s",
            message,
            type(exc).__name__,
            safe_fields,
        )


class DiagnosticTrace:
    """Emit detailed provider-operation stages only when DEBUG logging is enabled."""

    def __init__(self, operation: str, provider_id: str, provider_type: str) -> None:
        self.operation = safe_label(operation)
        self.provider_id = safe_label(provider_id)
        self.provider_type = safe_label(provider_type)
        self._started = time.perf_counter()

    @property
    def enabled(self) -> bool:
        return _LOG.isEnabledFor(logging.DEBUG)

    def start(self) -> None:
        if self.enabled:
            _LOG.debug(
                "============================================================\n"
                "[IPTV] PROVIDER OPERATION\n"
                "[IPTV] Operation: %s\n[IPTV] Provider ID: %s\n[IPTV] Provider Type: %s",
                self.operation,
                self.provider_id,
                self.provider_type,
            )

    @contextmanager
    def stage(self, name: str, **fields: object) -> Iterator[None]:
        started = time.perf_counter()
        safe_name = safe_label(name)
        if self.enabled:
            _LOG.debug("[IPTV] %s: START %s", safe_name, self._fields(fields))
        try:
            yield
        except Exception as exc:  # noqa: BLE001
            if self.enabled:
                _LOG.error(
                    "[IPTV] %s: FAIL %.3fs error_type=%s message=%s %s\n"
                    "[IPTV] FULL TRACEBACK:\n%s",
                    safe_name,
                    time.perf_counter() - started,
                    type(exc).__name__,
                    sanitize_exception(exc),
                    self._fields(fields),
                    safe_label(traceback.format_exc(), limit=10000),
                )
            raise
        else:
            if self.enabled:
                _LOG.debug(
                    "[IPTV] %s: PASS %.3fs %s",
                    safe_name,
                    time.perf_counter() - started,
                    self._fields(fields),
                )

    def result(self, result: str, **fields: object) -> None:
        if self.enabled:
            _LOG.debug(
                "[IPTV] OPERATION RESULT operation=%s provider=%s result=%s duration=%.3fs %s",
                self.operation,
                self.provider_id,
                safe_label(result),
                time.perf_counter() - self._started,
                self._fields(fields),
            )

    @staticmethod
    def _fields(fields: dict[str, object]) -> str:
        return " ".join(f"{key}={safe_label(value)}" for key, value in fields.items())
