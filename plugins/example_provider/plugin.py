"""Reference trusted provider plugin for the SamoTech provider-plugin SDK."""

from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.plugins.sdk import PLUGIN_API_VERSION, ProviderPlugin, ProviderPluginContext

if TYPE_CHECKING:
    from samotech_iptv.infrastructure.providers.provider_metadata import InfraProviderMetadata


class ExampleProviderPlugin(ProviderPlugin):
    """Reference plugin showing explicit provider-type registration only."""

    @property
    def plugin_id(self) -> str:
        """Return the stable provider-plugin identifier."""
        return "example_provider"

    @property
    def api_version(self) -> str:
        """Return the supported provider-plugin SDK version."""
        return PLUGIN_API_VERSION

    def register(self, context: ProviderPluginContext) -> None:
        """Register the reference namespaced provider type with the host factory."""
        context.register_provider_type("example_provider.demo", _build_provider)


def _build_provider(metadata: InfraProviderMetadata, **_: object) -> object:
    """Raise until an application replaces this reference constructor with an adapter."""
    raise NotImplementedError(
        f"Example provider adapter is not implemented for {metadata.provider_id}"
    )


PLUGIN = ExampleProviderPlugin()
