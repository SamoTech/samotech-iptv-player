from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from samotech_iptv.infrastructure.player.vlc_runtime import (
    VlcRuntimeError,
    create_vlc_instance,
)


def test_create_vlc_instance_returns_native_instance(monkeypatch: pytest.MonkeyPatch) -> None:
    instance = object()
    monkeypatch.setitem(sys.modules, "vlc", SimpleNamespace(Instance=lambda: instance))

    assert create_vlc_instance() is instance


def test_create_vlc_instance_converts_native_load_failure_without_secret_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail() -> None:
        raise OSError("token=super-secret-value")

    monkeypatch.setitem(sys.modules, "vlc", SimpleNamespace(Instance=fail))

    with pytest.raises(VlcRuntimeError, match="libVLC could not be loaded") as error:
        create_vlc_instance()

    assert "super-secret-value" not in str(error.value)


def test_create_vlc_instance_rejects_none_instance(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "vlc", SimpleNamespace(Instance=lambda: None))

    with pytest.raises(VlcRuntimeError, match="libVLC could not be loaded"):
        create_vlc_instance()
