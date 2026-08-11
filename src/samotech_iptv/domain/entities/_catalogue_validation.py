"""Shared validation for provider-sourced catalogue entities."""

from __future__ import annotations

from samotech_iptv.core.exceptions import ValidationError


def validate_catalogue_metadata(
    *,
    item_id: str,
    title: str,
    category_id: str | None,
    year: int | None,
    rating: float | None,
) -> None:
    """Validate metadata that Movie and Series entities expose in common."""
    if not item_id.strip():
        raise ValidationError("id", "Catalogue item ID must not be blank")
    if not title.strip():
        raise ValidationError("title", "Catalogue item title must not be blank")
    if category_id is not None and not category_id.strip():
        raise ValidationError("category_id", "Category ID must not be blank when supplied")
    if year is not None and year < 1:
        raise ValidationError("year", "Year must be a positive integer when supplied")
    if rating is not None and not 0.0 <= rating <= 10.0:
        raise ValidationError("rating", "Rating must be between 0.0 and 10.0 when supplied")
