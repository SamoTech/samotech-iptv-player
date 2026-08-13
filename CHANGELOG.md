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
- Registered-provider local XMLTV source binding with immutable canonical source/mapping records, SQLite persistence, atomic replacement, and cleanup during provider removal.
- Local-path and local-`file:` XMLTV loading with manual bounded refresh through the existing `defusedxml` parser, canonical EPG translation, generic safe failures, and a PySide6 configuration/dialog surface that renders title/time rows only.
- Focused domain, repository, local loader/service, application, provider-lifecycle, dialog, bootstrap, and composition tests for XMLTV binding; remote/tokenized sources, cached programme persistence, and scheduled refresh remain explicitly excluded.
- Favorites library view with safe listing, empty state, refresh, generic error feedback, and single-record removal.
- History library view with recent listing, duration, persisted playback-position display, recency, refresh, generic error feedback, and confirmation-protected clear-all.
- Production composition wiring and Library menu actions for the existing SQLite-backed user-library use cases.

### Scope limits

- History per-record deletion, replay, resume, provider reconstruction, and stream reconstruction remain out of scope.

## Runtime QA fix — 2026-08-13

- Fixed the P0/P1 provider-management defect where Add M3U, Add Xtream, and Add MAG/Stalker dialogs rendered input fields without usable Save/Cancel actions.
- Save now validates required fields, delegates to the existing secure registration/application boundary, closes only after successful registration, and reports generic failures. Cancel closes without invoking persistence. Secret and identity inputs remain transient and are cleared after submission.
- Added regression coverage for all currently exposed provider-add dialogs. This fix does not constitute verification of real IPTV playback.

## Runtime QA fix — HTTP session lifecycle — 2026-08-13

- Fixed the confirmed `HttpSession is not open — call open() first` failure affecting remote M3U channel loading and registered-provider category loading.
- The composed desktop application now owns the shared HTTP client lifecycle explicitly: the qasync runtime opens it after the Qt-aware event loop is available and closes it during shutdown. Provider adapters continue to use the existing HTTP abstraction; no UI-level or per-request `open()` calls were added.
- Added deterministic local HTTP regression coverage for closed-session failure, open/use/close behavior, and real M3U channel loading through the provider boundary. VLC stale-plugin-cache messages remain a separate warning and were not changed. Real IPTV playback remains unverified.

## M3U diagnostics — 2026-08-13

- Added stage-specific M3U diagnostics for source resolution, credential retrieval, HTTP/URL handling, content retrieval, parser input, and channel translation. Diagnostics include exception type and traceback while retaining the generic `Unable to load channels` presentation message.
- M3U remote-source failures now return controlled redacted errors without query tokens or userinfo. Added regression coverage for secure registered-source restoration and HTTP failure redaction. Real Windows M3U channel loading remains pending manual acceptance; no unrelated feature work was started.

## Real M3U integration fix — 2026-08-13

- A real network diagnostic established that the supplied M3U endpoint returned HTTP 200 with a 5.16 MB `application/octet-stream` playlist and a valid `#EXTM3U` first chunk, but the default HTTP body-read timeout expired before the complete response was consumed.
- With an evidence-based extended per-request M3U timeout, the existing application path completed against the real server and produced 21,786 canonical channel entities. The real playlist also contained malformed optional `tvg-logo` values; the parser now ignores only invalid optional logos while retaining valid channels.
- The real Xtream adapter authenticated and loaded 187 live categories. Live-channel loading remains separately unverified because the existing adapter received an invalid stream URL from the provider response. Playback was not tested.

### Changed

- Desktop bootstrap can accept a caller-owned shared player, preventing production composition from constructing multiple libVLC adapters.
- Removed the obsolete preconfigured-provider playback path from the Qt main-window constructor; registered-provider playback is the production desktop flow.

### Documentation

- Rebaselined product purpose, architecture terminology, support matrices, roadmap, gap analysis, security model, and direct-to-main development guidance against the repository’s verified implementation.
- Recorded the delivered composition-root, lifecycle, M3U registered-playback, generic desktop playback-control, secure provider lifecycle, browse-only registered live-category discovery, and local XMLTV binding/manual-refresh increments; prioritized user-library views next.

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
