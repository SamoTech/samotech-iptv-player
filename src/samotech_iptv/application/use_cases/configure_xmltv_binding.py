"""Configure a registered provider's non-secret local XMLTV source binding."""

from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.application.dtos import (
    ConfigureXMLTVBindingRequest,
    ConfigureXMLTVBindingResponse,
)
from samotech_iptv.core.logging import get_logger
from samotech_iptv.domain.entities.xmltv_binding import XMLTVBinding, XMLTVChannelMapping
from samotech_iptv.domain.value_objects.channel_id import ChannelId
from samotech_iptv.domain.value_objects.provider_id import ProviderId

if TYPE_CHECKING:
    from samotech_iptv.application.ports.provider_resolver_port import ProviderResolverPort
    from samotech_iptv.domain.repositories.xmltv_binding_repository import XMLTVBindingRepository

__all__ = ["ConfigureXMLTVBinding"]

_LOG = get_logger(__name__)
_ERROR = "Unable to save XMLTV guide configuration"


class ConfigureXMLTVBinding:
    """Persist a local XMLTV source after validating its explicit channel mappings."""

    def __init__(
        self,
        provider_resolver: ProviderResolverPort,
        binding_repository: XMLTVBindingRepository,
    ) -> None:
        self._provider_resolver = provider_resolver
        self._binding_repository = binding_repository

    async def execute(
        self,
        request: ConfigureXMLTVBindingRequest,
    ) -> ConfigureXMLTVBindingResponse:
        """Save a binding only when every mapped canonical channel is registered."""
        try:
            provider_id = ProviderId(request.provider_id)
            binding = XMLTVBinding(
                provider_id=provider_id,
                source=request.source,
                mappings=tuple(
                    XMLTVChannelMapping(
                        source_channel_id=mapping.source_channel_id,
                        channel_id=ChannelId(mapping.channel_id),
                    )
                    for mapping in request.mappings
                ),
            )
            provider = self._provider_resolver.resolve_catalog_provider(provider_id.value)
            channels = await provider.load_channels()
            registered_channel_ids = {channel.id for channel in channels}
            if any(
                mapping.channel_id not in registered_channel_ids for mapping in binding.mappings
            ):
                return ConfigureXMLTVBindingResponse(success=False, error=_ERROR)
            await self._binding_repository.save(binding)
        except Exception:  # noqa: BLE001
            _LOG.error("Unable to save XMLTV guide configuration")
            return ConfigureXMLTVBindingResponse(success=False, error=_ERROR)
        return ConfigureXMLTVBindingResponse(success=True)
