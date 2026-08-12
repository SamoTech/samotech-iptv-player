# Trusted Provider Plugin SDK

## Security model

The provider-plugin SDK supports **trusted, user-enabled local Python plugins only**. A plugin is executable Python code and therefore has the same operating-system permissions as the desktop application. It can access resources that the user account can access, including local files and network services.

> **Do not enable a plugin unless you trust its author and have reviewed its source.** The loader is intentionally not a sandbox, package-signature verifier, permission system, marketplace client, updater, or remote downloader.

The host never scans directories, imports every installed module, or activates a plugin at package import time. Application composition must explicitly supply both a selected plugin ID and its local `.py` path to `TrustedLocalPluginLoader.load()`.

| Boundary | Enforced behavior |
|---|---|
| Discovery | None. Every plugin path is explicitly selected by the host/user configuration. |
| Source | Existing local Python source files only; non-`.py` paths are rejected. |
| Identity | The requested ID must exactly match `PLUGIN.plugin_id`. |
| Compatibility | Plugins must declare `PLUGIN_API_VERSION` (`"1"`). |
| Registration | Plugins receive only `ProviderPluginContext`, which registers namespaced provider constructors with the host-owned `ProviderFactory`. |
| Namespace | A plugin with ID `weather_provider` may only register provider types beginning with `weather_provider.`. |
| Failure isolation | Import and activation failures raise generic `PluginLoadError` values; failed activation does not commit pending provider registrations. |
| Activation | Re-loading a successfully activated ID returns its existing safe summary and does not import it again. |

## Plugin API version 1

A plugin exports exactly one module-level `PLUGIN` instance that implements `ProviderPlugin`.

```python
from __future__ import annotations

from samotech_iptv.plugins.sdk import (
    PLUGIN_API_VERSION,
    ProviderPlugin,
    ProviderPluginContext,
)


class WeatherProviderPlugin(ProviderPlugin):
    @property
    def plugin_id(self) -> str:
        return "weather_provider"

    @property
    def api_version(self) -> str:
        return PLUGIN_API_VERSION

    def register(self, context: ProviderPluginContext) -> None:
        context.register_provider_type("weather_provider.demo", build_provider)


def build_provider(metadata, **context):
    return WeatherProviderAdapter(metadata, **context)


PLUGIN = WeatherProviderPlugin()
```

Provider constructors receive the existing infrastructure `InfraProviderMetadata` and host-supplied keyword context, then return an object that implements one or more established provider capability interfaces. Plugin authors should depend on the existing canonical domain entities, value objects, and capability ABCs rather than returning protocol payloads to the application or presentation layers.

The `ProviderPluginContext` retains registrations until the plugin's `register()` method returns. The trusted loader commits those registrations only after successful validation, preventing a plugin failure from leaving a partially registered provider type in the factory.

## Host integration

The composition root owns the allow-list and loader invocation. It must not enumerate paths or accept paths from untrusted remote content.

```python
from pathlib import Path

from samotech_iptv.infrastructure.plugins import TrustedLocalPluginLoader
from samotech_iptv.infrastructure.providers.provider_factory import ProviderFactory

factory = ProviderFactory()
loader = TrustedLocalPluginLoader(factory)
result = loader.load("weather_provider", Path("/trusted/plugins/weather_provider.py"))
```

`PluginLoadResult` exposes only the plugin ID and registered provider type names. It intentionally does not expose module objects, constructor internals, credentials, or provider session state.

## Reference plugin

[`plugins/example_provider/plugin.py`](../plugins/example_provider/plugin.py) is a minimal, tested reference plugin. It registers `example_provider.demo` but deliberately has no real protocol implementation. Replace its constructor with a capability-oriented adapter only when the corresponding provider protocol has verified fixtures and tests.

## Non-goals

The following capabilities require a future security and product decision and are deliberately out of scope for API version 1:

- Sandboxing or process isolation.
- Package signing, certificate trust, or marketplace distribution.
- Automatic plugin discovery, auto-update, or remote installation.
- Plugin access to UI objects, player adapters, credential stores, or provider sessions outside the narrow constructor context supplied by the host.
- A compatibility guarantee across future plugin API versions.
