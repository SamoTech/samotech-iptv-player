"""ExampleProviderPlugin — minimal reference implementation."""

from __future__ import annotations

from samotech_iptv.plugins.sdk.provider_plugin import IProviderPlugin


class ExampleProviderPlugin(IProviderPlugin):
    """Reference provider plugin — demonstrates the Plugin SDK contract."""

    @property
    def name(self) -> str:
        return "Example Provider"

    @property
    def version(self) -> str:
        return "0.1.0"

    def activate(self) -> None:
        pass

    def deactivate(self) -> None:
        pass
