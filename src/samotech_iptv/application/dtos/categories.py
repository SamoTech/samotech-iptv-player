"""Category DTOs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Sequence

__all__ = ["CategoryDTO", "LoadCategoriesRequest", "LoadCategoriesResponse"]


@dataclass(frozen=True)
class CategoryDTO:
    id: str
    name: str
    provider_id: str
    parent_id: Optional[str] = None


@dataclass(frozen=True)
class LoadCategoriesRequest:
    provider_id: str


@dataclass(frozen=True)
class LoadCategoriesResponse:
    categories: Sequence[CategoryDTO] = field(default_factory=list)
    error: Optional[str] = None
