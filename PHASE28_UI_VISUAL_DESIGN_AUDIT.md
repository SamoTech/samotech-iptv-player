# Phase 28 UI/UX, Visual Design & Complete Menu Audit

## 1. Final Decision

**Decision B — verified UI improvement, preserve v0.1.6.** The audit confirmed and repaired two P1 discoverability gaps and two P2 exposure gaps without changing provider protocols, account/capability truth, media resolution, libVLC ownership, authentication, diagnostics contents, packaging configuration, or release metadata. A v0.1.7 release was neither required by the evidence nor explicitly authorized; v0.1.6 remains the public-testing release.

## 2. Scope and Method

The review followed the required sequence: read the current baseline; inventory every supported user-facing surface; audit hierarchy, navigation, menus, accessibility, controls, states, performance evidence, and public-feedback mappings; complete cross-role review and independent challenge; implement only approved capability-backed changes; run focused and full validation; inspect security and release boundaries; validate on Windows and hosted CI; and make the final decision from evidence.

## 3. Starting and Ending Repository State

| Item | Evidence |
|---|---|
| Starting HEAD/origin | `4ccea50fde480341d7896a03d3e1885459fcf0d5` / equal |
| Implementation commit | `ebdf3b016eeeeb938bf33b405c8654de46c5fdca` |
| Branch | `main` |
| Push result | Normal non-force push; `HEAD == origin/main` immediately after push |
| Release version | `0.1.6`, unchanged |
| Release/tag/assets | Untouched; no new tag or release created |

## 4. Protected-Boundary Review

No changed path was `README.md`, `pyproject.toml`, or `.github/workflows/*`. The current `README.md` digest was `b5fae9edbbe346864c76547744aef294040f865243d349d46c56f850fa5bcd25` at both initial `HEAD` and `origin/main`; it therefore predates this cycle and was not modified. This differs from the inherited historical digest value `d6310d733baae10823f9a84f2bb7ad157706930d993f4b26d78eb534d7da810d`; the discrepancy is documented, not repaired, because altering the README is forbidden.

## 5. Formal Role Assignment

The version-controlled engineering charter now includes **Interface & Visual Design Engineer**. The role owns visual hierarchy, typography, spacing, consistency, menus, navigation, dialogs, player controls, themes, accessibility, discoverability, and cross-role review, but cannot bypass the provider/media/playback/security boundaries.

## 6. Complete UI Inventory

`docs/evidence/PHASE28_UI_INVENTORY.json` records the audited MainWindow and PlayerShell windows; ten in-shell pages; provider, channel, EPG, library, diagnostics, settings, and import dialogs; all menu actions; player controls; keyboard shortcuts; states; and discoverability gaps. It is the machine-readable baseline for later UI work.

## 7. Visual Hierarchy, Typography, and Spacing

The established dark, player-first layout has a coherent hierarchy: compact navigation, page kickers/titles/subtitles, primary player surface, status feedback, media/detail areas, and explicit empty panels. Shared tokens and repeated controls provide adequate current consistency. No unmeasured palette, typography, or layout rewrite was approved. The theme engine already applies the persisted System/Light/Dark preference at desktop startup; PlayerShell's existing dark-oriented local styling should receive a future Windows visual review before any theme-token refactor.

## 8. Navigation and Home Flow

Home, Live TV, Movies, Series, Favorites, History, Search, EPG, Providers, and Settings remain capability-gated. Navigation still uses the current provider capabilities rather than invented server/account state. Full provider selection, catalogue loading, content switching, and stale-result protections remain in the existing presentation/application boundary.

## 9. Provider Setup and Smart Import

The highest-value P1 gap was confirmed: `Add IPTV Provider…` already existed and opened the supported combined Smart Import/manual flow, but normal menu navigation could not reach it. It is now the **first Providers-menu action**, preceding protocol-specific Xtream, M3U, and MAG/Stalker actions. The change exposes rather than reimplements provider configuration and makes no credential, protocol, duplicate, parsing, or authentication change.

## 10. Safe Active-Provider Selection

The active provider selector now uses a non-editable registered-provider list and the placeholder **Select provider**. The selector stores the provider ID in `itemData`; `_provider_id()` now returns only that data. The normal UI no longer advertises or accepts opaque manual provider-ID entry, while registered names and types remain human-readable. This preserves provider isolation and removes a direct discoverability/accessibility issue without changing the provider registry.

## 11. Menu Architecture

The Providers, Library, and Playback menus retain their established capabilities. The selected menu improvements are intentionally limited: Add IPTV Provider is now visible; **Playback Diagnostics…** exposes an existing safe panel; and Settings is a direct menu-bar action rather than a redundant one-item menu. No speculative Tools, Help, icon-library, or duplicate Fullscreen menu was added.

## 12. Settings Discoverability

Settings remains the existing direct PlayerShell settings page with the pre-existing dialog fallback for reduced/test shells. Replacing the one-action Settings menu with the existing direct action reduces unnecessary activation without changing persisted theme preference, storage, or settings scope.

## 13. Safe Playback Diagnostics

The new Playback-menu action calls the existing PlayerShell diagnostics entry point. The underlying report, sanitization, runtime data retrieval, ownership lifecycle, dialog, and error message are unchanged. The menu action provides a secondary discoverability path only; it does not add diagnostic collection or expose raw URLs, headers, credentials, tokens, cookies, or provider secrets.

## 14. Player Controls and Fullscreen

The audit retained the existing content-aware player controls. Live playback continues to disable VOD-only seeking/restart behavior; VOD/episodes retain seek, adjacent episode, volume, mute, audio-track, subtitle, aspect-ratio, retry, diagnostics, and fullscreen controls. Fullscreen remains available through the overlay and existing F/Escape keyboard behavior; no duplicate menu action was justified.

## 15. Icons and Media Assets

No new icon system, branding asset, external image, or randomly selected glyph dependency was introduced. Current textual labels and compact navigation glyphs remain appropriate for the established Qt presentation surface, avoiding a cosmetic-only dependency expansion.

## 16. Dialog and Window Management

Existing provider-entry, browse, EPG, library, diagnostics, and settings dialogs retain their ownership/parenting model. The implementation adds no unmanaged top-level dialog, windowing rewrite, or native VLC-surface change.

## 17. Accessibility and Keyboard Operation

Existing accessible names/tooltips and keyboard shortcuts remain intact. The native probe now verifies that the provider selector has accessible naming and is non-editable. The menu changes use native `QAction`s with descriptive labels. No accessibility regression was observed in the isolated presentation corpus.

## 18. Empty, Loading, Error, and Retry States

No-provider, provider-unavailable, no-channel, no-category, empty-search, unavailable-content, artwork-unavailable, playback-error/retry, EPG, and theme-feedback states were audited and retained. No raw transport/security detail was added to any user-facing state.

## 19. Large Playlist, EPG, and Responsiveness Evidence

No large-data or EPG behavior was changed. Existing deterministic 1k/5k/10k-plus evidence, models/delegates, explicit loading, local filter/sort/search, capability gating, and stale-request guards remain the only supported performance basis. No invented 50k/100k performance claim is made.

## 20. Public Feedback Mapping

Historical discoverability feedback maps directly to the combined provider entry, human-readable safe provider selection, direct Settings, and diagnostics menu changes. Provider-authentication/real-stream reports remain **external-evidence blocked**: they require a safe reproduction package containing timestamps, sanitized diagnostics, version, provider type, content class, and behavior—never credentials, private URLs, tokens, cookies, or MAC addresses.

## 21. Architecture and Provider/Media Boundary

Provider adapters, domain translation, registered provider IDs, resolved playback, `PlayerPort`, libVLC adapter, native Qt video surface, task ownership, request generations, and stale identity checks are unchanged. The implementation resides only in presentation menus/selector behavior and test fixtures.

## 22. Security and Privacy Analysis

The final diff contains no committed credentials, bearer headers, API keys, provider URLs, passwords, tokens, signed URLs, cookies, or MAC addresses. Bandit completed successfully, while existing diagnostics sanitization remains the source of truth. The new diagnostics action delegates to that existing safe path.

## 23. Implementation Files

| File | Change |
|---|---|
| `src/samotech_iptv/presentation/views/main_window.py` | Exposes existing Add IPTV Provider and diagnostics actions; makes Settings direct. |
| `src/samotech_iptv/presentation/player_shell.py` | Makes provider selector non-editable, removes text fallback, exposes existing diagnostics through a public presentation method. |
| `tests/test_presentation_main_window.py` | Verifies the revised Providers, Playback, and direct Settings action structure. |
| `tests/test_desktop_bootstrap.py` | Extends the Qt menu-bar double for native direct actions. |
| `tests/player_shell_native_probe.py` | Selects providers through registered item data and verifies non-editability while preserving async lifecycle behavior. |
| `tests/xtream_vod_series_concurrency_cases.py` | Uses the same safe provider selection in stale VOD/series concurrency cases. |
| `docs/evidence/*`, charter, `todo.md` | Records inventory, design review, formal role, and completion evidence. |

## 24. Focused Regression Evidence

| Gate | Result |
|---|---|
| `tests/test_presentation_main_window.py` | **4 passed** |
| Standalone `tests/player_shell_native_probe.py` | **PASS**, including provider selection, stale identity, retry, navigation, artwork, keyboard, and playback stale-result checks |
| `tests/xtream_vod_series_concurrency_cases.py` | **7 passed** |

## 25. Complete Local Test Evidence

The official non-presentation corpus completed with **902 passed, 72 existing aiohttp deprecation warnings, 10.73s**. The complete isolated Qt presentation corpus completed with `FAILED=0`, followed by the standalone native PlayerShell probe **PASS**. A first full-corpus attempt exposed an obsolete editable-selector test fixture in the nested Xtream concurrency probe; it was repaired to use the safe registered selection contract, the focused nested suite passed, and the complete corpus then passed. No test was deleted, skipped, weakened, or converted to a warning.

## 26. Static Quality and Local Security Gates

| Gate | Result |
|---|---|
| Ruff | PASS |
| Black | PASS; 362 files unchanged |
| mypy | PASS; 225 source files, no issues |
| Bandit high/medium scan | PASS; no reportable findings |
| `git diff --check` | PASS before commit |
| Credential-pattern diff scan | PASS |
| Release/version/workflow boundary scan | PASS; README, `pyproject.toml`, and workflow files unchanged |

## 27. Windows Portable Validation

GitHub Actions run [Windows Portable EXE #32362243678](https://github.com/SamoTech/samotech-iptv-player/actions/runs/32362243678) completed **successfully**. It passed checkout, version resolution, pinned official VLC acquisition and verification, Ruff, Black, mypy, Windows non-Qt pytest, native VLC lifecycle, one-file EXE build, packaged-VLC smoke, Qt/application diagnostics smoke, sanitized debug launcher, sanitized PATH/outside-repository validation, artifact audit, checksum, metadata, and portable artifact upload. The tagged-release job was correctly not run because this was not a tag/release build.

## 28. Hosted CI and CodeQL

General [CI #32362243614](https://github.com/SamoTech/samotech-iptv-player/actions/runs/32362243614) completed **successfully**. [CodeQL Security Scan #32362243854](https://github.com/SamoTech/samotech-iptv-player/actions/runs/32362243854) completed **successfully**. The Windows workflow reported a GitHub Actions Node 20 deprecation annotation for third-party action runtime migration; it did not affect execution and is external workflow maintenance, not a Phase 28 application defect.

## 29. Independent Final Audit

The Independent Auditor accepts the change set: each user-facing improvement exposes a pre-existing capability, the safe selector reduces opaque internal-ID entry, focused coverage proves the changed UI contract, and full local plus hosted validation shows no regression. The auditor rejects a broader visual rewrite, theme-token rewrite, icon-system replacement, new Help/Tools menu, provider authentication change, media-engine change, and release escalation as unsupported by present evidence.

## 30. Limitations, Blockers, and Intentionally Unchanged Items

There are no implementation blockers. External production-stream reports remain unreproduced without a safe user feedback package. Manual Windows visual screenshot review of theme interaction remains a deferred validation item; it is not evidence for a code change. Intentionally unchanged: v0.1.6 version/tag/assets, README, workflow permissions, provider protocols, provider credentials/storage, authentication, account/server dashboards, VLC options/lifecycle, media resolution, retry policy, EPG data, artwork logic, favorites/history, large-data architecture, release notes, and packaging configuration.

## 31. Final Status and Next Action

**Final status: PASS, with Decision B.** The verified commit is `ebdf3b016eeeeb938bf33b405c8654de46c5fdca`, pushed normally to `origin/main`; Windows Portable, CI, and CodeQL all passed. No release was created. The next action is to collect safe, reproducible real-user feedback before considering any provider/playback or broader visual-theme work.

---

**Evidence files:** [`PHASE28_UI_INVENTORY.json`](docs/evidence/PHASE28_UI_INVENTORY.json), [`PHASE28_UI_DESIGN_REVIEW.md`](docs/evidence/PHASE28_UI_DESIGN_REVIEW.md), and [`AI_ENGINEERING_TEAM_CHARTER.md`](docs/AI_ENGINEERING_TEAM_CHARTER.md).
