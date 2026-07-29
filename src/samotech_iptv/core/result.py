"""Result monad — functional error handling without exceptions.

Usage::

    def divide(a: int, b: int) -> Result[float, str]:
        if b == 0:
            return Err("division by zero")
        return Ok(a / b)

    match divide(10, 0):
        case Ok(value):  print(f"got {value}")
        case Err(error): print(f"error: {error}")
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, Iterator, TypeVar, Union

__all__ = ["Result", "Ok", "Err"]

T = TypeVar("T")
E = TypeVar("E")
U = TypeVar("U")


@dataclass(frozen=True)
class Ok(Generic[T]):
    """Successful result carrying a value."""

    value: T

    def is_ok(self) -> bool:
        return True

    def is_err(self) -> bool:
        return False

    def unwrap(self) -> T:
        return self.value

    def unwrap_or(self, default: T) -> T:  # noqa: ARG002
        return self.value

    def map(self, fn: Callable[[T], U]) -> "Ok[U]":
        return Ok(fn(self.value))

    def __iter__(self) -> Iterator[T]:
        yield self.value


@dataclass(frozen=True)
class Err(Generic[E]):
    """Failed result carrying an error."""

    error: E

    def is_ok(self) -> bool:
        return False

    def is_err(self) -> bool:
        return True

    def unwrap(self) -> None:
        raise ValueError(f"Called unwrap() on Err: {self.error!r}")

    def unwrap_or(self, default: T) -> T:
        return default

    def map(self, fn: Callable) -> "Err[E]":  # type: ignore[override]
        return self

    def __iter__(self) -> Iterator[E]:
        yield self.error


#: Union alias for type annotations: ``Result[T, E]``
Result = Union[Ok[T], Err[E]]
