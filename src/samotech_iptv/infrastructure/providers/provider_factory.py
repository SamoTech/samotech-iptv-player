"""Provider factory — discover and instantiate providers by type string.

The factory maintains a type registry that maps type strings (e.g. ``"mag"``)
to callable factories.  Adapter registration happens in Phase B.2 by
calling ``ProviderFactory.register_type()``.

No MAG, Xtream, or M3U adapters are created here.
"""
from __future__ import annotations

from typing import Any, Callable, Optional

from samotech_iptv.core.exceptions import NotFoundError
from samotech_iptv.core.logging import get_logger
from samotech_iptv.infrastructure.providers.provider_metadata import InfraProviderMetadata

__all__ = ["ProviderFactory"]

_log = get_logger(__name__)

# Type alias: a callable that takes InfraProviderMetadata + kwargs and returns
# an object implementing one or more capability interfaces.
ProviderConstructor = Callable[..., Any]


class ProviderFactory:
    """Registry of provider type constructors.

    Usage::

        factory = ProviderFactory()

        # Phase B.2 — called by MagProviderAdapter module at import time:
        factory.register_type("mag", lambda meta, **kw: MagProviderAdapter(meta, **kw))

        # Application startup:
        instance = factory.create(mag_metadata, http_client=client)
    """

    def __init__(self) -> None:
        self._constructors: dict[str, ProviderConstructor] = {}

    def register_type(
        self,
        type_name: str,
        constructor: ProviderConstructor,
    ) -> None:
        """Register a factory callable for a provider type.

        Args:
            type_name:   Lowercase discriminator (e.g. ``"mag"``).
            constructor: Callable ``(metadata: InfraProviderMetadata, **kwargs) -> Any``.
        """
        self._constructors[type_name] = constructor
        _log.info("ProviderFactory registered type=%s", type_name)

    def create(
        self,
        metadata: InfraProviderMetadata,
        **kwargs: Any,
    ) -> Any:
        """Instantiate a provider from its metadata.

        Args:
            metadata: Provider runtime metadata (from the registry).
            **kwargs: Forwarded verbatim to the constructor (e.g.
                      ``http_client=...``, ``credential_store=...``).

        Raises:
            NotFoundError: If no constructor is registered for this type.
        """
        constructor = self._constructors.get(metadata.provider_type)
        if constructor is None:
            raise NotFoundError(
                resource_type="ProviderType",
                resource_id=metadata.provider_type,
            )
        _log.debug("Creating provider id=%s type=%s",
                   metadata.provider_id, metadata.provider_type)
        return constructor(metadata, **kwargs)

    def supported_types(self) -> frozenset[str]:
        """Return the set of registered provider type names."""
        return frozenset(self._constructors)

    def is_registered(self, type_name: str) -> bool:
        return type_name in self._constructors
