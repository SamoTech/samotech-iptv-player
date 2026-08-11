"""Provider registry — maps provider keys to implementation classes."""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from .base import BaseProvider

_REGISTRY: dict[str, type["BaseProvider"]] = {}


def register(
    key: str,
) -> Callable[[type[BaseProvider]], type[BaseProvider]]:
    """Class decorator that registers a provider under *key*."""

    def decorator(cls: type[BaseProvider]) -> type[BaseProvider]:
        _REGISTRY[key] = cls
        return cls
    return decorator


class ProviderRegistry:
    @staticmethod
    def get(key: str) -> type["BaseProvider"]:
        if key not in _REGISTRY:
            raise KeyError(f"Unknown provider: {key!r}. Available: {list(_REGISTRY)}")
        return _REGISTRY[key]

    @staticmethod
    def available() -> list[str]:
        return list(_REGISTRY.keys())
