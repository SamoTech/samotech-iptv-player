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
    validate_nonblank_text(item_id, field="id", label="Catalogue item ID")
    validate_nonblank_text(title, field="title", label="Catalogue item title")
    if category_id is not None:
        validate_nonblank_text(
            category_id,
            field="category_id",
            label="Category ID",
            when_supplied=True,
        )
    if year is not None and year < 1:
        raise ValidationError("year", "Year must be a positive integer when supplied")
    if rating is not None and not 0.0 <= rating <= 10.0:
        raise ValidationError("rating", "Rating must be between 0.0 and 10.0 when supplied")


def validate_nonblank_text(
    value: str,
    *,
    field: str,
    label: str,
    when_supplied: bool = False,
) -> None:
    """Reject blank required strings using the domain's standard error type."""
    if not value.strip():
        suffix = " when supplied" if when_supplied else ""
        raise ValidationError(field, f"{label} must not be blank{suffix}")
