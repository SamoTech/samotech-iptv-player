"""Versioned contract for trusted, explicitly enabled local provider plugins."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from samotech_iptv.core.exceptions import ValidationError

if TYPE_CHECKING:
    from samotech_iptv.infrastructure.providers.provider_factory import (
        ProviderConstructor,
        ProviderFactory,
    )

__all__ = ["PLUGIN_API_VERSION", "ProviderPlugin", "ProviderPluginContext"]

PLUGIN_API_VERSION = "1"
_PLUGIN_ID_RE = re.compile(r"^[a-z][a-z0-9_]{1,63}$")
_PROVIDER_TYPE_RE = re.compile(r"^[a-z][a-z0-9_.-]{1,127}$")


class ProviderPlugin(ABC):
    """Trusted local plugin that registers provider constructors with the host."""

    @property
    @abstractmethod
    def plugin_id(self) -> str:
        """Return a stable lowercase plugin identifier."""
        ...

    @property
    @abstractmethod
    def api_version(self) -> str:
        """Return the SDK API version implemented by this plugin."""
        ...

    @abstractmethod
    def register(self, context: ProviderPluginContext) -> None:
        """Register plugin-owned provider types through the supplied host context."""
        ...


class ProviderPluginContext:
    """Narrow host-owned registration context supplied to one trusted plugin."""

    def __init__(self, factory: ProviderFactory, plugin_id: str) -> None:
        self._factory = factory
        self._plugin_id = self._validate_plugin_id(plugin_id)
        self._pending_registrations: list[tuple[str, ProviderConstructor]] = []

    @property
    def plugin_id(self) -> str:
        """Return the validated identifier of the active plugin."""
        return self._plugin_id

    @property
    def registered_types(self) -> tuple[str, ...]:
        """Return provider types registered by this plugin in activation order."""
        return tuple(provider_type for provider_type, _ in self._pending_registrations)

    def register_provider_type(self, provider_type: str, constructor: ProviderConstructor) -> None:
        """Register one namespaced provider constructor without allowing replacement."""
        normalized_type = self._validate_provider_type(provider_type)
        namespace = f"{self._plugin_id}."
        if not normalized_type.startswith(namespace):
            raise ValidationError(
                "provider_type",
                f"Plugin provider type must start with {namespace!r}",
            )
        if self._factory.is_registered(normalized_type) or any(
            pending_type == normalized_type for pending_type, _ in self._pending_registrations
        ):
            raise ValidationError("provider_type", "Provider type is already registered")
        self._pending_registrations.append((normalized_type, constructor))

    def commit(self) -> None:
        """Apply all validated registrations after the plugin completes successfully."""
        for provider_type, _ in self._pending_registrations:
            if self._factory.is_registered(provider_type):
                raise ValidationError("provider_type", "Provider type is already registered")
        for provider_type, constructor in self._pending_registrations:
            self._factory.register_type(provider_type, constructor)

    @staticmethod
    def _validate_plugin_id(value: str) -> str:
        normalized = value.strip()
        if not _PLUGIN_ID_RE.fullmatch(normalized):
            raise ValidationError(
                "plugin_id", "Plugin ID must be lowercase alphanumeric or underscore"
            )
        return normalized

    @staticmethod
    def _validate_provider_type(value: str) -> str:
        normalized = value.strip()
        if not _PROVIDER_TYPE_RE.fullmatch(normalized):
            raise ValidationError("provider_type", "Provider type has invalid characters")
        return normalized
