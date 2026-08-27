"""Safe libVLC runtime discovery and initialization."""

from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.core.logging import get_logger
from samotech_iptv.core.safe_logging import sanitize_exception

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = ["VlcRuntimeError", "create_vlc_instance"]

_LOG = get_logger(__name__)


class VlcRuntimeError(RuntimeError):
    """Raised when the python-vlc binding cannot initialize a usable libVLC runtime."""


def create_vlc_instance(arguments: Sequence[str] = ()) -> object:
    """Create one libVLC instance or raise a safe, user-facing runtime error.

    ``python-vlc`` is only a binding; the native libVLC DLL/shared library and
    its plugins must also be discoverable. The native exception is retained as
    a cause for durable diagnostics, but its text is never shown directly to a
    user or written to logs.
    """
    try:
        import vlc  # type: ignore[import-untyped]
    except ImportError as exc:
        _LOG.error(
            "VLC runtime initialization failed stage=binding_import error=%s",
            sanitize_exception(exc),
        )
        raise VlcRuntimeError(
            "The python-vlc binding is not installed. Install the application runtime dependencies."
        ) from exc

    try:
        instance = vlc.Instance(*tuple(arguments))
    except Exception as exc:  # noqa: BLE001
        _LOG.error(
            "VLC runtime initialization failed stage=native_load error=%s",
            sanitize_exception(exc),
        )
        raise VlcRuntimeError(
            "libVLC could not be loaded. Install VLC or repair the bundled VLC runtime."
        ) from exc
    if instance is None:
        _LOG.error("VLC runtime initialization failed stage=native_load result=none")
        raise VlcRuntimeError(
            "libVLC could not be loaded. Install VLC or repair the bundled VLC runtime."
        )
    return instance
