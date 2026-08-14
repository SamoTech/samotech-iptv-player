"""Category DTOs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from samotech_iptv.application.dtos.content import ContentType

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = ["CategoryDTO", "LoadCategoriesRequest", "LoadCategoriesResponse"]


@dataclass(frozen=True)
class CategoryDTO:
    id: str
    name: str
    provider_id: str
    parent_id: str | None = None


@dataclass(frozen=True)
class LoadCategoriesRequest:
    provider_id: str
    content_type: ContentType = ContentType.LIVE


@dataclass(frozen=True)
class LoadCategoriesResponse:
    categories: Sequence[CategoryDTO] = field(default_factory=list)
    error: str | None = None
    unsupported: bool = False
