# Changelog

## v0.1.4 — 2026-08-18

### Fixed

- Added the missing frozen `desktop_entrypoint.py` main guard so PyInstaller executes the application instead of importing the script and returning success without startup.
- Preserved full startup-journal path identity and retained sanitized traceback, runtime, VLC, and phase details for failures before Qt initialization.

### Added

- Added a VLC-independent Qt diagnostic mode and a forensic OneDir/OneFile/debug build and execution matrix.
- Added blocking exact-candidate acceptance across C-drive, spaces, Unicode, Downloads-like, TEMP, arbitrary-CWD, normal-PATH, sanitized-PATH, first-launch, and second-launch cases.

### Release validation

- The new production candidate was built and accepted on a Windows Server 2025 runner through all 48 exact-artifact executions, with `VLC_READY`, `MAIN_WINDOW_SHOWN`, `APPLICATION_READY`, exit code 0, checksum, PE metadata, and artifact identity verified.

## v0.1.3 — 2026-08-17

### Fixed

- Made Windows VLC discovery deterministic for source execution through an explicit `VLC_RUNTIME_DIR`, while frozen execution continues to resolve its bundled runtime relative to `_MEIPASS` and does not rely on the current working directory.
- Replaced stale installed-metadata version precedence with the authoritative `pyproject.toml` version source so startup diagnostics and runtime metadata identify the actual checkout or bundle.

### Added

- Added a redacted, atomic startup journal with ordered checkpoints through `VLC_READY`, `MAIN_WINDOW_SHOWN`, and `APPLICATION_READY`; startup failures retain the last successful stage and sanitized loader/dependency error details.
- Added blocking generated-EXE and exact-published-artifact checks for startup diagnostics, VLC readiness, and `MAIN_WINDOW_SHOWN` under arbitrary-CWD and sanitized-PATH cases.

### Release validation

- Promotes the confirmed source-mode loader fix and diagnostic evidence path through the existing CodeQL, Linux, Windows, native VLC, PyInstaller, packaged-VLC, Qt smoke, sanitized-PATH, artifact, and published-artifact acceptance workflows.

## v0.1.2 — 2026-08-17

### Fixed

- Canonicalized local M3U line endings to LF so LF and CRLF playlists behave identically across platforms; added regression coverage for both forms.

### Release validation

- Promotes the validated Windows portable-release candidate through the existing CodeQL, Linux, Windows, native VLC, PyInstaller, packaged-VLC, Qt smoke, sanitized-PATH, artifact, and acceptance workflows.

## Zero-touch Windows release pipeline — 2026-08-17

### Added

- Added a metadata-driven release-body template and generator that derive the version, tag, commit, workflow URL, artifact filename, SHA256, size, build timestamp, toolchain versions, validation summary, and current project-status limitations during the tagged Windows workflow.
- Added blocking tag-to-application-version validation and packaged-runtime version resolution from the authoritative `pyproject.toml` metadata.
- Changed tagged release publication to consume the generated `dist/release/release-notes.md` through `softprops/action-gh-release@v3`, eliminating the previous manual post-publication notes augmentation path.

### Verification and limitations

- Deterministic tests cover dynamic substitution, version/tag consistency, artifact and checksum fields, limitation extraction, missing metadata failure, and rejection of stale hard-coded release data.
- Tagged workflow run `32019974720` published `v0.1.1` without manual release-note editing. The generated release body contains the current artifact filename, SHA256, commit, workflow, validation summary, build metadata, and project-status limitations. Windows presentation-test collection remains an environment limitation and is not silently re-enabled.

## Windows portable EXE pipeline — 2026-08-17

### Added

- Added a reproducible PyInstaller one-file Windows x64 build with pinned Python 3.13, PyInstaller 6.22.1, PySide6 6.11.1, `python-vlc` 3.0.21203, and VLC 3.0.23 runtime acquisition verified by SHA256.
- Added runtime-relative bundled-VLC discovery, explicit VLC DLL/plugin/lua/locale collection, safe `--smoke-test` and `--packaged-vlc-test` modes, artifact content auditing, automatic naming, `SHA256SUMS.txt`, GitHub artifact upload, and tag-triggered release publishing.
- Added a blocking Windows workflow that validates the actual generated executable in a sanitized `PATH` and Unicode temporary directory without requiring a system VLC installation.

### Fixed

- Fixed M3U and XMLTV local-source validation on Windows so drive-letter paths are not misclassified as URL schemes; local `file:///C:/...` URIs are normalized correctly.
- Made packaged-runtime path assertions separator-independent across POSIX and Windows test hosts.

### Verification and limitations

- Windows run `32013261624` passed the non-presentation tests, native VLC lifecycle, PyInstaller build, packaged-VLC smoke, Qt/application smoke, clean-environment validation, artifact audit, checksum generation, and artifact upload for commit `a7b57d5`.
- The generated artifact was `SamoTech-IPTV-Player-Windows-x64-build-a7b57d5.exe` with SHA256 `bb14aaa8bd2ea13d62d4a5bdac56ffc10ddd101b5906a2f584466b5d5a65c7ef`; tag-triggered release publication is configured but was not exercised by this non-tag run.
- Presentation test modules remain excluded from the Windows corpus because their collection causes a fatal Windows Qt access violation; this is documented as an environment limitation, not a weakened product assertion. Authorized-provider runtime acceptance, installer creation, ARM64 builds, and auto-update infrastructure remain out of scope.

See [WINDOWS_PORTABLE_EXE_BUILD_AUDIT.md](docs/historical/WINDOWS_PORTABLE_EXE_BUILD_AUDIT.md) for the complete evidence matrix.

## Real-world IPTV reliability validation — 2026-08-17

### Added

- Extended synthetic compatibility fixtures for realistic Xtream, MAG/Stalker, Extended M3U, XMLTV, and local subtitle variations, including Unicode/Arabic, sparse/null/malformed metadata, duplicates, escaped M3U attributes, EPG overlaps, subtitle encodings, and large local catalogues.
- Added deterministic reliability evidence for provider workflows, failure handling, artwork/provider invalidation, stale-result protection, playback identity, local subtitles, and 10K/50K/100K catalogue behavior.

### Fixed

- Fixed the Extended M3U `#EXTINF` separator scanner so backslash-escaped quotes inside quoted attributes no longer prevent valid display-name parsing. Strict URL, title, stream, and channel-number validation remains unchanged.

### Preserved boundaries and limitations

- Provider architecture, MAG/Xtream/M3U ownership, shared libVLC, qasync, PlayerPort, and existing Live EOF recovery were preserved.
- The final classification is **C — PARTIAL**. Populated authorized-provider acceptance, Windows-native VLC validation, real-provider subtitle interoperability, and native VLC track-shape validation remain blocked or not executed. Catch-up/archive remains unimplemented without a verified provider-neutral contract.
- See [REAL_WORLD_IPTV_RELIABILITY_VALIDATION.md](docs/historical/REAL_WORLD_IPTV_RELIABILITY_VALIDATION.md) for the single authoritative evidence record.

## Commercial provider and subtitle hardening — 2026-08-17

### Added

- Added credential-free Provider Health snapshots with distinct connected, unauthenticated, unknown, and error classifications derived from declared capabilities and adapter authentication state without loading full catalogues or exposing credentials.
- Added non-blocking post-save provider onboarding: Save → safe health check → capability summary → Ready/error feedback, while preserving provider registration, qasync, and Qt task ownership.
- Added unified local search filters for All, Live, Movies, Series, and Episodes. Episode title, plot, season, and episode number are searchable over explicitly loaded canonical records without adding network requests.
- Added local SRT, ASS, SSA, and VTT subtitle validation and loading through `PlayerPort` into libVLC, subtitle-slave removal, bounded subtitle-delay controls, and media/session-safe invalidation across provider, media, and playback switches.
- Added focused provider-health, local-subtitle, VLC adapter, search-filter, episode-search, stale-session, and native PlayerShell regression evidence.

### Preserved boundaries and limitations

- Provider adapters, MAG, Xtream, M3U, shared libVLC ownership, qasync, typed playback resolution, and bounded Live EOF recovery remain preserved.
- The UI never imports libVLC, constructs provider URLs, reads credentials, uploads subtitle files, or persists subtitle contents. Subtitle controls are capability-gated by the injected player contract.
- Catch-up/archive remains not implemented because no current provider advertises a verified capability. Windows-native VLC validation, real populated-provider acceptance, and production subtitle runtime acceptance remain unexecuted in this Linux environment.

## Desktop UI/UX modernization — 2026-08-16

### Added

- Added token-driven cinematic dark/blue PySide6 theme primitives shared by the application stylesheet and desktop surfaces.
- Added a remembered collapsible `PlayerShell` sidebar, compact provider/status context, local global search over already-loaded Live/Movie/Series models, reusable Movie/Series content cards, and explicit loading/empty/error states.
- Added a presentation-only player overlay with idle visibility, status feedback, stop/play-pause controls, fullscreen, and supported `Space`/`F` shortcuts.
- Expanded deterministic native Qt probe coverage for navigation, local search grouping, card-view configuration, overlay behavior, and player delegation.

### Preserved boundaries

- Existing provider adapters, application use cases, credential handling, `PlayerPort`, shared libVLC ownership, qasync runtime, and desktop composition contracts remain unchanged.
- Global search is local-only and does not add provider requests; the presentation layer does not construct provider URLs or access secrets.

## Xtream synthetic compatibility hardening — 2026-08-16

- Hardened Xtream Movie and Series translation for realistic optional-field variation: malformed year, rating, and artwork values are ignored safely while required identity remains validated; Series year and rating are now translated when present.
- Added deterministic synthetic Xtream fixtures covering numeric/string IDs, default and varied extensions, missing/null optional fields, malformed optional metadata, empty seasons and episode lists, unknown fields, and unexpected detail shapes.
- Real-provider validation remains separate: the previously authorized account authenticated but exposed zero VOD and Series records, so populated real Movie/Series playback remains unvalidated.

## Xtream VOD and Series hardening — 2026-08-16

- Hardened the existing Xtream Movie and Series → Season → Episode flow with presentation-side provider/content/action freshness checks around asynchronous detail, discovery, and playback completions.
- Stale movie, season, episode, provider-switched, navigated-away, duplicate, and disposed-owner completions no longer mutate current non-live UI state or initiate stale playback.
- Added deterministic offscreen Qt/async coverage for stale VOD detail, stale Series seasons, stale episode lists, provider switching, rapid episode selection, and safe playback outcomes.
- Updated architecture documentation to distinguish repository-observed Xtream behavior from provider-dependent compatibility assumptions. No live, MAG, M3U, VLC recovery, retry, decoder, qasync, or packaging behavior changed.
- Authorized real-Xtream runtime validation remains pending and is not claimed.

## Phase 2 playback contract — 2026-08-16

- Introduced the provider-neutral `PlaybackResource`, typed `TransportMetadata`, and ephemeral `ResolvedPlayback` contract.
- Updated Xtream, M3U, and existing MAG resolution boundaries to return resolved playback objects while retaining provider URL construction, authentication, and session state inside infrastructure.
- Updated the application player port and VLC adapter to consume resolved playback; supported typed headers, user-agent, and referrer metadata are translated into media options without changing existing caching, decoder, retry, recording, recovery, or lifecycle behavior.
- Preserved Phase 1 stale-result protection and provider-switch invalidation, and added deterministic transport metadata and validation coverage.
- No new M3U capabilities, MAG functionality, authentication behavior, persistence schema, or Phase 3+ work was introduced.

## Unreleased

### Added

- Added end-to-end Xtream Codes non-live support through the existing provider, domain, application, desktop-composition, and Qt presentation boundaries. The Xtream adapter now loads Movie detail metadata, resolves opaque Movie and Episode playback resources through its existing authenticated client, loads Series seasons and episodes, and advertises the corresponding narrow runtime capabilities. `PlayerShell` now presents explicit Movie detail/play and Series → Season → Episode navigation, while all non-live playback uses the existing generation-safe `PlaybackTarget` path and shared `PlayerPort`/libVLC adapter. Opaque resource IDs use `stream_id|extension`; raw URLs remain adapter-local and are rejected from target contracts. MAG, M3U, Live playback behavior, VLC options, qasync lifecycle, provider timeouts, and provider configuration remain unchanged. Real Xtream-provider runtime validation is still pending.
- Added provider-free Windows native libVLC validation infrastructure: the existing Windows CI job installs the standard VLC runtime, runs a temporary-local-media lifecycle probe, and executes the deterministic Live EOF recovery suite. The new manual Windows EOF runtime procedure records only safe aggregate state and requires an authorized desktop/provider session; no real-provider CI test, secret, stream URL, or runtime-success claim was added.
- Added an adapter-local, generation- and session-safe Live-stream EOF recovery controller. Unexpected current-session `END`/`STOPPED` and a bounded buffering deadline can rebuild media only through the existing libVLC media-construction path. Recovery is capped at five attempts in 45 seconds with 1/2/4/8-second backoff and a five-second stable-playing reset; explicit stop, shutdown, pause, channel switch, and recording restart invalidate pending recovery. No provider, MAG, timeout, network-caching, hardware-decoding, qasync, PlayerShell, or libVLC option behavior changed. Native/libVLC/stream root cause remains unconfirmed.
- Added minimal Ubuntu CI provisioning for the real cross-platform PySide6 offscreen probes: the quality job installs only `libegl1`, validates `QtGui`/`QtWidgets` imports, and runs the native and 39,753-channel probes directly before coverage pytest. The probes remain required and assertions are unchanged.
- Added deterministic operation-scoped SQLite ownership. Favorites, history, provider metadata, theme preferences, and XMLTV bindings now commit or roll back and explicitly close every per-operation connection; a direct test schema-inspection connection is also closed. No shared connection, `check_same_thread` override, or qasync shutdown ordering change was introduced.
- Added safe MAG catalogue response-boundary diagnostics. Catalogue requests now report header arrival, complete-body aggregate timing, or incomplete-body aggregate progress without logging provider URLs, device identities, tokens, cookies, authorization headers, credentials, response bodies, or stream URLs. The instrumentation preserves the existing timeout, retries, request contracts, authentication, response acceptance, and lifecycle behavior.
- Added provider-neutral non-live contracts for Movie stream resolution, Series-detail season/episode discovery, and Episode stream resolution. The new resolver-service seams require both the narrow interface and an explicit runtime capability declaration; no M3U, MAG/Stalker, or Xtream adapter advertises or executes them yet.
- Added canonical provider-scoped Season identity, a safe provider-scoped Episode DTO/request boundary, bounded generation-safe discovery use cases, Movie/Episode target factories, fake-backed stale-result tests, raw-URL rejection tests, and synthetic discovery-scale coverage. This is an architecture increment only: Movie/Episode playback and non-live navigation UI remain unimplemented.
- Added separate `stalker_gui_compatibility` and `stalker_helper_compatibility` MAG profiles based on distinct secondary Stalker client references. The profiles preserve the observed endpoint paths, query differences, MAC-cookie formats, headers, timezones, live pagination starts, strict token validation, private cookie mapping, live genre/ordered-list loading, and channel-command stream-link construction. The random-token/prehash retry and fabricated device identities remain deliberately excluded because they are not verified by authorized portal evidence.
- Added a source-derived local classic Stalker/Ministra middleware laboratory that drives the real MAG adapter through handshake, TTL, token transport, genres, page-one/page-two ordered lists, channel translation, and `create_link` using deterministic local data. Official Infomir configuration research and open-source middleware inspection are documented separately; production portal compatibility remains unresolved.
- Added an optional explicit `mag_model` identity field for model-dependent client headers. The runtime leaves the model **UNKNOWN** when absent and never fabricates a MAG250/MAG254 identity. Official login/password, authorization-key, new-STB, and allowed-model policies remain documented provider-side possibilities rather than silently selected client modes.
- Added an evidence-backed MAG authentication state machine with explicit `mac_only`, `mac_plus_login`, and `authorization_key` modes, optional `get_profile`, form-encoded POST `do_auth`, explicit serial/device/signature fields, safe policy classifications, and a fixed T01–T06 differential request lab. The authorized real portal returned HTTP 404 for every new variation, so production authentication remains unresolved.

### Verification

- Added deterministic Xtream API-client, domain-translator, adapter, Movie-detail use-case, unified Movie/Episode playback-target, desktop-composition, and native offscreen PlayerShell coverage. The Qt probe now exercises Movie detail/play activation and a complete Series → Season → Episode selection flow using fakes only. Full offscreen pytest, Black, Ruff, `mypy src`, `git diff --check`, and a sensitive-marker diff scan pass; the suite retains only four existing non-fatal `aiohttp` bare-handler deprecation warnings.
- Executed the blocking Windows CI validation job successfully: standard VLC installed, the provider-free native lifecycle probe reported binding/instance/lifecycle success, and the focused deterministic Live EOF recovery suite completed successfully. This does not claim an authorized provider or real desktop runtime result.
- Added a Windows-only native libVLC lifecycle probe that imports the binding, creates/releases the native instance/player/media, requires per-generation local-media `PLAYING`/`END` and replacement `PLAYING`/`STOPPED` callbacks, reports `BUFFERING` only when native VLC emits it, validates media replacement, and prints safe aggregate diagnostics. Linux intentionally reports `SKIP reason=windows_required`; native Windows CI and authorized real IPTV runtime results remain pending.
- Added deterministic fake-backed recovery coverage for unexpected EOF/STOPPED, buffering deadline, explicit stop/shutdown/pause/recording-restart protection, channel switch, stale generations, concurrent signals, capped backoff, stability reset, retry exhaustion, non-live exclusion, and preserved immediate initial-play fallback. Focused adapter tests, full offscreen pytest, Black, Ruff, `mypy src`, and `git diff --check` pass.
- Added direct offscreen Qt import/probe CI gates and deterministic SQLite close/rollback regression coverage across every SQLite repository. The affected repository and composition tests pass with `ResourceWarning` treated as an error.
- Added deterministic MAG transport coverage for response-header metadata, complete multi-chunk JSON collection, zero-byte and partial-body timeout classification, payload and pre-response network errors, unchanged three-attempt retry accounting, malformed/empty response rejection, POST URL routing, and diagnostic redaction.
- Added adapter-to-fixture coverage for strict handshake gating, headers, Referer, private cookies, explicit model-dependent helper headers, token TTL, live genres, helper page-one ordered-list channels, command-based stream resolution, source-derived middleware behavior, resource cleanup, and sensitive-value redaction. The authorized real-portal runs, including the new no-model helper revalidation, completed without a token-bearing handshake; real MAG authentication and playback remain **UNRESOLVED**.


This file records concise historical delivery milestones. It is **not** the current support matrix or roadmap; read [PROJECT_STATUS.md](PROJECT_STATUS.md) for verified current capability status and [ROADMAP.md](ROADMAP.md) for delivery direction.

## [Unreleased]

### Added

- MAG authentication failure-path cleanup: the legacy provider now closes its owned aiohttp session and connector when bounded discovery or session authentication fails, while successful sessions remain reusable until provider close. Deterministic local coverage proves failure cleanup, repeated failures, provider shutdown, and no premature successful-session closure. A supplied Windows run of this revision recorded session closure after two discovery failures and contained no unclosed-session or unclosed-connector warning.
- Bounded MAG/Stalker handshake discovery for exactly four approved endpoint families, safe response classification, deterministic priority, and a conditional `prehash=false` retry only after a JSON response without a token. Discovery retains no token or raw payload and selected profiles are reused by the established session, catalogue, and stream boundaries.
- Deterministic local fixture coverage for bounded candidate construction, 401/403/404/empty/malformed/missing-token classifications, valid handshake selection, safe result redaction, conditional prehash behavior, and selected-endpoint reuse.
- Deterministic MAG/Stalker compatibility lab using a local aiohttp protocol fixture and the real adapter → legacy provider → HTTP/session/parser boundaries.
- Explicit legacy and opt-in Stalker-query handshake profiles based on repository and secondary implementation evidence.
- Fixture coverage for successful authentication, empty/malformed/status failures, missing tokens, TTL, session expiration/re-authentication, unsupported categories, channels, and stream resolution.
- MAG protocol, firmware/middleware compatibility, and test-lab documentation.
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

- Passing local MAG fixtures is simulation only and does not establish compatibility with a production portal or any MAG hardware family.
- The supplied real MAG portal remains unresolved at authentication unless an authorized discovery run yields a structurally valid token-bearing handshake. On the supplied Windows run, libVLC and the GUI started and the fixed discovery sequence ran twice; both attempts stopped safely before stream resolution. MAG playback remains blocked before stream resolution.
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

## Xtream diagnostics and resilience — 2026-08-13

- Invalid optional Xtream channel logo metadata is now warned and ignored at the domain translation boundary; valid channel records continue translating, while required channel identity and stream validation remain strict.
- Added `IPTV_DEBUG=1` development diagnostics with timed provider stages, safe exception tracebacks, record/category summaries, and credential-bearing URL redaction. Normal users retain concise behavior with `IPTV_DEBUG=0`.

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


## Xtream/MAG normalized provider audit — 2026-08-16

- Added provider-neutral `ProviderSession`, `AccountInfo`, `ServerInfo`, and `CatchupEvent` domain records with secret-free validation and exports.
- Added explicit `AccountInfoProvider` and `ServerInfoProvider` application ports, runtime capability values, provider-resolution methods, and Xtream implementation through `user_info`/`server_info` response mappings.
- Added deterministic API-client, translator, adapter, resolver, security-boundary, malformed-response, and sparse-metadata tests. Existing MAG capability declarations remain unchanged because the current MAG facade and authorized fixtures do not establish VOD, Series, or executable catch-up contracts.
- Preserved the existing `PlayerPort`/libVLC boundary, provider credentials/keyring ownership, playback URL construction boundary, generation-safe workflows, and presentation architecture.
- Full offscreen pytest with coverage, native Qt/player probe, Ruff, Black, mypy, and `git diff --check` pass.


## KiddaC technology adaptation — 2026-08-16

- Added `KIDDAC_TECHNOLOGY_GAP_MATRIX.md` and source-linked adaptation records comparing SamoTech with EStalker and XStreamity without cloning Enigma2 code, UI, global state, filesystem assumptions, or decoder APIs.
- Added an opt-in local Movie/Series catalogue sort selector for provider order, title A–Z, newest-first, and rating ordering. The default preserves provider response order and all choices operate only on already-loaded canonical content.
- Added deterministic native Qt coverage for the new sort behavior and retained large-catalogue identity/performance coverage through 100,000 content records.
- Documented rejected legacy behavior, external-source licenses, catch-up limitations, MAG production evidence limits, and the unchanged PlayerPort/libVLC and Live EOF recovery boundaries.


## Product-hardening reference study — 2026-08-16

- Completed a source-level workflow trace and gap audit against public EStalker and XStreamity engineering patterns while preserving SamoTech’s provider, qasync, PySide6, SQLite/keyring, `ResolvedPlayback`, `PlayerPort`, shared libVLC, and Live-only recovery boundaries.
- Added sanitized Xtream API-client coverage distinguishing expired authentication from an active account with zero VOD/Series content, plus a safe unusual `webm` container-extension fixture.
- Added README acknowledgment linking [EStalker](https://github.com/kiddac/EStalker) and [XStreamity](https://github.com/kiddac/XStreamity). The projects were studied as public technical references only; no external source code was copied, no dependency was added, and no permission, endorsement, partnership, ownership, or license claim was inferred where GitHub metadata exposed no SPDX license or tracked root license file.
- Reconciled stale product-gap claims with the verified Xtream Movie/Episode and Series discovery paths, bounded Favorites/History library workflows, local search/category/sort behavior, and the remaining authorized-runtime and contract-gated limitations.
- Focused verification passed with 75 tests, the native PlayerShell probe, and the 100,000-record local catalogue performance probe. The full repository quality gate remains the final pre-commit verification.

## 2026-08-16 — Commercial Xtream VOD/Series hardening

### Added

- Optional Movie metadata for duration, genre, director, cast, country, release date, backdrop, and container format, with safe malformed-value fallback.
- Optional Series genre, backdrop, season count, and episode count propagation.
- Inline PlayerShell detail presentation for Movie, Series, and Episode identity and metadata, including artwork availability and human-readable duration.
- Deterministic translator, application DTO, and native Qt assertions for rich fixtures.

### Preserved and verified

- Existing provider abstractions, qasync generation/stale-result protection, local search/category/sort, SQLite Favorites/History, `ResolvedPlayback`/`PlayerPort`, shared libVLC lifecycle, Live-only EOF recovery, MAG, and M3U behavior.

### Explicitly not claimed

- Populated authorized real-provider VOD/Series runtime validation, remote artwork loading/cache, resume reconstruction, catch-up, and audio/subtitle track APIs.


## Advanced Xtream VOD/Series increment — 2026-08-16

### Added

- Added provider-supplied Movie and Series optional metadata propagation for detail panels, local search, category filtering, and sorting.
- Added a provider-scoped `ArtworkPort` and bounded shared-session artwork loader with URL safety, response-size limits, TTL/LRU eviction, provider invalidation, cancellation preservation, and deterministic placeholders.
- Added provider identity to Favorites with legacy SQLite migration and idempotent same-provider duplicate prevention.
- Added Movie and Series Favorite actions and provider-aware Favorites library summaries.
- Added explicit non-live loading, empty, unavailable, and metadata-search states.

### Preserved or deferred by contract

- Preserved Live EOF recovery, MAG, M3U, qasync ownership, stale-result protection, shared libVLC ownership, and typed `PlayerPort` handoff.
- Deferred watched-state inference, true resume, progress updates, catch-up, track selection, external metadata enrichment, and populated real-provider acceptance because the current contracts or evidence do not support safe claims.

### Verification

The full offscreen pytest suite, native PlayerShell probe, native 100,000-record performance probe, Ruff, Black, mypy, and `git diff --check` passed. The native VLC lifecycle probe was executed at its repository path and reported `SKIP reason=windows_required`; no Windows runtime claim is made from the Linux environment.


## Real Xtream acceptance and production hardening — 2026-08-16

The acceptance phase reviewed the exact Xtream action/field compatibility surface, controlled authorized-account availability, response robustness, bounded artwork failures/cancellation, provider-scoped Favorites migration/restart/corruption behavior, History/resume constraints, PlayerPort capabilities, commercial native UX, concurrency, security, and performance.

The phase added deterministic Favorites acceptance coverage for restart persistence, duplicate database rows, and corrupt-database error handling, plus artwork cancellation coverage. The performance probe now includes exact 10K and 50K checkpoints in addition to the existing 100K coverage. No production architecture change was justified by the measurements.

Populated real-provider acceptance remains **BLOCKED BY EVIDENCE** because no authorized populated account was available and the prior authorized session returned zero VOD/Series records. Windows validation remains **NOT EXECUTED** on Linux; the native VLC lifecycle probe explicitly reports `SKIP reason=windows_required`. Live EOF recovery, MAG, M3U, qasync, shared libVLC, and stale-result behavior remain unchanged.

## 2026-08-16 — Player 2 commercial playback

Player 2 adds a typed player capability model, explicit playback state machine, evidence-backed position/duration/seek/volume/mute operations, native audio and subtitle track enumeration and selection, aspect ratio, restart, and safe error handling over the existing libVLC adapter. The PySide6 PlayerShell now exposes mode-aware commercial controls, Live-safe seek suppression, progress labels, relative seek actions, volume/mute, native track menus, fullscreen overlay behavior, keyboard shortcuts, diagnostics, and qasync-owned control tasks.

History now stores provider-scoped identity, optional lifecycle timestamps, runtime progress, watched percentage, completion, and safely migrated SQLite columns. Movie and Episode resume restoration is provider-scoped and limited to incomplete records; Live history is never resumed or completed. Deterministic tests, native offscreen PlayerShell and performance probes, full source quality gates, and security review were executed in Linux. Windows native VLC and populated authorized-provider acceptance remain not executed.


## 2026-08-16 — Player 3 commercial hardening

Player 3 hardens the existing Player 2 implementation without rewriting provider adapters, MAG, M3U, Live EOF recovery, qasync, shared libVLC ownership, or the `PlaybackTarget` → `ResolvedPlayback` → `PlayerPort` path. Xtream translation now skips malformed and duplicate live/VOD/Series/Season/Episode records individually; MAG declares live categories; EPG description/category metadata is preserved with a bounded output; PlayerShell exposes provider-scoped adjacent-episode controls and typed backend-state labels; History validates timestamp ordering; and user-facing failures use a stable credential-free taxonomy.

### Verification

Focused regression tests, isolated Qt concurrency/lifecycle invocations, the native PlayerShell probe, the 39,753-live/5,000-content performance probe across required catalogue sizes through 100,000, the changed-file security scan, Ruff/Black/mypy checks, and `git diff --check` were executed for the Player 3 delivery. The combined offscreen Qt invocation remains unsuitable because cross-module Qt teardown can segfault; compatible Qt-heavy modules are therefore reported from isolated runs rather than falsely treated as a product defect.

### Explicitly not claimed

Catch-up/archive remains not implemented because no current provider advertises `ProviderCapability.CATCHUP`. Populated authorized Xtream acceptance was not executed. MAG VOD/Series/Episodes remain not executed because the authorized portal contract is unproven. Windows-native validation was not executed on Linux; the VLC lifecycle probe reports `SKIP reason=windows_required`. Credentials, tokens, cookies, resolved URLs, and raw provider payloads were not added to source, tests, documentation, reports, or commits.
