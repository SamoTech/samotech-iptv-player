# Xtream Real Acceptance and Production Hardening — Final Audit

**Date:** 2026-08-16
**Repository:** `SamoTech/samotech-iptv-player`
**Audit scope:** The authoritative real-Xtream acceptance and production-hardening specification attached to this task.
**Final classification:** **PARTIAL COMMERCIAL READINESS — SYNTHETIC/NATIVE ACCEPTANCE READY; POPULATED REAL-PROVIDER ACCEPTANCE BLOCKED BY EVIDENCE; WINDOWS ACCEPTANCE NOT EXECUTED.**

This report distinguishes `OBSERVED`, `TESTED SYNTHETICALLY`, `TESTED NATIVE`, `INFERRED`, `NOT EXECUTED`, and `BLOCKED BY EVIDENCE`. A synthetic or native pass is never presented as a real-provider pass.

## 1. Executive Summary

The repository was audited and hardened without architectural rewrite. The current phase did not repeat the prior commercial implementation; it verified the existing Xtream protocol boundary, added only deterministic acceptance coverage for Favorites persistence/corruption/duplicates and artwork cancellation, extended the existing performance probe with exact 10K and 50K checkpoints, reconciled documentation, and executed the complete quality-gate matrix.

The result is **ready for synthetic/native acceptance**. The populated real-provider acceptance milestone remains **blocked by evidence** because no authorized populated Xtream account was available in this environment. The previous authorized session authenticated but returned zero VOD and zero Series records. Windows acceptance is **not executed** because the environment is Linux; the Windows-only VLC probe correctly reports an explicit skip.

## 2. Initial Repository State

The read-only baseline fetched `origin/main`, verified the `main` branch and clean worktree, inspected the previous advanced audit, and traced current provider, translator, artwork, Favorites, History, PlayerPort, qasync, and presentation contracts. The inherited baseline already contained bounded provider-scoped artwork, Movie/Series detail UX, provider-scoped Favorites, local search/filter/sort, generation-safe non-live workflows, and deterministic native/performance probes.

The initial known blockers were populated real-provider evidence, Windows runtime evidence, true watched/resume semantics, catch-up, audio/subtitle tracks, and external metadata enrichment. No secrets, provider credentials, or authenticated URLs were added to the repository.

## 3. Ordered Todo List

The dependency-ordered Todo List was: establish the clean baseline; audit the Xtream action and field surface; attempt controlled authorized real validation only if credentials were available; verify response robustness; verify artwork, Favorites, and History boundaries; audit PlayerPort, Windows, UX, and security; run concurrency and performance matrices; revisit KiddaC references; reconcile documentation; run final gates; write this report; then commit and push normally.

The list was executed sequentially. The only evidenced fix was updating the performance test expectations after the intentionally required 10K/50K probe expansion.

## 4. Architecture Trace

The observed dependency direction remains `provider adapter → translator → canonical domain → application use cases/ports → ResolvedPlayback → PlayerPort → libVLC → PySide6`. Xtream credentials and provider-specific URL construction remain infrastructure-owned. Presentation does not construct provider URLs, access keyring secrets, or import libVLC directly.

The artwork loader reuses the shared asynchronous HTTP client through an application-owned `ArtworkPort`; it does not create a second uncontrolled session. qasync task ownership, generation checks, provider invalidation, SQLite persistence, keyring storage, and the shared libVLC instance remain intact. See [`ARCHITECTURE.md`](ARCHITECTURE.md) and [`PROJECT_STATUS.md`](PROJECT_STATUS.md).

## 5. Xtream Protocol Compatibility Matrix

The inspected API surface is summarized below. These are source-observed compatibility claims, not a guarantee that every portal implements every variation.

| Surface | Standard form observed | Accepted variation or fallback | Missing/malformed behavior | Classification |
|---|---|---|---|---|
| Base API | `/player_api.php` with `username`, `password`, optional `action` | Base path is normalized to scheme/host; parameters are URL-encoded | Invalid base URL or credential fails validation | IMPLEMENTED |
| Categories | `get_live_categories`, `get_vod_categories`, `get_series_categories` | String/integer-like IDs normalized to text | Non-list or non-object response raises safe provider error | IMPLEMENTED; provider-dependent payloads |
| VOD list | `get_vod_streams` | String/integer `stream_id`, sparse metadata, safe alphanumeric extensions | Required `stream_id`/`name` failure rejects; optional malformed values are ignored | IMPLEMENTED synthetically; real blocked |
| Series list | `get_series` | String/integer `series_id`, list-shaped artwork, explicit or derived counts | Required identity failure rejects; optional malformed metadata is ignored | IMPLEMENTED synthetically; real blocked |
| Movie detail | `get_vod_info&vod_id=` with `movie_data` and optional `info` | `movie_data` and `info` are merged | Missing/non-object detail or identity mismatch raises safe validation/provider error | IMPLEMENTED synthetically; real blocked |
| Series detail | `get_series_info&series_id=` with seasons and episodes | Episodes are keyed by string season number; optional nested `info` is read | Invalid seasons/episodes shape raises safe validation error | IMPLEMENTED synthetically; real blocked |
| Playback | `/live`, `/movie`, or `/series` path with opaque ID and extension | Missing VOD/episode extension defaults to `mp4`; live defaults to `ts`; `webm` remains safe | Non-alphanumeric extension or embedded playback delimiter rejects | IMPLEMENTED synthetically; real blocked |
| Artwork | Provider-supplied poster/backdrop URLs | Scalar or list-shaped values select the first usable string | Invalid URL is ignored and the record is retained; loader rejects unsafe URL/secret query | IMPLEMENTED provider-supplied; real blocked |
| Optional metadata | `year`, `rating`, `plot`, `duration_secs`, `genre`, `director`, `cast`, `country`, release-date aliases | Movie cast accepts `actors`; duration accepts `duration_seconds`; rating accepts `rating_5based` | Invalid optional values become `None`; valid records are not dropped | IMPLEMENTED synthetically |
| Unknown fields | Additional provider keys | Ignored | No raw payload leaks across the boundary | IMPLEMENTED |
| Duplicates | Repeated list/database records | Favorites are provider-scoped and duplicate-save safe; catalogue deduplication is not invented | Duplicate catalogue behavior remains provider-dependent; duplicate Favorites are retained only when pre-existing database rows already exist | PARTIAL / PROVIDER-DEPENDENT |

## 6. Real Provider Validation

A controlled availability check found no authorized populated Xtream account or credential-bearing runtime configuration in the current environment. No credential was reconstructed, printed, or committed. Therefore, no live request was attempted in this phase.

Prior authorized evidence, recorded in the inherited audit, showed authentication success but zero VOD and zero Series records. That is historical `OBSERVED` evidence, not a new populated run. VOD/Series counts, details, artwork, real playback, HTTP failure behavior, timeout behavior, provider switching, and shutdown against populated real content are therefore `BLOCKED BY EVIDENCE` or `NOT EXECUTED`.

## 7. Response Robustness

Synthetic response-variation tests cover string versus integer IDs, blank or missing extensions, unusual safe extensions, sparse optional metadata, duplicate/unordered categories, empty seasons/episodes, malformed optional years/ratings/posters, and invalid required nested shapes. The focused robustness suite passed.

The implementation ignores malformed optional metadata and artwork while rejecting malformed required identity or nested response structures. No speculative provider alias, server-side search contract, or silent record-dropping behavior was added.

## 8. Artwork Pipeline

The existing provider-scoped artwork system was verified rather than replaced. It uses the shared HTTP client, HTTP(S)-only URL policy, rejection of embedded credentials and secret query keys, a 4 MiB per-response limit, bounded 16 MiB cache capacity, entry limit, TTL, LRU eviction, failure non-caching, cancellation propagation, provider invalidation, native Qt decode/error placeholders, and stale-selection generation protection.

Synthetic tests cover URL safety, cache identity, LRU bounds, TTL, provider invalidation, failures, oversized payloads, and cancellation. Native PlayerShell evidence reports `artwork_preview_and_provider_invalidation=PASS`. Remote populated-provider artwork remains `NOT EXECUTED`.

## 9. Favorites

Favorites carry optional provider identity, migrate legacy SQLite schemas, prevent same-provider duplicate saves, allow identical item IDs across providers, persist across repository restart, and preserve the existing opaque delete workflow. Movie and Series actions are exposed through the existing SaveFavorite boundary; Episode Favorites remain outside the current allowed item-type contract.

New deterministic tests verify restart persistence, duplicate database rows are readable without identity collapse, and a corrupt SQLite database raises safe `StorageError`. Favorites are classified **IMPLEMENTED / PARTIAL** because Episode Favorites are deliberately deferred and real-provider UI acceptance was not executed.

## 10. History and Resume

History remains a playback-start record with `id`, `item_id`, `item_type`, `watched_at`, `duration_seconds`, and `position_seconds`. It has no provider identity, completion state, typed seek position, or replay/resume target. The current PlayerPort likewise does not expose current position, duration, completion, or seek.

The acceptance tests document the safe limitation: unknown duration and zero position must not be presented as genuine resume. True watched state, resume reconstruction, replay position, and completion marking are **DEFERRED / BLOCKED BY CONTRACT**. No fake resume behavior was implemented.

## 11. PlayerPort Capability Matrix

| Capability | Current contract | Evidence | Classification |
|---|---|---|---|
| Play, pause, resume, stop | Typed async methods | Source audit and tests | IMPLEMENTED |
| Recording start/stop | Typed async methods | Existing tests | IMPLEMENTED |
| Native output attachment | Typed method | Existing native/UI tests | IMPLEMENTED |
| Is playing/recording | Boolean properties | Source audit | IMPLEMENTED, limited |
| Seek/current position/duration/completion | No typed methods/properties | Source audit | NOT SUPPORTED / DEFERRED |
| Audio/subtitle tracks | No typed methods | Source audit | NOT SUPPORTED / DEFERRED |
| Volume/mute | No typed methods | Source audit | NOT SUPPORTED / DEFERRED |
| Fullscreen | Window/presentation behavior, not PlayerPort | Native probe | IMPLEMENTED as presentation behavior |

No UI direct-libVLC path or second player backend exists.

## 12. Windows Native Validation

The current environment is Linux and has no Windows runtime bridge. The native VLC lifecycle probe was executed and returned `native_vlc_lifecycle=SKIP reason=windows_required` with exit status zero. This is correctly classified **NOT EXECUTED**, not PASS. Windows acceptance remains a required external action on a supported Windows machine.

## 13. Movie UX

Movie detail UX is implemented through the existing PlayerShell and canonical DTOs. The detail surface presents identity, category, year, rating, genre, duration, format, director, cast, country, release date, plot, artwork availability, and a Movie Favorite action. The UI is generation-safe and uses the existing provider-neutral playback handoff.

Synthetic/native evidence covers rich metadata, malformed optional metadata, selection, local search, Favorite action timing, stale provider results, and selection-without-playback. Populated-provider Movie detail/playback remains blocked or not executed.

## 14. Series, Season, and Episode UX

Series detail presents canonical metadata and navigates safely through Series → Season → Episode. Season and episode structures preserve provider-scoped identity, support empty valid collections, and reject malformed required nested shapes. Episode detail exposes safe title/plot/duration information and does not falsely expose Episode Favorites or resume.

Native evidence covers capability navigation, Series detail, Episode detail, stale provider transitions, stale search, and playback handoff. Real populated Series acceptance remains blocked by evidence.

## 15. Search

Local search operates over already-loaded canonical snapshots and covers title plus safe canonical metadata fields. It issues no additional provider query for Movie/Series local search and does not access credentials. The native probe and performance matrix verify common, rare, no-match, and clear-search behavior, including Movie and Series content.

Provider-side live search remains a separate existing capability. Populated real-provider search was not executed.

## 16. Sort

The local opt-in sort selector preserves provider order by default and supports title, year, and rating over the loaded canonical DTO snapshot after filtering. It does not issue network requests or alter provider contracts. Synthetic/native and performance evidence passed. Real-provider ordering behavior was not executed.

## 17. Category and Filter

Category selectors use canonical provider category IDs and filter loaded snapshots locally. Empty categories, no-match results, and cleared filters are represented explicitly. The implementation does not claim hidden/adult-content policy, server-side filtering, or a parental-control contract.

Synthetic/native and performance evidence passed. Provider-specific category behavior remains provider-dependent and real populated counts were unavailable.

## 18. Playback and Resolution

Movie and Episode targets resolve through the provider adapter into `ResolvedPlayback`, then cross the existing `PlayerPort` boundary to libVLC. Series is a non-playable container. The UI does not construct Xtream URLs or pass raw provider DTOs to the player.

Synthetic resolver and stale-result tests passed. Real populated Movie/Episode URL resolution and libVLC playback were not executed. Live EOF recovery, MAG, M3U, and shared VLC recovery behavior were not changed.

## 19. Concurrency and Stale Protection

The concurrency matrix passed 50 tests covering Movie A→B, Series A→B, Season/Episode stale transitions, provider switching, rapid selection, back/close cancellation, artwork invalidation, playback stale results, shutdown, and task ownership. Generation checks prevent stale provider/content/action completions from mutating UI or playback.

This evidence is `TESTED SYNTHETICALLY` and `TESTED NATIVE` where applicable; no claim is made for a populated live portal.

## 20. Performance

The exact performance probe passed at 10K, 50K, and 100K records for channels, Movies, and Series. It verified model replacement, first/middle/last identity, selection, category filtering, common search, no-match search, and clear-search behavior.

| Dataset | Movie replacement / category / search | Series replacement / category / search |
|---|---:|---:|
| 10K | 1.021 / 1.154 / 9.166 ms | 1.098 / 1.234 / 9.368 ms |
| 50K | 8.088 / 6.709 / 46.342 ms | 7.130 / 7.301 / 45.586 ms |
| 100K | 11.953 / 14.778 / 92.500 ms | 11.135 / 13.811 / 92.837 ms |

These are deterministic local synthetic measurements, not provider network timings. The single failure found during the first full gate was a stale expected checkpoint list; updating the test expectation fixed it without production changes.

## 21. Security

The security review found no credential values or credential-bearing URLs in the changed files. The sensitive-marker scan matched only legitimate field names and negative-test strings such as `password` and `token` in URL-policy tests. Keyring storage, generic diagnostics, ephemeral resolved playback, provider-scoped artwork, and safe persistence boundaries remain intact.

The application does not persist provider passwords, session tokens, cookies, raw stream URLs, or resolved playback URLs. No new authentication mechanism, external enrichment, or uncontrolled cache was introduced.

## 22. Test and Quality Gate Results

The final corrected gate matrix passed in full.

| Gate | Result | Evidence |
|---|---|---|
| Full offscreen pytest + coverage | PASS | 8,417 statements; 2,221 missed; 74% total coverage |
| Native PlayerShell probe | PASS | Artwork, stale protection, navigation, search, keyboard, and playback assertions passed |
| Performance probe | PASS | Exact 10K/50K/100K checkpoints passed |
| Concurrency matrix | PASS | 50 focused tests passed |
| Native VLC lifecycle | SKIP | `windows_required` on Linux; not claimed as Windows pass |
| Ruff | PASS | All checks passed |
| Black | PASS | Check passed |
| mypy | PASS | No issues in 210 source files |
| `git diff --check` | PASS | No whitespace errors |
| Sensitive-marker scan | PASS | No credential-bearing values or URLs |

## 23. Documentation Changes

The following documents were reconciled with the current acceptance evidence: [`README.md`](README.md), [`ARCHITECTURE.md`](ARCHITECTURE.md), [`PROJECT_STATUS.md`](PROJECT_STATUS.md), [`PRODUCT_GAP_ANALYSIS.md`](PRODUCT_GAP_ANALYSIS.md), [`CHANGELOG.md`](CHANGELOG.md), and the report itself. The documentation records populated real-provider evidence as blocked, Windows as not executed, resume as contract-blocked/deferred, and the exact performance/concurrency evidence.

The existing KiddaC compatibility and adaptation records were reviewed. No new finding required changing their safe adaptation boundary.

## 24. KiddaC Technology Usage Boundary

EStalker and XStreamity remain technical references only. No Enigma2 UI, global playlist state, service references, decoder APIs, provider-specific legacy URL construction, credential persistence, or source code was copied. SamoTech’s typed provider capabilities, canonical DTOs, PySide6 UI, qasync ownership, SQLite/keyring split, `ResolvedPlayback`, shared libVLC player, bounded artwork cache, and stale-generation protection remain authoritative.

The references support engineering comparison only; they do not provide evidence for real SamoTech provider acceptance.

## 25. Files Changed

The intentional changed files are:

| Group | Files |
|---|---|
| Documentation | `README.md`, `ARCHITECTURE.md`, `PROJECT_STATUS.md`, `PRODUCT_GAP_ANALYSIS.md`, `CHANGELOG.md`, `XTREAM_REAL_ACCEPTANCE_AND_PRODUCTION_HARDENING_FINAL_AUDIT.md` |
| Tests | `tests/test_infra_artwork_loader.py`, `tests/test_infra_sqlite_favorite_repository.py`, `tests/player_shell_performance_probe.py`, `tests/test_presentation_01_player_shell_performance.py` |

No production source file changed in this acceptance phase. The prior advanced production implementation is preserved.

## 26. Blockers

The primary blocker is **populated authorized real-provider evidence**. No authorized populated account was available in the current environment, and the prior authorized session returned zero VOD and Series records. Therefore, real counts, details, artwork, playback, timeout, HTTP-error, provider-switch, and shutdown acceptance against populated content remain blocked or not executed.

The second blocker is **Windows runtime availability**. The current environment is Linux, so the Windows lifecycle probe remains an explicit skip.

## 27. Deferred Items

True watched/resume and replay position remain deferred because History and PlayerPort lack provider-scoped completion and typed seek/progress capabilities. Audio/subtitle track selection, volume/mute, catch-up/timeshift, external TMDB-style enrichment, remote XMLTV caching, server-side VOD/Series search, hidden/adult-content policy, Episode Favorites, and non-Xtream VOD/Series adapters remain deferred or provider-dependent.

No fake implementation was added for any of these items.

## 28. Remaining Actions

On an authorized populated Xtream account, execute aggregate-only validation for authentication, category/list counts, Movie and Series detail, artwork, Movie/Episode resolution, playback, provider switching, malformed responses, timeout, HTTP errors, cancellation, rapid selection, and shutdown. Run the Windows native VLC lifecycle and PlayerShell acceptance suite on a supported Windows environment. Record only sanitized outcomes, never credentials, tokens, cookies, raw payloads, or credential-bearing URLs.

If true resume or track selection becomes a product requirement, first extend the typed domain/application/player contracts and design a migration; do not infer state from the current start-history record.

## 29. Final Readiness Classification

| Area | Classification | Evidence |
|---|---|---|
| Xtream protocol boundary | IMPLEMENTED | Source audit, translator/API tests, compatibility matrix |
| Response tolerance | IMPLEMENTED | Synthetic variation and focused tests |
| Provider-scoped artwork | IMPLEMENTED / PARTIAL | Synthetic/native bounded loader and UI evidence; real artwork not executed |
| Movie/Series/Season/Episode UX | IMPLEMENTED / PARTIAL | Synthetic/native UI evidence; populated provider not executed |
| Favorites | IMPLEMENTED / PARTIAL | SQLite migration/scope/restart/corruption/duplicate tests; Episode Favorites deferred |
| History/resume | PARTIAL / DEFERRED | Safe playback-start history only; no typed resume capability |
| Search/sort/filter | IMPLEMENTED locally | Native and performance evidence; provider-side real search not executed |
| Playback | PARTIAL | Synthetic resolver/player handoff; populated real playback not executed |
| Concurrency/shutdown | IMPLEMENTED synthetically/native | 50-test matrix and native stale-protection probe |
| Performance | IMPLEMENTED synthetically | Exact 10K/50K/100K measurements |
| Windows | NOT EXECUTED | Linux environment; explicit probe skip |
| Real populated provider | BLOCKED BY EVIDENCE | No populated authorized account; prior count zero |

Overall: **PARTIAL COMMERCIAL READINESS**.

## 30. Git Commit and Push Evidence

The final logical commits were created and pushed normally to `origin/main` without force-push or history rewrite:

| Commit | Subject | Scope |
|---|---|---|
| `afaed43` | `test: verify real xtream acceptance matrix` | Artwork cancellation, Favorites restart/duplicate/corruption acceptance, and exact 10K/50K/100K performance checkpoints |
| `22e5692` | `docs: record real xtream acceptance evidence` | Final audit report plus README, architecture, status, gap, and changelog reconciliation |

No production source change was justified in this acceptance phase; therefore no artificial empty `feat:` commit was created. The previous advanced production implementation remains preserved in `6abc6cc` and its ancestors. The push was a normal fast-forward to `origin/main`.

## 31. Final Repository State

After the normal push, `git rev-parse HEAD` and `git rev-parse origin/main` both returned `22e5692de00a6f9c8697615a1cb148d07dd30e23`. `git status --short` returned no entries. The transient `uv.lock` was removed. The report, intentional tests, and reconciled documentation are committed; the worktree is clean and synchronized.

## 32. Evidence Classification and Audit Conclusion

`OBSERVED`: repository source contracts, current branch/worktree, native probe output, explicit Linux/Windows skip, security scan output, and prior authorized zero-content result as recorded in the inherited report. `TESTED SYNTHETICALLY`: API/translator variations, artwork failures/cancellation/cache behavior, Favorites persistence/corruption/duplicates, History limitation, concurrency, and performance datasets. `TESTED NATIVE`: PlayerShell Qt probe and offscreen interaction assertions. `INFERRED`: provider compatibility beyond the inspected response forms and any behavior not exercised by an authorized populated account. `NOT EXECUTED`: populated real-provider workflow and Windows runtime. `BLOCKED BY EVIDENCE`: populated VOD/Series acceptance and real playback because no populated authorized account was available; true resume is also blocked by typed contracts.

The specification was executed without architectural rewrite, unsupported provider behavior, fake resume, or prohibited changes to Live EOF recovery, MAG, M3U, shared libVLC ownership, or qasync task ownership. The repository is ready for the final commit/push phase, but not for an unqualified populated real-provider or Windows acceptance claim.

### References

1. [SamoTech architecture](ARCHITECTURE.md)
2. [SamoTech current project status](PROJECT_STATUS.md)
3. [SamoTech product gap analysis](PRODUCT_GAP_ANALYSIS.md)
4. [SamoTech KiddaC compatibility matrix](docs/KIDDAC_COMPATIBILITY_MATRIX.md)
5. [EStalker reference repository](https://github.com/kiddac/EStalker/tree/master/EStalker/usr/lib/enigma2/python/Plugins/Extensions/EStalker)
6. [XStreamity reference repository](https://github.com/kiddac/XStreamity/tree/master/XStreamity/usr/lib/enigma2/python/Plugins/Extensions/XStreamity)
