"""Development diagnostics for structured, timed provider-operation traces."""

from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from typing import TYPE_CHECKING

from samotech_iptv.core.logging import get_logger
from samotech_iptv.core.safe_logging import safe_label, sanitize_url

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
    logger: logging.Logger, _message: str, _exc: BaseException, **_fields: object
) -> None:
    """Log a static exception event without forwarding exception-controlled text."""
    if logger.isEnabledFor(logging.DEBUG):
        logger.error("diagnostic_exception error_type=exception details=redacted")
    else:
        logger.error("diagnostic_exception error_type=exception")


class DiagnosticTrace:
    """Emit timed provider-operation events without forwarding input-controlled text."""

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
            _LOG.debug("[IPTV] PROVIDER OPERATION START")

    @contextmanager
    def stage(self, _name: str, **_fields: object) -> Iterator[None]:
        started = time.perf_counter()
        if self.enabled:
            _LOG.debug("[IPTV] STAGE START")
        try:
            yield
        except Exception:  # noqa: BLE001
            if self.enabled:
                _LOG.error(
                    "[IPTV] STAGE FAIL duration=%.3fs error_type=exception",
                    time.perf_counter() - started,
                )
            raise
        else:
            if self.enabled:
                _LOG.debug(
                    "[IPTV] STAGE PASS duration=%.3fs",
                    time.perf_counter() - started,
                )

    def result(self, _result: str, **_fields: object) -> None:
        if self.enabled:
            _LOG.debug(
                "[IPTV] OPERATION RESULT duration=%.3fs",
                time.perf_counter() - self._started,
            )
