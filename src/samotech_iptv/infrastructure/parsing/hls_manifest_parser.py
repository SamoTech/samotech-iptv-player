"""Parse HLS master and media manifests independently from IPTV M3U content playlists."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["HLSManifest", "HLSManifestError", "HLSManifestParser", "HLSVariant"]


class HLSManifestError(ValueError):
    """Raised when HLS manifest syntax cannot be represented safely."""


@dataclass(frozen=True)
class HLSVariant:
    """One advertised variant URI from an HLS master manifest."""

    uri: str
    bandwidth: int | None = None


@dataclass(frozen=True)
class HLSManifest:
    """A bounded representation of an HLS master or media playlist."""

    kind: str
    is_live: bool
    variants: tuple[HLSVariant, ...] = ()
    segments: tuple[str, ...] = ()


class HLSManifestParser:
    """Parse essential HLS tags without treating them as IPTV content records."""

    def parse(self, text: str) -> HLSManifest:
        """Return master variants or media segments from an ``#EXTM3U`` document."""
        lines = [line.strip() for line in text.lstrip("\ufeff").splitlines() if line.strip()]
        if not lines or lines[0] != "#EXTM3U":
            raise HLSManifestError("An HLS manifest must start with #EXTM3U")
        if any(line.startswith("#EXT-X-STREAM-INF") for line in lines):
            return self._master(lines)
        return self._media(lines)

    @staticmethod
    def _master(lines: list[str]) -> HLSManifest:
        variants: list[HLSVariant] = []
        for index, line in enumerate(lines):
            if not line.startswith("#EXT-X-STREAM-INF"):
                continue
            if index + 1 >= len(lines) or lines[index + 1].startswith("#"):
                raise HLSManifestError("HLS master variant has no following URI")
            attributes = line.partition(":")[2]
            bandwidth = next(
                (
                    int(value.split("=", 1)[1])
                    for value in attributes.split(",")
                    if value.startswith("BANDWIDTH=")
                ),
                None,
            )
            variants.append(HLSVariant(uri=lines[index + 1], bandwidth=bandwidth))
        if not variants:
            raise HLSManifestError("HLS master manifest has no variants")
        return HLSManifest(kind="master", is_live=True, variants=tuple(variants))

    @staticmethod
    def _media(lines: list[str]) -> HLSManifest:
        segments = tuple(line for line in lines if not line.startswith("#"))
        if not segments:
            raise HLSManifestError("HLS media manifest has no segments")
        return HLSManifest(kind="media", is_live="#EXT-X-ENDLIST" not in lines, segments=segments)
