"""Explicit opt-in loader for trusted local Python provider plugins."""

from __future__ import annotations

import hashlib
import importlib.util
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING

from samotech_iptv.plugins.sdk.provider_plugin import (
    PLUGIN_API_VERSION,
    ProviderPlugin,
    ProviderPluginContext,
)

if TYPE_CHECKING:
    from pathlib import Path
    from types import ModuleType

    from samotech_iptv.infrastructure.providers.provider_factory import ProviderFactory

__all__ = ["PluginLoadError", "PluginLoadResult", "TrustedLocalPluginLoader"]


class PluginLoadError(RuntimeError):
    """Raised when an explicitly enabled trusted plugin cannot be loaded safely."""


@dataclass(frozen=True)
class PluginLoadResult:
    """Safe summary of one successfully activated local provider plugin."""

    plugin_id: str
    provider_types: tuple[str, ...]


class TrustedLocalPluginLoader:
    """Load only caller-selected trusted Python plugin files; never auto-discover code."""

    def __init__(self, factory: ProviderFactory) -> None:
        self._factory = factory
        self._loaded: dict[str, PluginLoadResult] = {}

    def load(self, plugin_id: str, plugin_path: Path) -> PluginLoadResult:
        """Import and activate one trusted plugin selected explicitly by its path."""
        if plugin_id in self._loaded:
            return self._loaded[plugin_id]
        path = self._validated_path(plugin_path)
        module_name = self._module_name(plugin_id, path)
        module = self._import_module(module_name, path)
        try:
            plugin = self._plugin(module)
            if plugin.plugin_id != plugin_id:
                raise PluginLoadError("Plugin identity does not match the enabled plugin ID")
            if plugin.api_version != PLUGIN_API_VERSION:
                raise PluginLoadError("Plugin API version is not supported")
            context = ProviderPluginContext(self._factory, plugin.plugin_id)
            plugin.register(context)
            context.commit()
        except PluginLoadError:
            sys.modules.pop(module_name, None)
            raise
        except Exception as exc:  # noqa: BLE001
            sys.modules.pop(module_name, None)
            raise PluginLoadError("Trusted plugin activation failed") from exc

        result = PluginLoadResult(
            plugin_id=plugin.plugin_id, provider_types=context.registered_types
        )
        self._loaded[plugin_id] = result
        return result

    @staticmethod
    def _validated_path(plugin_path: Path) -> Path:
        path = plugin_path.expanduser().resolve()
        if path.suffix != ".py" or not path.is_file():
            raise PluginLoadError("Enabled plugin must be an existing Python source file")
        return path

    @staticmethod
    def _module_name(plugin_id: str, path: Path) -> str:
        digest = hashlib.sha256(f"{plugin_id}\x00{path}".encode()).hexdigest()[:16]
        return f"_samotech_trusted_plugin_{digest}"

    @staticmethod
    def _import_module(module_name: str, path: Path) -> ModuleType:
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise PluginLoadError("Enabled plugin source cannot be imported")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except Exception as exc:  # noqa: BLE001
            sys.modules.pop(module_name, None)
            raise PluginLoadError("Trusted plugin import failed") from exc
        return module

    @staticmethod
    def _plugin(module: ModuleType) -> ProviderPlugin:
        plugin = getattr(module, "PLUGIN", None)
        if not isinstance(plugin, ProviderPlugin):
            raise PluginLoadError("Enabled module does not expose a valid provider plugin")
        return plugin
