# Changelog

This file records concise historical delivery milestones. It is **not** the current support matrix or roadmap; read [PROJECT_STATUS.md](PROJECT_STATUS.md) for verified current capability status and [ROADMAP.md](ROADMAP.md) for delivery direction.

## [Unreleased]

### Documentation

- Rebaselined product purpose, architecture terminology, support matrices, roadmap, gap analysis, security model, and direct-to-main development guidance against the repository’s verified implementation.

## [0.1.0] — 2026-08-12

### Added

- Clean Architecture foundation with canonical IPTV domain records, provider capabilities, application use cases, and infrastructure adapters.
- Extended-M3U parser/source loading; stream transport/manifest classification; bounded HLS, MPEG-DASH, and XMLTV parser foundations.
- Capability-oriented M3U, Xtream Codes, and MAG/Stalker provider foundations with secure registration, non-secret metadata persistence, and OS-keyring credential ownership.
- Xtream live/VOD/series/category/short-EPG adapter methods and MAG/Stalker live/EPG/search/session/stream-resolution support.
- libVLC-only player adapter with Qt native video output and local MPEG transport-stream recording.
- PySide6/qasync desktop component foundation: provider entry/listing, live-channel browser/search/playback action, EPG grid, favorite insertion, history recording, recording controls, and persisted system/light/dark theme settings.
- Trusted explicitly selected local provider-plugin SDK with version/identity/namespace validation and transactional registration.

### Known scope limits at the baseline

- No production desktop composition root or executable application launcher exists yet.
- M3U registered stream resolution, full VOD/series desktop workflows, XMLTV source binding, comprehensive favorites/history UI, packaging, updates, telemetry, and Ministra runtime support remain incomplete or planned.

The baseline commit for this release state is `7896c9e5036d278b68ffc5e1cde35b8015415707` (`feat: add theme settings UI`).
