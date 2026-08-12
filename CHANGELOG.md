# Changelog

This file records concise historical delivery milestones. It is **not** the current support matrix or roadmap; read [PROJECT_STATUS.md](PROJECT_STATUS.md) for verified current capability status and [ROADMAP.md](ROADMAP.md) for delivery direction.

## [Unreleased]

### Added

- Production desktop composition root that initializes non-secret SQLite repositories, restores safe provider metadata, registers M3U/Xtream/MAG provider constructors, constructs existing provider services/use cases, loads the persisted theme, and injects one shared libVLC player into the Qt shell.
- Supported `samotech-iptv` console command and `python -m samotech_iptv` module entry point that invoke production composition, run the qasync desktop loop, report generic startup failures, and close the shared HTTP resource after the window loop exits.
- Fake-backed integration coverage for safe metadata restoration, factory registration, persisted-theme loading, shared-player wiring, lifecycle cleanup, and entry-point error safety.
- M3U `PlaybackProvider` support that resolves a selected canonical channel from the current parsed playlist through the registered-player path when its stream is HTTP(S).
- Adapter and resolver-to-player M3U playback coverage, including generic failures that do not expose unknown channel IDs or unsupported transport URLs.
- Generic desktop pause, resume, and stop controls: dedicated application use cases delegate only through `PlayerPort`; the Qt Playback menu schedules them on qasync and emits safe generic success/failure feedback.
- Focused playback-control application, presentation, bootstrap, and composition coverage, including proof that the controls share the existing libVLC player rather than constructing a second backend.
- Registered-provider lifecycle management with application update/removal use cases, type-aware Qt edit dialogs, safe provider selection, list refresh after removal, and generic presentation outcomes.
- Credential-preserving profile edits: optional blank Xtream/MAG/M3U secret fields are never prefilled and retain existing keyring values; removal deletes persisted non-secret metadata, the associated keyring credential when present, and the runtime registry record.
- Focused lifecycle and presentation coverage for metadata deletion, credential cleanup, blank-field preservation, registry synchronization, safe status copy, and production composition wiring.
- Registered Xtream **live-category** discovery through the existing registry/factory path, typed `CategoryProvider`, canonical category translation, `LoadCategories` application use case, and a minimal Qt browse dialog.
- Deterministic resolver and registry-to-factory-to-adapter integration coverage for live-category discovery, plus presentation tests for provider selection, rendered categories, empty state, and generic failure feedback.

### Changed

- Desktop bootstrap can accept a caller-owned shared player, preventing production composition from constructing multiple libVLC adapters.
- Removed the obsolete preconfigured-provider playback path from the Qt main-window constructor; registered-provider playback is the production desktop flow.

### Documentation

- Rebaselined product purpose, architecture terminology, support matrices, roadmap, gap analysis, security model, and direct-to-main development guidance against the repository’s verified implementation.
- Recorded the delivered composition-root, lifecycle, M3U registered-playback, generic desktop playback-control, secure provider lifecycle, and browse-only registered live-category discovery increments; prioritized XMLTV source binding and refresh next.

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
