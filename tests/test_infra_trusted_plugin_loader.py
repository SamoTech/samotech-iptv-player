from __future__ import annotations

from pathlib import Path

import pytest
from providers.plugins import load_plugins

from samotech_iptv.infrastructure.plugins.trusted_plugin_loader import (
    PluginLoadError,
    TrustedLocalPluginLoader,
)
from samotech_iptv.infrastructure.providers.provider_factory import ProviderFactory


def _write_plugin(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    return path


def test_legacy_plugin_loader_rejects_automatic_discovery() -> None:
    with pytest.raises(RuntimeError, match="Automatic plugin discovery is disabled"):
        load_plugins()


def test_loader_activates_explicit_reference_plugin_only() -> None:
    factory = ProviderFactory()
    loader = TrustedLocalPluginLoader(factory)
    plugin_path = Path(__file__).parents[1] / "plugins" / "example_provider" / "plugin.py"

    result = loader.load("example_provider", plugin_path)

    assert result.plugin_id == "example_provider"
    assert result.provider_types == ("example_provider.demo",)
    assert factory.supported_types() == frozenset({"example_provider.demo"})
    assert loader.load("example_provider", plugin_path) == result


def test_loader_rejects_unselected_or_non_python_files(tmp_path: Path) -> None:
    loader = TrustedLocalPluginLoader(ProviderFactory())
    non_python = tmp_path / "plugin.txt"
    non_python.write_text("not Python", encoding="utf-8")

    with pytest.raises(PluginLoadError, match="existing Python source"):
        loader.load("sample", non_python)


def test_loader_rejects_identity_and_api_version_mismatches(tmp_path: Path) -> None:
    identity_mismatch = _write_plugin(
        tmp_path / "identity_mismatch.py",
        """
from samotech_iptv.plugins.sdk import PLUGIN_API_VERSION, ProviderPlugin

class DemoPlugin(ProviderPlugin):
    plugin_id = property(lambda self: "other")
    api_version = property(lambda self: PLUGIN_API_VERSION)
    def register(self, context):
        return None

PLUGIN = DemoPlugin()
""",
    )
    api_mismatch = _write_plugin(
        tmp_path / "api_mismatch.py",
        """
from samotech_iptv.plugins.sdk import ProviderPlugin

class DemoPlugin(ProviderPlugin):
    plugin_id = property(lambda self: "sample")
    api_version = property(lambda self: "999")
    def register(self, context):
        return None

PLUGIN = DemoPlugin()
""",
    )
    loader = TrustedLocalPluginLoader(ProviderFactory())

    with pytest.raises(PluginLoadError, match="identity"):
        loader.load("sample", identity_mismatch)
    with pytest.raises(PluginLoadError, match="API version"):
        loader.load("sample", api_mismatch)


def test_loader_rejects_unnamespaced_provider_types_without_factory_side_effects(
    tmp_path: Path,
) -> None:
    plugin_path = _write_plugin(
        tmp_path / "invalid_type.py",
        """
from samotech_iptv.plugins.sdk import PLUGIN_API_VERSION, ProviderPlugin

class DemoPlugin(ProviderPlugin):
    plugin_id = property(lambda self: "sample")
    api_version = property(lambda self: PLUGIN_API_VERSION)
    def register(self, context):
        context.register_provider_type("other.demo", lambda metadata, **kwargs: object())

PLUGIN = DemoPlugin()
""",
    )
    factory = ProviderFactory()

    with pytest.raises(PluginLoadError, match="activation failed"):
        TrustedLocalPluginLoader(factory).load("sample", plugin_path)

    assert factory.supported_types() == frozenset()


def test_loader_discards_pending_registrations_when_plugin_activation_fails(tmp_path: Path) -> None:
    plugin_path = _write_plugin(
        tmp_path / "failing.py",
        """
from samotech_iptv.plugins.sdk import PLUGIN_API_VERSION, ProviderPlugin

class DemoPlugin(ProviderPlugin):
    plugin_id = property(lambda self: "sample")
    api_version = property(lambda self: PLUGIN_API_VERSION)
    def register(self, context):
        context.register_provider_type("sample.demo", lambda metadata, **kwargs: object())
        raise RuntimeError("plugin setup failed")

PLUGIN = DemoPlugin()
""",
    )
    factory = ProviderFactory()

    with pytest.raises(PluginLoadError, match="activation failed"):
        TrustedLocalPluginLoader(factory).load("sample", plugin_path)

    assert factory.supported_types() == frozenset()
