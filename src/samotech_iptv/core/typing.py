"""Shared type aliases and protocols used across all layers."""
from __future__ import annotations

from typing import Any, Protocol, TypeAlias, TypeVar, runtime_checkable

__all__ = [
    "JSON",
    "Headers",
    "EntityId",
    "Comparable",
    "Identifiable",
]

#: Recursive JSON type alias.
JSON: TypeAlias = "dict[str, Any] | list[Any] | str | int | float | bool | None"

#: HTTP headers mapping.
Headers: TypeAlias = dict[str, str]

#: Generic entity identifier.
EntityId = TypeVar("EntityId", str, int)


@runtime_checkable
class Comparable(Protocol):
    """Protocol for objects that support ordering."""

    def __lt__(self, other: Any) -> bool: ...
    def __le__(self, other: Any) -> bool: ...
    def __gt__(self, other: Any) -> bool: ...
    def __ge__(self, other: Any) -> bool: ...


@runtime_checkable
class Identifiable(Protocol):
    """Protocol for entities that have a string ``id`` attribute."""

    @property
    def id(self) -> str: ...
