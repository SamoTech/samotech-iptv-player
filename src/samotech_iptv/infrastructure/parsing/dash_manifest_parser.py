"""Parse bounded MPEG-DASH MPD manifest metadata independently from providers."""

from __future__ import annotations

from dataclasses import dataclass

from defusedxml import ElementTree

__all__ = ["DASHManifest", "DASHManifestError", "DASHManifestParser", "DASHRepresentation"]


class DASHManifestError(ValueError):
    """Raised when MPD XML cannot be represented safely."""


@dataclass(frozen=True)
class DASHRepresentation:
    """One advertised MPEG-DASH representation."""

    id: str
    bandwidth: int | None = None


@dataclass(frozen=True)
class DASHManifest:
    """A bounded representation of an MPD's playback type and representations."""

    is_live: bool
    representations: tuple[DASHRepresentation, ...]


class DASHManifestParser:
    """Parse MPD type and representation metadata without downloading media segments."""

    def parse(self, text: str) -> DASHManifest:
        """Return the MPD live/VOD classification and declared representations."""
        try:
            root = ElementTree.fromstring(text)
        except ElementTree.ParseError as exc:
            raise DASHManifestError("Invalid MPEG-DASH MPD XML") from exc
        if root.tag.rsplit("}", maxsplit=1)[-1] != "MPD":
            raise DASHManifestError("MPEG-DASH manifest root must be MPD")
        representations = tuple(
            DASHRepresentation(
                id=element.attrib["id"],
                bandwidth=(
                    int(element.attrib["bandwidth"]) if "bandwidth" in element.attrib else None
                ),
            )
            for element in root.iter()
            if element.tag.rsplit("}", maxsplit=1)[-1] == "Representation"
            and "id" in element.attrib
        )
        if not representations:
            raise DASHManifestError("MPEG-DASH MPD has no representations")
        return DASHManifest(
            is_live=root.attrib.get("type") == "dynamic", representations=representations
        )
