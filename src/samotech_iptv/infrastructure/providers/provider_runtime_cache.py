"""Own live provider runtimes without retaining provider secrets in the registry."""

from __future__ import annotations

import asyncio
import hashlib
import inspect
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from samotech_iptv.infrastructure.providers.provider_context import ProviderContext
    from samotech_iptv.infrastructure.providers.provider_factory import ProviderFactory
    from samotech_iptv.infrastructure.providers.provider_metadata import InfraProviderMetadata

__all__ = ["ProviderRuntimeCache"]


@dataclass(frozen=True)
class _RuntimeEntry:
    """One live provider instance and its non-secret metadata generation."""

    metadata_fingerprint: bytes
    instance: object


class ProviderRuntimeCache:
    """Reuse provider instances while keeping lifecycle ownership in infrastructure.

    The registry continues to own only provider metadata. This cache owns live
    instances and closes them when an entry is invalidated or the application
    shuts down. Credentials, tokens, cookies, and response data remain inside
    the provider instance and are never copied into cache state or diagnostics.
    """

    def __init__(self, factory: ProviderFactory, context: ProviderContext) -> None:
        self._factory = factory
        self._context = context
        self._entries: dict[str, _RuntimeEntry] = {}
        self._closing_tasks: set[asyncio.Task[None]] = set()
        self._provider_creation_count = 0
        self._closed = False

    @property
    def provider_creation_count(self) -> int:
        """Return the number of provider instances constructed by this cache."""
        return self._provider_creation_count

    def diagnostics(self) -> dict[str, int]:
        """Return safe aggregate runtime counts without provider metadata values."""
        return {
            "provider_creation_count": self._provider_creation_count,
            "active_provider_runtime_count": len(self._entries),
        }

    def get_or_create(self, metadata: InfraProviderMetadata) -> object:
        """Return the current runtime or construct one through the existing factory."""
        if self._closed:
            raise RuntimeError("Provider runtime cache is closed")

        provider_id = metadata.provider_id
        fingerprint = self._metadata_fingerprint(metadata)
        existing = self._entries.get(provider_id)
        if existing is not None and existing.metadata_fingerprint == fingerprint:
            return existing.instance

        if existing is not None:
            self._entries.pop(provider_id, None)
            self._schedule_close(existing.instance)

        instance = self._factory.create(metadata, context=self._context)
        self._provider_creation_count += 1
        self._install_failure_hook(provider_id, instance)
        self._entries[provider_id] = _RuntimeEntry(fingerprint, instance)
        return instance

    async def invalidate(self, provider_id: str, reason: str) -> None:
        """Evict and close one provider runtime, ignoring only safe close failures."""
        del reason  # The reason is intentionally not retained or logged here.
        entry = self._entries.pop(provider_id, None)
        if entry is None:
            return
        await self._close_instance(entry.instance)

    async def invalidate_if_current(
        self,
        provider_id: str,
        instance: object,
        reason: str,
    ) -> None:
        """Evict only when the failure belongs to the currently cached instance."""
        del reason  # The reason is intentionally not retained or logged here.
        entry = self._entries.get(provider_id)
        if entry is None or entry.instance is not instance:
            return
        self._entries.pop(provider_id, None)
        await self._close_instance(entry.instance)

    async def close_all(self) -> None:
        """Close every retained runtime exactly once and clear the cache."""
        if self._closed:
            return
        self._closed = True
        entries = tuple(self._entries.values())
        self._entries.clear()
        for entry in entries:
            await self._close_instance(entry.instance)
        if self._closing_tasks:
            await asyncio.gather(*tuple(self._closing_tasks), return_exceptions=True)
            self._closing_tasks.clear()

    def _install_failure_hook(self, provider_id: str, instance: object) -> None:
        setter = getattr(instance, "set_runtime_failure_callback", None)
        if not callable(setter):
            return

        async def on_failure(reason: str) -> None:
            await self.invalidate_if_current(provider_id, instance, reason)

        setter(cast("Callable[[str], Awaitable[None]]", on_failure))

    def _schedule_close(self, instance: object) -> None:
        """Close a stale runtime without blocking synchronous provider resolution."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        task = loop.create_task(self._close_instance(instance))
        self._closing_tasks.add(task)
        task.add_done_callback(self._closing_tasks.discard)

    async def _close_instance(self, instance: object) -> None:
        close = getattr(instance, "close_session", None)
        if not callable(close):
            close = getattr(instance, "close", None)
        if not callable(close):
            return
        try:
            result = close()
            if inspect.isawaitable(result):
                await result
        except asyncio.CancelledError:
            raise
        except Exception:
            # Runtime shutdown must continue even when one provider cannot close.
            return

    @staticmethod
    def _metadata_fingerprint(metadata: InfraProviderMetadata) -> bytes:
        """Build an opaque generation marker without retaining or logging metadata values."""
        value = repr(
            (
                metadata.provider_id,
                metadata.provider_type,
                metadata.base_url,
                metadata.is_active,
                tuple(sorted(str(capability) for capability in metadata.capabilities)),
                metadata.source_is_secure,
            )
        ).encode("utf-8")
        return hashlib.sha256(value).digest()
