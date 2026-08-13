"""Development diagnostics for structured, timed provider-operation traces."""

from __future__ import annotations

import logging
import re
import time
import traceback
from contextlib import contextmanager
from typing import TYPE_CHECKING
from urllib.parse import urlsplit, urlunsplit

from samotech_iptv.core.logging import get_logger

if TYPE_CHECKING:
    from collections.abc import Iterator

__all__ = ["DiagnosticTrace", "log_exception", "redact_url", "safe_label"]

_LOG = get_logger("diagnostics")


def safe_label(value: object, limit: int = 120) -> str:
    """Normalize a diagnostic label and redact embedded URLs and controls."""
    normalized = " ".join(str(value).split())
    normalized = re.sub(
        r"https?://[^\s)]+",
        lambda match: redact_url(match.group(0)),
        normalized,
        flags=re.IGNORECASE,
    )
    normalized = re.sub(
        r"(?i)(username|password|token|api[_-]?key|authorization|cookie)=([^&\s,;]+)",
        r"\1=<REDACTED>",
        normalized,
    )
    return normalized[:limit]


def redact_url(value: str) -> str:
    """Keep only scheme, host, port, and path from a credential-bearing URL."""
    try:
        parsed = urlsplit(value)
        if not parsed.scheme or not parsed.netloc:
            return "<redacted>"
        host = parsed.hostname or "<invalid-host>"
        if parsed.port is not None:
            host = f"{host}:{parsed.port}"
        return urlunsplit((parsed.scheme, host, parsed.path, "", ""))
    except ValueError:
        return "<redacted>"


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
            safe_label(exc),
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
        self.operation = operation
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
        if self.enabled:
            _LOG.debug("[IPTV] %s: START %s", name, self._fields(fields))
        try:
            yield
        except Exception as exc:  # noqa: BLE001
            if self.enabled:
                _LOG.error(
                    "[IPTV] %s: FAIL %.3fs error_type=%s message=%s %s\n"
                    "[IPTV] FULL TRACEBACK:\n%s",
                    name,
                    time.perf_counter() - started,
                    type(exc).__name__,
                    safe_label(exc),
                    self._fields(fields),
                    safe_label(traceback.format_exc(), limit=10000),
                )
            raise
        else:
            if self.enabled:
                _LOG.debug(
                    "[IPTV] %s: PASS %.3fs %s",
                    name,
                    time.perf_counter() - started,
                    self._fields(fields),
                )

    def result(self, result: str, **fields: object) -> None:
        if self.enabled:
            _LOG.debug(
                "[IPTV] OPERATION RESULT operation=%s provider=%s result=%s duration=%.3fs %s",
                self.operation,
                self.provider_id,
                result,
                time.perf_counter() - self._started,
                self._fields(fields),
            )

    @staticmethod
    def _fields(fields: dict[str, object]) -> str:
        return " ".join(f"{key}={safe_label(value)}" for key, value in fields.items())
