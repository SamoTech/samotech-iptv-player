"""Shared type aliases and protocols used across all layers."""

from __future__ import annotations

from typing import Protocol, TypeVar, runtime_checkable

__all__ = [
    "JSON",
    "Headers",
    "EntityId",
    "Comparable",
    "Identifiable",
]

#: Recursive JSON type alias.
type JSON = dict[str, JSON] | list[JSON] | str | int | float | bool | None

#: HTTP headers mapping.
type Headers = dict[str, str]

#: Generic entity identifier.
EntityId = TypeVar("EntityId", str, int)


@runtime_checkable
class Comparable(Protocol):
    """Protocol for objects that support ordering."""

    def __lt__(self, other: object) -> bool: ...
    def __le__(self, other: object) -> bool: ...
    def __gt__(self, other: object) -> bool: ...
    def __ge__(self, other: object) -> bool: ...


@runtime_checkable
class Identifiable(Protocol):
    """Protocol for entities that have a string ``id`` attribute."""

    @property
    def id(self) -> str: ...
