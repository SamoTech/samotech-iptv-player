"""Small, deterministic redaction helpers for security-safe diagnostics."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from urllib.parse import urlsplit, urlunsplit

__all__ = [
    "sanitize_exception",
    "sanitize_headers",
    "sanitize_mapping",
    "sanitize_url",
    "safe_label",
]

_SENSITIVE_KEY_PARTS = {
    "authorization",
    "cookie",
    "key",
    "mac",
    "password",
    "passwd",
    "pwd",
    "secret",
    "token",
    "username",
}
_SENSITIVE_QUERY_KEYS = {
    "access_token",
    "api_key",
    "apikey",
    "authorization",
    "cookie",
    "mac",
    "password",
    "passwd",
    "pwd",
    "refresh_token",
    "secret",
    "session",
    "token",
    "username",
}
_URL_RE = re.compile(r'(?i)\b[a-z][a-z0-9+.-]*://[^\s<>" ]+')
_ASSIGNMENT_RE = re.compile(
    r"(?i)(?P<key>authorization|cookie|mac(?:_address)?|password|passwd|pwd|secret|token|username)"
    r"(?P<separator>\s*[:=]\s*)(?P<value>[^\s,;}&]+)"
)
_BEARER_RE = re.compile(r"(?i)\bBearer\s+[^\s,;}&]+")


def _is_sensitive_key(key: object) -> bool:
    normalized = str(key).casefold().replace("-", "_")
    return normalized in _SENSITIVE_KEY_PARTS or any(
        part in normalized.split("_") for part in _SENSITIVE_KEY_PARTS
    )


def sanitize_url(value: str) -> str:
    """Keep safe URL origin/path information while removing userinfo and query data."""
    try:
        parsed = urlsplit(value)
        if not parsed.scheme or not parsed.netloc:
            return "<redacted>"
        hostname = parsed.hostname or "<invalid-host>"
        if parsed.port is not None:
            hostname = f"{hostname}:{parsed.port}"
        return urlunsplit((parsed.scheme, hostname, parsed.path, "", ""))
    except ValueError:
        return "<redacted>"


def _sanitize_text(value: str, limit: int = 120) -> str:
    normalized = " ".join(value.split())
    normalized = _URL_RE.sub(lambda match: sanitize_url(match.group(0)), normalized)
    normalized = _BEARER_RE.sub("Bearer <REDACTED>", normalized)
    normalized = _ASSIGNMENT_RE.sub(
        lambda match: f"{match.group('key')}{match.group('separator')}<REDACTED>",
        normalized,
    )
    return normalized[:limit]


def sanitize_mapping(value: Mapping[object, object]) -> dict[str, object]:
    """Recursively sanitize mapping values while retaining safe keys and structure."""
    sanitized: dict[str, object] = {}
    for key, item in value.items():
        safe_key = str(key)
        if _is_sensitive_key(key):
            sanitized[safe_key] = "<REDACTED>"
        elif isinstance(item, Mapping):
            sanitized[safe_key] = sanitize_mapping(item)
        elif isinstance(item, Sequence) and not isinstance(item, (str, bytes, bytearray)):
            sanitized[safe_key] = [sanitize_value(entry) for entry in item]
        else:
            sanitized[safe_key] = sanitize_value(item)
    return sanitized


def sanitize_value(value: object) -> object:
    if isinstance(value, Mapping):
        return sanitize_mapping(value)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [sanitize_value(entry) for entry in value]
    if isinstance(value, bytes):
        return "<bytes>"
    if isinstance(value, str):
        return _sanitize_text(value)
    return value


def sanitize_headers(headers: Mapping[object, object]) -> dict[str, object]:
    """Sanitize HTTP header mappings without exposing authentication material."""
    return sanitize_mapping(headers)


def sanitize_exception(exc: BaseException, limit: int = 1000) -> str:
    """Return a safe exception type/message summary without raw sensitive text."""
    return f"{type(exc).__name__}: {_sanitize_text(str(exc), limit=limit)}"


def safe_label(value: object, limit: int = 120) -> str:
    """Convert diagnostic values to bounded, recursively sanitized text."""
    sanitized = sanitize_value(value)
    if isinstance(sanitized, (dict, list, tuple)):
        rendered = json.dumps(sanitized, ensure_ascii=True, sort_keys=True, default=str)
    else:
        rendered = str(sanitized)
    return _sanitize_text(rendered, limit=limit)
