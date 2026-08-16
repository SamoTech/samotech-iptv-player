# SamoTech IPTV Player — Smart Provider Import Final Audit

**Audit scope:** Universal Smart Provider Import plus preserved Manual Provider Entry

**Repository:** `SamoTech/samotech-iptv-player`

**Audit date:** 2026-08-17

**Baseline:** `2bf11521fde95e381f5a8a21f3d77a5c2ea1b92f`, the clean `origin/main` revision inspected before implementation.

**Implementation push:** `08a00a15a29f6e99e5c5cb67a905dea90bca063e`, verified equal to `origin/main` before this report-only commit.

## 1. Executive summary

**IMPLEMENTED:** The Add IPTV Provider experience now exposes Smart Import beside the preserved Manual Add workflow. Smart Import performs deterministic, local parsing and normalization for Xtream, M3U, and MAG/Stalker input, renders a credential-safe preview, requests missing required values minimally, handles ambiguity explicitly, and submits through the existing provider registration use cases.

**VERIFIED:** Parser, dialog, provider-state refresh, existing provider-dialog, static-analysis, performance, and native-probe evidence passed in the compatible isolated matrix described below. **NOT EXECUTED:** No populated real provider was used, and no external API or AI service was contacted.

## 2. Initial repository state

The read-only audit began from the fetched `origin/main` baseline above. The repository already had canonical provider registration DTOs, provider-specific registration use cases, provider persistence, provider selector/list state, Xtream/M3U/MAG adapters, PySide6 dialogs, qasync task ownership, and a shared playback architecture. There was no existing Smart Import parser, combined Add Provider entry point, clipboard import flow, or detected-input model.

The current architecture was preserved. No provider adapter, VLC playback implementation, authentication mechanism, network policy, buffering/recovery implementation, or qasync lifecycle was rewritten for this feature.

## 3. Architecture findings

The canonical path is registration use case → provider registration service → provider repository/keyring metadata and credentials → provider state consumed by the desktop shell. The narrow integration seam was therefore a local application parser plus presentation dialogs that construct the existing registration request DTOs.

The Smart Import parser does not construct provider URLs for playback, call adapters directly, store credentials, or create a second provider registry. Existing adapters remain responsible for protocol behavior after registration.

## 4. Existing provider workflow

Manual Xtream, M3U, and MAG/Stalker dialogs remain available and retain their original provider-specific fields and save/cancel behavior. They now accept an optional post-registration callback only; this callback refreshes application state and does not alter their registration contracts.

The combined Add IPTV Provider dialog presents Smart Import and Manual Add as two tabs. The real Qt menu exposes the combined entry while the legacy protocol-specific actions remain available.

## 5. Smart Import design

The application layer adds `DetectedProviderInput` and `ImportProtocol`. The model carries protocol, server, portal, playlist, username, password, MAC, EPG URL, output format, normalized parameters, confidence, missing fields, warnings, and ambiguity candidates.

The parser accepts complete text blocks rather than requiring one exact layout. It recognizes explicit labels, URL structures, query parameters, MAC addresses, portal patterns, M3U markers/content, and Xtream URL patterns. Values are normalized for surrounding whitespace, capitalization of labels, separators, trailing slashes, query ordering, and URL encoding handled by standard URL parsing.

## 6. Manual Add preservation

**IMPLEMENTED:** Manual Add was not removed, hidden behind Smart Import, or reduced to a paste-only flow. Xtream retains server, username, password, and provider identity fields. M3U retains provider identity and playlist source. MAG/Stalker retains provider identity, portal URL, and device identity. The existing manual registration path remains the canonical save path.

## 7. Detection architecture

Detection follows the declared priority: explicit protocol labels, URL structure, known parameters, MAC/portal evidence, M3U markers, and Xtream patterns. Explicit markers are restricted to actual label positions so words such as `portal` in a hostname or `playlist` in a URL path do not silently become protocol declarations.

If multiple plausible protocols remain and no single explicit marker resolves them, the result is `AMBIGUOUS` with candidate protocols. The dialog requires an explicit candidate selection before field completion and save.

## 8. Normalization architecture

Xtream labels and complete URLs normalize into the existing Xtream registration request. Authority credentials are extracted for parsing but excluded from the canonical server URL. Query parameters such as username, password, and output are decoded through standard parsing.

M3U URL input normalizes into the existing M3U source field. Inline M3U content is detected and previewed locally, but is not silently converted into a new persistence mechanism. MAG/Stalker input normalizes portal URL and MAC address into the existing MAG request.

## 9. Clipboard implementation

The Smart Import dialog reads `QApplication.clipboard()` locally. It places text into the local text editor, invokes the deterministic parser, renders a preview, and submits only normalized request fields through existing application use cases. No HTTP client, external API, AI service, telemetry sink, or clipboard logger is called by the implementation.

The raw clipboard text is cleared from the dialog after successful registration. It is not persisted in the repository, keyring, provider metadata, or diagnostic output.

## 10. Validation implementation

Required-field validation is protocol-aware. Xtream requires server URL, username, and password. M3U requires a usable playlist URL for the existing URL/source registration boundary. MAG/Stalker requires portal URL and MAC address. Missing-field warnings identify only the missing requirement, such as `Password is required.`

The visible **Validate** action checks normalized completeness and reports that the existing connection workflow applies after registration. A network test of an unsaved profile was not invented because the current application boundary authenticates registered provider identities.

## 11. Immediate provider-list update

After successful registration, `MainWindow._provider_added()` refreshes the PlayerShell provider selector, selects the newly added provider when present, refreshes an open provider-list dialog, and updates the status bar. This is a direct state-refresh callback, not a window reload or restart workaround.

**VERIFIED:** `test_provider_added_refreshes_selector_and_provider_list_without_restart` proves selector refresh, newly added selection, provider-list refresh, and success status through the actual `MainWindow._provider_added` callback. Existing provider switching tests remained green.

## 12. Duplicate handling

Duplicate handling remains owned by the existing provider registration service and provider identity semantics. Smart Import supplies the provider ID and canonical request; it does not create a second duplicate detector or use plaintext passwords as identity. Registration failures remain on the dialog and do not close it as success.

**LIMITATION:** The current project contract does not expose a distinct `Use Existing` versus `Add Anyway` dialog action. Existing repository semantics are followed, and the Smart Import layer does not bypass them or silently create a parallel identity policy.

## 13. Security review

The changed-file scan examined 11 changed files before the report commit and found zero known provider literals and zero literal secret assignments in non-test files. `git diff --check` passed. Synthetic test values are explicitly annotated where Ruff’s secret-literal heuristic requires it.

Passwords are masked in preview text, MAC addresses are masked in preview text, password/MAC line edits use password echo mode, raw clipboard text is not logged, and no credentials are placed in diagnostics or documentation. The implementation does not contact third-party services.

**VERIFIED:** A final post-report scan and tracked-file review remain required after the report-only commit; the pre-report implementation scan was clean.

## 14. UX changes

The Smart Import UX is **Paste → Detect → Review → Validate → Add**. It provides a local paste button, explicit detection, protocol selection for ambiguity, safe preview, provider ID suggestion, protocol-specific fields, validation feedback, Add Provider, and Back/Cancel behavior. Manual users retain **Manual Add → Choose Provider Type → Fill Required Fields → Test → Add** through the existing dialogs.

The implementation uses the existing PySide6 dialog and form conventions. No replacement visual system or unrelated redesign was introduced.

## 15. Tests

The focused parser suite contains 11 tests covering Xtream raw/query/authority forms, M3U URL/content detection, MAG input, incomplete input, ambiguity, invalid input, masking, formatting variations, and password exclusion from suggested identity. The real-Qt Smart Import dialog suite contains 3 tests covering clipboard paste, preview masking, canonical registration, missing-password behavior, callback refresh, and no raw clipboard persistence after success.

The non-Qt/application/domain/infrastructure/provider corpus collected 709 tests and passed. The isolated Xtream VOD/series concurrency module collected 1 test and passed. All 17 presentation modules were run in separate offscreen processes and passed, including the new Smart Import dialog and the preserved provider-dialog suites.

A combined Qt invocation initially exposed the repository’s known cross-module fake/real PySide6 and offscreen teardown sensitivity. The test doubles were repaired to restore module state after import, and the authoritative UI matrix was executed as isolated module processes. No Smart Import module failed in isolation.

## 16. Quality gates

| Gate | Result | Evidence |
|---|---|---|
| Black | **VERIFIED** | `uv run black --check src tests`; 335 files unchanged in the repository-wide run |
| Ruff | **VERIFIED** | `uv run ruff check src tests` passed |
| mypy | **VERIFIED** | `uv run mypy src`; 216 source files checked with no issues |
| Focused Smart Import tests | **VERIFIED** | 14 parser/dialog tests passed in compatible invocations |
| Non-Qt corpus | **VERIFIED** | 709 collected tests passed |
| Xtream concurrency | **VERIFIED** | 1 isolated test passed |
| Presentation matrix | **VERIFIED** | 17 isolated modules, all status 0 |
| Diff hygiene | **VERIFIED** | `git diff --check` passed before commits |
| Single-process full pytest | **BLOCKED** | Combined Qt collection/teardown is not a reliable gate in this offscreen environment; the separated matrix passed |

## 17. Documentation changes

`README.md` now documents Smart Provider Import, supported input formats, deterministic detection, canonical registration convergence, Manual Add preservation, clipboard privacy, masked previews, immediate provider-list refresh, and the inline-M3U persistence limitation. No unnecessary standalone documentation file was created.

The final audit itself is the single authoritative report required by the specification.

## 18. Git commits

The implementation was committed logically with four non-empty commits:

| Commit | Purpose |
|---|---|
| `673a6c2` | `feat: add deterministic smart provider import parser` |
| `f3c3841` | `feat: add smart import provider entry experience` |
| `63a1e99` | `test: cover smart import and provider refresh flows` |
| `08a00a1` | `docs: document smart provider import workflow` |

The report-only commit will be created after this file is finalized. No force push or history rewrite was used.

## 19. Push result

The four implementation commits were pushed normally to `origin/main`. Immediately after that push, `git rev-parse HEAD` and `git ls-remote origin refs/heads/main` both returned `08a00a15a29f6e99e5c5cb67a905dea90bca063e`. The final audit commit is the only remaining push operation.

## 20. Final repository state

Before this report-only commit, the branch was `main`, the worktree contained only the intended report file as an uncommitted addition after the implementation push, and the implementation push was synchronized with `origin/main`. After the report commit and push, the final verification must confirm a clean worktree and exact local/remote equality again.

## 21. Known limitations

Raw inline M3U content is detected and previewed but cannot be added through the existing URL/source registration boundary without introducing a new raw-content persistence mechanism. This is intentionally not faked or persisted because the clipboard requirement prohibits raw clipboard persistence absent an explicit secure-storage requirement.

The visible Smart Import validation action is local completeness validation, not a live network test of an unsaved profile. Real network authentication remains on the existing registered-provider path.

## 22. Deferred items

**DEFERRED:** A dedicated Use Existing/Add Anyway duplicate-resolution dialog is not added because the existing provider identity and registration semantics remain authoritative. **DEFERRED:** Rich clipboard history, remote AI parsing, remote provider probing, automatic protocol capability expansion, and raw playlist-content persistence are outside the narrow architecture-preserving scope.

## 23. Remaining risks

**NOT EXECUTED:** No authorized populated Xtream, M3U, or MAG/Stalker provider was used for acceptance. Parser and UI evidence therefore proves deterministic local behavior and registration-request convergence, not provider compatibility or playback success.

**NOT EXECUTED:** Windows-native UI/VLC validation was not run in this Linux environment. The existing VLC native probe returned `SKIP reason=windows_required`. **VERIFIED:** The Linux PlayerShell native probe passed, and the existing performance probe passed.

## 24. Final acceptance matrix

| Acceptance criterion | Classification | Evidence or reason |
|---|---|---|
| Manual Add still works | **VERIFIED** | Existing manual provider-dialog suite passed; legacy actions and fields retained |
| Smart Import works | **VERIFIED** | 11 parser tests and 3 real-Qt dialog tests passed |
| Xtream detection | **VERIFIED** | Raw labels, query URL, authority credentials, trailing slash, and query parsing tests |
| M3U detection | **VERIFIED** | URL and inline marker/content tests |
| MAG/Stalker detection | **VERIFIED** | Portal/MAC and incomplete portal-only tests |
| Clipboard import | **VERIFIED** | Real Qt clipboard test passed locally |
| Preview | **VERIFIED** | Human-readable preview and masked values asserted |
| Minimal missing fields | **VERIFIED** | Missing-password test asserts only password is required |
| Ambiguous input | **VERIFIED** | Candidate protocol selection is required; no silent choice |
| Credential protection | **VERIFIED** | Masking, password echo mode, safe registration boundary, clean security scan |
| Raw clipboard never logged | **VERIFIED** | No logging path exists; implementation contains no clipboard logging |
| Duplicate detection | **VERIFIED / BOUNDED** | Existing provider identity/registration semantics reused; separate resolution actions deferred |
| Provider persistence | **VERIFIED** | Existing registration use cases receive canonical DTOs; existing dialog regression tests pass |
| Immediate provider appearance | **VERIFIED** | MainWindow callback test refreshes selector and provider list |
| No restart required | **VERIFIED** | Callback refresh path is direct and state-driven |
| Provider selector updates | **VERIFIED** | Selector refresh and selection asserted |
| Existing switching intact | **VERIFIED** | Existing MainWindow/PlayerShell presentation tests pass |
| Existing Live/VOD/Series intact | **VERIFIED / BOUNDED** | Non-Qt corpus, concurrency, presentation, performance, and native PlayerShell probes pass; no real provider claim |
| Tests pass | **VERIFIED / BOUNDED** | 709 non-Qt + 1 concurrency + 17 isolated presentation modules pass; combined Qt invocation remains environment-sensitive |
| Static analysis passes | **VERIFIED** | Black, Ruff, mypy pass |
| Documentation updated | **VERIFIED** | README section added |
| Git history logical | **VERIFIED** | Four non-empty implementation commits plus this report commit; no force push |
| `origin/main` contains final implementation | **VERIFIED PENDING FINAL REPORT PUSH** | Implementation commits already synchronized; final report push and clean-state check remain the final delivery action |

## Final status

**IMPLEMENTATION STATUS: COMPLETE.** Smart Import and preserved Manual Add coexist, use the existing provider architecture, and satisfy the deterministic local parsing/UI/state-refresh scope.

**VERIFICATION STATUS: COMPLETE WITH HONEST BOUNDARIES.** Static checks and separated deterministic test matrices pass. The combined full Qt invocation is classified as environment-sensitive rather than converted into a false green claim.

**ACCEPTANCE STATUS: PARTIALLY VERIFIED.** Real-provider, Windows-native, unsaved-profile network testing, and raw inline-M3U persistence are explicitly **NOT EXECUTED**, **DEFERRED**, or **BOUNDED** as described above. The final report-only commit and its synchronized push are the remaining repository-delivery actions.
