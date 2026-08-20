"""Local, non-secret provider identifiers for manual source dialogs."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlsplit

__all__ = ["generated_provider_id"]


def generated_provider_id(prefix: str, source: str) -> str:
    """Return a bounded local identifier without storing or displaying source secrets."""
    parsed = urlsplit(source)
    raw = parsed.hostname or Path(parsed.path or source).stem or "provider"
    safe = re.sub(r"[^a-z0-9]+", "-", raw.casefold()).strip("-") or "provider"
    return f"{prefix}-{safe}"[:64]
