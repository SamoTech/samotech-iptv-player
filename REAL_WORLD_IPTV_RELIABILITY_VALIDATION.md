# Real-World IPTV Reliability and Commercial Validation

**Repository:** SamoTech IPTV Player  
**Validation date:** 2026-08-17  
**Author:** Manus AI  
**Baseline:** `origin/main` at `9474efac0be010b0b3a33f5b35511f40cdbb1aab` before this increment

> **Final classification:** **C — PARTIAL**. The repository is strongly validated against deterministic synthetic provider data, realistic parser variations, local subtitle fixtures, stale-result scenarios, artwork failures, and large local catalogues. It is not classified as commercially ready because populated authorized-provider acceptance, Windows-native validation, and native VLC track-shape validation were not executable in the current Linux sandbox. MAG VOD/Series/Episode and catch-up/archive remain unsupported or unverified by the current contracts.

## 1. Executive Summary

This phase was a reliability and compatibility audit, not a feature-quantity exercise. The implementation was started from synchronized `origin/main`, the current provider/player architecture was mapped, public protocol references were researched without private-provider access, synthetic fixtures were expanded, deterministic workflows were executed, one reproducible M3U parser compatibility defect was fixed test-first, and all applicable quality gates were re-run.

The strongest evidence is synthetic and local: the broad non-presentation matrix contains **816 passing tests**, the isolated Qt matrix contains **64 passing tests**, the provider-focused matrix contains **174 passing tests**, and the workflow/state matrix contains **74 passing tests**. The Linux PlayerShell native probe passed, and the 10K/50K/100K performance probe completed successfully. These results establish a reliable implementation boundary, but they do not substitute for a populated authorized provider or a Windows desktop runtime.

## 2. Scope

The audit covered Xtream-compatible API response variation, MAG/Stalker session and live compatibility, Extended M3U parsing, XMLTV/EPG parsing, local subtitles, artwork, provider registration and selection, search, Series/Episode identity, playback resolution, stale-result protection, provider switching, error containment, security, performance, Qt/offscreen behavior, python-vlc symbol availability, and preserved Live EOF recovery.

The audit deliberately did not add catch-up/archive behavior, MAG VOD/Series/Episode behavior, remote subtitle downloading, remote XMLTV caching, telemetry, provider-specific URL construction in the UI, a second playback backend, or an architecture rewrite. Those areas are documented as unsupported, deferred, or blocked when the current contracts or environment do not establish them.

## 3. Initial Repository State

The initial forensic check fetched `origin/main` and recorded branch `main`, `HEAD` equal to `origin/main` at `9474efac0be010b0b3a33f5b35511f40cdbb1aab`, a clean worktree, no staged changes, no untracked files, and 455 tracked files. The current task then introduced only six modified tracked files; the environment-generated `uv.lock` was not retained for commit.

The baseline documentation, CI workflow, architecture, security policy, provider registry, provider metadata persistence, keyring boundary, runtime cache, provider resolution, PlayerShell, VLC adapter, artwork loader, existing compatibility labs, native probes, and previous final audit were inspected before implementation.

## 4. Architecture Audit

The verified workflow is:

```text
Provider input
  → protocol parsing and provider-specific normalization
  → non-secret metadata persistence plus secure credential storage
  → provider registry and runtime cache
  → provider selection and declared capability gating
  → catalogue retrieval
  → canonical domain records
  → application use cases and presentation-safe DTOs
  → Qt models, local search, and selection
  → provider-owned playback resolution
  → typed ResolvedPlayback
  → PlayerPort
  → one shared VLC adapter/libVLC player
```

The AST boundary scan reported `boundary_violations=0`. The presentation layer does not import libVLC or infrastructure credentials, application code does not perform direct HTTP/SQLite/keyring/libVLC I/O, and domain code remains framework independent. Provider-specific networking and URL construction remain in infrastructure. The player remains responsible for media creation, events, subtitle slaves, delay, recording, and Live recovery. Local subtitle contents remain file-local and are not persisted or logged.

## 5. Provider Architecture

`ProviderRegistrationService` validates and persists non-secret `InfraProviderMetadata`, while credential-bearing Xtream/MAG/M3U values remain in the secure credential boundary. `ProviderRuntimeCache` owns live adapter instances, reuses or invalidates them using non-secret metadata fingerprints, and closes them during shutdown. `ProviderResolutionService` requires both the correct provider port and a declared capability before resolving operations.

Xtream currently advertises authentication, account/server information, Live, categories, EPG, stream resolution, VOD, Series, Movie playback, Series details, Episode playback, and search. MAG currently advertises authentication, session, Live, categories, EPG, search, and Live stream resolution. M3U currently advertises Live, search, and HTTP(S) stream resolution. No adapter advertises a verified catch-up capability.

## 6. Xtream Research

The public `engenex/xtream-codes-api-v2` repository describes itself as a historical public Xtream API V2 reference and contains documentation rather than a current acceptance environment [1]. It was used only to cross-check action and response-shape concepts. SamoTech remains authoritative through its own request builder, adapter, canonical translator, capability declarations, and typed playback resources.

The synthetic audit therefore emphasized numeric-versus-string identifiers, null or missing optional fields, malformed optional artwork, duplicate identity, empty arrays, sparse nested Series detail, Arabic and Unicode text, default extensions, opaque playback resources, and error-shaped responses. No private account, provider payload, or copyrighted media was accessed.

## 7. MAG/Stalker Research

The public `crispy-stalker` documentation describes the Stalker/MAG ecosystem as a legacy query-string-based portal protocol with discovery, MAC-based authentication, session state, pagination, categories, channels, EPG, and stream resolution; it also exposes VOD and Series types in that separate client [2]. That breadth demonstrates ecosystem variation, not SamoTech support.

SamoTech’s MAG contract remains intentionally narrower. The deterministic labs exercise the existing handshake/session, discovery profiles, categories, Live channels, EPG, search, stream resolution, retry, expiry, empty/malformed/status failures, and safe redaction boundaries. MAG VOD, Series, Episode, and catch-up behavior are not inferred from external clients and remain unsupported or unverified.

## 8. M3U Research

A public M3U guide documents `#EXTM3U`, `#EXTINF`, the following media path/URL, and common IPTV attributes such as `tvg-id`, `tvg-name`, `tvg-logo`, and `group-title` [3]. These conventions informed safe synthetic fixtures for quoted and unquoted attributes, EPG identifiers, group labels, Unicode/Arabic names, catch-up annotations, duplicate titles, malformed lines, and escaped quotes.

The parser remains strict about the extended-M3U header, required title/stream pairing, stream URL validation, and numeric channel numbers. Catch-up metadata is parsed only as ignored metadata; it does not become an archive resolver. The one compatibility fix in this phase makes quoted-attribute scanning backslash-escape aware without weakening stream or identity validation.

## 9. XMLTV Research

The public XMLTV format reference describes `channel` and `programme` records, optional metadata, multilingual text, icons, categories, episode numbering, and broadcast timestamps [4]. The public XMLTV DTD further shows that programme timing is carried by `start`, `stop`, and `channel` attributes and that titles, descriptions, categories, icons, subtitles, and other metadata may be omitted or repeated [5].

The SamoTech XMLTV parser intentionally consumes a bounded safe subset: mapped programme identity, title, description, category, and validated timezone-aware timestamps. It uses defensive XML parsing and ignores unmapped channels. The fixture phase added multilingual Arabic/Unicode, icons, valid overlapping programmes, and malformed/empty cases. EPG loading remains separate from playback and cannot block media control through the tested service boundary.

## 10. KiddaC Technology Comparison

Public KiddaC XStreamity documentation describes an Enigma2 plugin for official Xtream Codes playlists and explicitly states that users provide their own playlist details [6]. Public KiddaC EStalker documentation describes an Enigma2 Ministra/Stalker player [7]. These projects were used as technology-pattern references for provider-driven catalogue navigation and portal-specific workflows only.

SamoTech implements the concepts differently through Clean Architecture, canonical domain records, capability-gated provider ports, OS-keyring credential ownership, SQLite non-secret metadata, qasync task ownership, PySide6, a shared libVLC adapter, and typed `ResolvedPlayback`/`PlayerPort` boundaries. No source code was copied. GitHub metadata returned no SPDX license metadata for XStreamity, EStalker, or the Xtream documentation repository; XMLTV returned GPL-2.0 metadata. XMLTV was used only as a DTD/format reference [8].

## 11. Synthetic Xtream Fixtures

The Xtream fixture set covers active and expired authentication, missing sections, malformed responses, empty lists, numeric and string IDs, null optional values, malformed optional years/ratings/artwork, missing identity, duplicate catalogue and nested records, sparse Series detail, empty seasons/episodes, default extensions, Unicode/Arabic titles, list-shaped poster/backdrop fields, and opaque Movie/Episode playback resources.

New evidence added this phase covers an Arabic Movie title with list-shaped artwork and a sparse Arabic Episode plot with an inferred safe display title. Existing fixtures cover Live, VOD, Series, categories, short EPG, authentication, server information, and adapter capabilities. Real populated Xtream VOD/Series acceptance remains blocked by evidence rather than promoted from synthetic results.

## 12. Synthetic MAG Fixtures

The MAG fixture set covers legacy and Stalker-query profiles, discovery, MAC identity handling, authentication/session state, token TTL, empty and malformed responses, 401/403/404 outcomes, missing tokens, session expiry and controlled re-authentication, categories, Live channels, EPG, stream resolution, retries, ordered pages, and safe token/cookie redaction.

This phase added an Arabic channel with a malformed optional logo, category, EPG identifier, and numeric-string channel number. The fixture was translated successfully while the malformed optional logo was ignored. No unsupported MAG VOD/Series/Episode fixture was promoted into a capability claim.

## 13. Synthetic M3U Fixtures

The M3U set covers standard/extended headers, `#EXTINF`, quoted and unquoted attributes, `tvg-id`, `tvg-logo`, `group-title`, channel numbers, Unicode/Arabic text, duplicate title identity, invalid logos, supported UDP classification, malformed/missing stream lines, unsupported FTP rejection, catch-up and catch-up-source annotations, and an ignored attribute containing an escaped quote.

The escaped-quote case initially failed deterministically in the separator scanner. After the minimum fix, the parser passed all 12 focused parser tests and the broader provider matrix. VOD-like, series-like, and catch-up-shaped entries remain metadata/parser observations; M3U’s current adapter contract remains Live/search/HTTP(S) resolution only. Multiple playlists are validated as separate source registrations rather than silently merged.

## 14. XMLTV Fixtures

The XMLTV set covers mapped and unmapped channels, minimum and richly populated programmes, start/stop timestamps with offsets and `Z`, titles, descriptions, categories, Arabic/Unicode text, icons, empty EPG, malformed timestamps, missing channel/title/timing, invalid schedule ordering, unsafe XML, document limits, entry limits, and valid overlapping programmes.

The new rich fixture passed with two Arabic/English programmes and retained the expected descriptions/categories/timestamps. The parser’s mapped-channel and bounded-entry behavior remains unchanged. Remote XMLTV sources, scheduled refresh, and catch-up linkage remain outside the current contract.

## 15. Subtitle Fixtures

The subtitle set covers SRT, ASS, SSA, and VTT; English, Arabic, mixed RTL/LTR, UTF-8, UTF-16-BOM legacy-looking text, malformed timestamps, duplicate cues, empty files, unsupported extensions, missing files, truncated timing, and the 16 MiB limit. No copyrighted subtitle file was used.

Existing PlayerPort/VLC adapter tests cover attachment, replacement-generation protection, slave removal, bounded delay, and media lifecycle. The local validator reads only a bounded probe, validates structure, returns metadata rather than contents, and never uploads, logs, persists, or executes subtitle text.

## 16. Compatibility Matrix

| Protocol | Workflow | Input variation | Expected behavior | Actual behavior | Status | Evidence | Risk | Fix required |
|---|---|---|---|---|---|---|---|---|
| Xtream | Authentication/account | active, expired, missing sections, malformed/empty response | typed safe state or controlled provider error | translator/client distinguishes active/expired and rejects missing required sections | **VERIFIED** | Xtream API/client/translator tests | Provider-specific response drift | No immediate fix |
| Xtream | Live/VOD/Series | numeric strings, nulls, duplicates, Unicode, malformed optional metadata | preserve valid identity; ignore malformed optional fields | valid records translate; malformed optional data is ignored; duplicates are skipped where nested identity requires it | **VERIFIED** | Xtream adapter and variation suites | Required-field drift | No immediate fix |
| Xtream | Episodes | sparse detail, duplicate IDs, Arabic plot, missing title | stable opaque identity and safe fallback title | stable `series:episode:id`, fallback title, optional plot retained | **VERIFIED** | realistic variation suite | Inconsistent provider nesting | No immediate fix |
| MAG | Handshake/session | profiles, empty/malformed/status failure, expiry | safe classification, cleanup, bounded re-auth | deterministic labs pass; production portal remains unresolved | **PARTIAL** | MAG compatibility/discovery labs | Portal policy variation | Production acceptance required |
| MAG | Live/EPG/search/playback | channels, categories, EPG, stream link | supported capability path | fixture adapter path passes | **VERIFIED / SYNTHETIC** | MAG adapter/lab suites | Real portal variability | Real portal acceptance required |
| MAG | VOD/Series/Episodes | external clients expose such types | do not infer support | not advertised or executed | **UNSUPPORTED** | capability set and audit | User expectation | Contract/provider evidence required |
| M3U | Import/parse | quoted/unquoted, Unicode, duplicates, malformed lines | strict structural validation with tolerant metadata | parser passes; invalid stream/title/header remains rejected | **VERIFIED** | 12 parser tests and adapter tests | Playlist dialect variation | No immediate fix |
| M3U | Escaped attributes | backslash-escaped quote in ignored attribute | find title separator without weakening validation | initial regression failed; minimal scanner fix passes | **VERIFIED / FIXED** | focused failing/re-passing test | Unusual quoting | Fixed |
| M3U | Catch-up/VOD-like entries | catch-up annotations and non-live-looking names | preserve metadata only unless contract exists | parsed as current live records; no archive resolver added | **PARTIAL / UNSUPPORTED** | synthetic parser fixture | Misleading user expectations | Contract decision required |
| XMLTV | EPG parse | mapped/unmapped, offsets, Arabic, icon, overlap, empty | bounded mapped guide records; no playback block | passes and ignores unmapped records | **VERIFIED** | XMLTV parser/service tests | Guide schema drift | No immediate fix |
| Artwork | Load/cache/switch | missing, invalid, unsafe, slow/fail, provider switch | placeholder/failure containment; no stale cross-provider image | loader tests and native probe pass | **VERIFIED** | artwork loader suite/native probe | Remote server behavior | No immediate fix |
| Subtitles | Local validation/attach | four formats, Arabic, UTF-16, malformed/large | safe local validation and capability-gated attachment | validation and VLC fake-backed contract pass | **VERIFIED / SYNTHETIC** | subtitle/VLC adapter suites | Native platform differences | Windows/runtime acceptance required |
| Playback | Live/VOD/Episode | synthetic resolved resources | correct provider/content identity and PlayerPort handoff | existing resolution and stale-result suites pass | **VERIFIED / SYNTHETIC** | workflow and concurrency suites | Real stream behavior | Authorized acceptance required |
| Provider switching | stale catalog/artwork/subtitles/playback | A completes after B selected | stale result cannot mutate current state | generation/session guards pass | **VERIFIED** | native PlayerShell and concurrency suites | Timing-sensitive regressions | No immediate fix |
| Errors | auth/network/server/empty/unsupported | status, timeout, malformed, empty | safe typed/user-friendly distinction | deterministic infrastructure and presentation tests pass | **PARTIAL** | failure labs and application tests | Provider-specific taxonomy | Real-provider acceptance required |

## 17. Provider Workflow Results

The supported synthetic provider workflow is validated through registration/application boundaries, adapter capability declarations, catalogue translation, local search, selection, and playback resolution. Xtream’s fake-backed adapter flow covers authentication, account/server metadata, Live, categories, EPG, VOD, Series, Movie detail/playback, Episode discovery/playback, and safe opaque resource handoff. M3U covers source parsing, Live catalogue/search, and HTTP(S) resolution. MAG covers the existing authentication/session/Live/EPG/search/stream contract through deterministic protocol labs.

The Qt desktop flow preserves non-blocking onboarding and provider selection without restart. No provider-specific UI URL construction or credential access was introduced. Real populated-provider results are not substituted for this synthetic workflow evidence.

## 18. Catalogue Results

The local PlayerShell performance probe exercised catalogue sizes through **100,000 records**. Model replacement, selection identity, category filtering, search, no-match search, and clear-search were measured without a reported UI freeze or identity corruption. The provider parser fixtures exercised empty, singleton, duplicate, sparse, malformed, and Unicode records.

The current evidence supports robust local catalogue behavior. It does not establish remote server pagination correctness for every provider dialect or memory behavior on an unbounded live server response; those remain provider-specific risks.

## 19. Search Results

Unified local search remains scoped to loaded canonical content. The native PlayerShell probe verifies Live, Movie, Series, and Episode result identity and explicit content-type filtering, including episode title/plot/season/episode-number matching. The state matrix also verifies registered-channel search, provider resolution, and stale search/provider behavior.

No additional provider request, remote search endpoint, or alternate URL path was added. Search is classified **IMPLEMENTED / VERIFIED within loaded-catalogue scope**.

## 20. Series/Episode Results

Xtream Series → Season → Episode discovery and playback remain generation-safe and provider-scoped. Synthetic fixtures cover missing and duplicate nested identity, sparse metadata, numeric/string values, empty seasons, Arabic plot text, fallback episode titles, and opaque playback resources. The native PlayerShell probe verifies episode detail/search behavior, while the concurrency suite verifies stale Series/Season/Episode completions cannot mutate current state.

MAG Series/Episode runtime acceptance is **UNSUPPORTED/NOT EXECUTED** because the current MAG adapter does not advertise those capabilities and no authorized contract establishes them.

## 21. Artwork Results

`BoundedArtworkLoader` validates safe non-secret HTTP(S) artwork URLs, bounds cache/payload behavior, invalidates by provider, preserves cancellation, and returns controlled failure/placeholder behavior. Existing tests cover unsafe query-bearing or userinfo URLs, invalid URLs, cache reuse, TTL, LRU eviction, provider invalidation, cancellation, oversized payloads, and failed fetches. The native PlayerShell probe also passes stale artwork/provider invalidation checks.

No artwork enrichment, external metadata service, or cache redesign was introduced. Artwork is classified **VERIFIED within existing bounded loader scope**.

## 22. Playback Results

Xtream Live, Movie, and Episode playback resources remain provider-owned and are handed to the shared `PlayerPort` as typed `ResolvedPlayback` values. M3U and MAG supported Live resolution paths remain covered by provider and adapter tests. Existing PlayerShell and VLC adapter tests verify media-generation/session safety, playback invalidation, replacement behavior, state transitions, and safe failure behavior.

The Linux environment did not establish actual media decoding against a populated provider. The native track-shape probe was blocked by missing native `libvlc_new`, and the Windows lifecycle gate correctly skipped on Linux. Playback is therefore **VERIFIED synthetically / PARTIAL operationally**.

## 23. Subtitle Results

Local SRT/ASS/SSA/VTT validation, capability gating, attachment, removal, bounded delay, replacement, session token invalidation, and media-generation checks pass through the existing application/player boundary. The installed python-vlc binding exposes `MediaPlayer.add_slave`, `Media.slaves_clear`, `video_get_spu_delay`, and `video_set_spu_delay`; the adapter uses those verified symbols rather than faking behavior.

Real-provider subtitle interoperability and Windows native subtitle attachment/removal/delay are **NOT EXECUTED**. The implementation does not fetch remote subtitles or persist subtitle contents.

## 24. Concurrency Results

The existing stale-result architecture was preserved and revalidated. The Qt/native probe and concurrency suites cover Provider A finishing after Provider B is selected, late Movie/Series/Episode results, rapid Episode reselection, stale artwork after provider switch, playback invalidation, disposed-shell/task-owner cleanup, and subtitle session invalidation after media/provider changes.

The isolated Qt matrix passed because each Qt-heavy module was executed in its own offscreen process. A combined offscreen invocation is not used as evidence due the repository’s known cross-module teardown instability; this is a test-environment limitation, not a product-failure claim.

## 25. Performance Results

| Record scale | Model replacement | Selection | Category filter | Search render | Clear/search behavior |
|---:|---:|---:|---:|---:|---|
| 10,000 | 1.116 ms | 0.064 ms | 1.336 ms | 9.099 ms | completed |
| 50,000 | 7.488 ms | 0.082 ms | 6.874 ms | 45.785 ms | completed |
| 100,000 | 11.742 ms | 0.085 ms | 14.234 ms | 91.776 ms | completed |

The probe reports successful selection identity and row counts at each scale. No performance fix was made because the measurements did not identify a proven defect requiring optimization. Artwork and provider switching were measured through bounded loader and stale-invalidation tests rather than a new speculative queue implementation.

## 26. Windows Validation

The Windows-only native VLC lifecycle probe was executed in the current Linux environment and returned `native_vlc_lifecycle=SKIP reason=windows_required`. No Windows result is claimed. The repository CI configuration remains the authoritative route for Windows-native installation and lifecycle validation when the Windows runner is available.

Windows subtitle attachment/removal/delay, native media replacement, cleanup, and authorized Live EOF runtime acceptance remain **NOT EXECUTED** in this task environment.

## 27. Real Provider Validation

No new populated authorized-provider acceptance run was executed. The previous repository evidence records that the authorized Xtream session authenticated but returned zero VOD and Series records; it therefore cannot establish populated non-live acceptance. The current task used only synthetic payloads, localhost protocol fixtures, and public documentation.

Authorized MAG production acceptance remains unresolved before a structurally valid token-bearing handshake. No username, password, MAC, token, cookie, authorization header, or raw credential-bearing stream URL appears in this report or the new committed changes.

## 28. Security Audit

The refined scan inspected 455 files and found **zero production/documentation findings** for credential-bearing URLs, bearer literals, JWTs, private keys, AWS keys, or literal cookie/authorization values. Seven credential-shaped URL matches were confined to existing synthetic tests that intentionally exercise redaction and unsafe-URL handling; they are not authorized-provider values.

The AST boundary scan found zero forbidden imports across domain, application, and presentation layers. Subtitle contents stay local. Provider secrets stay in secure infrastructure boundaries. No provider payloads were uploaded to external AI services or included in the repository. `git diff --check` passed.

## 29. Defects Found

One in-scope compatibility defect was found. The M3U EXTINF separator scanner treated a backslash-escaped quote inside a quoted ignored attribute as a closing quote. That caused a valid-looking EXTINF record to fail before its display-name separator could be found.

No additional production defect was proven by the new Xtream, MAG, XMLTV, subtitle, artwork, concurrency, or performance fixtures. The native track-shape failure was an environment/binding availability problem, not a proven application defect.

## 30. Defects Fixed

The M3U parser’s `_split_extinf_metadata_and_name()` now tracks a minimal `escaped` state while inside a quoted attribute. A backslash escapes the next character, and only an unescaped matching quote closes the attribute. Required title/stream pairing, URL validation, channel-number validation, and duplicate identity behavior remain unchanged.

The fix followed the required test-first sequence: the new escaped-quote fixture failed before implementation, the minimum source change was applied, the focused 12-test M3U suite passed, the provider matrix passed, and the final broad quality gates passed.

## 31. Defects Rejected / Deferred

No speculative protocol support was implemented. Catch-up/archive is deferred because no provider advertises a verified provider-neutral contract. MAG VOD/Series/Episode is unsupported by the current adapter contract. Remote subtitles, remote XMLTV caching/scheduling, adaptive playback logic in Python, telemetry, and provider-specific enrichment remain future work.

The missing native `libvlc_new` symbol in the optional track-shape probe was not “fixed” because the application binding inventory and fake-backed adapter contracts already expose the exact symbols used by the adapter; installing or changing the host VLC runtime would be an environment operation, not a proven application defect.

## 32. Documentation Changes

The final documentation increment updates `README.md`, `CHANGELOG.md`, and `PROJECT_STATUS.md` with the synthetic compatibility validation, the escaped-quote parser fix, the quality-gate split, security classifications, performance evidence, and explicit real-provider/Windows/native limitations. This report is the single authoritative reliability-validation record. No additional audit report is created.

## 33. Git Commit History

The logical commit sequence for this reliability phase is:

| Order | Commit | Scope |
|---:|---|---|
| 1 | `audit: record real-world IPTV reliability baseline and protocol research` | Baseline, architecture, public research, and compatibility evidence notes. |
| 2 | `compat: extend synthetic IPTV protocol fixtures` | Xtream, MAG, M3U, XMLTV, and subtitle fixture coverage. |
| 3 | `fix: handle escaped quotes in M3U EXTINF attributes` | Minimum parser fix proven by regression. |
| 4 | `test: add reliability validation matrix coverage` | Regression and validation test additions. |
| 5 | `docs: document real-world IPTV reliability validation` | README, CHANGELOG, PROJECT_STATUS, and this report. |

The exact hashes will be filled after the commits are created and the post-push verification is complete. No empty commits, force-push, history rewrite, or environment-generated lockfile is permitted.

## 34. Push Verification

This section is intentionally pending until the logical commits are created and pushed. The required final evidence is `git fetch origin main`, `HEAD == origin/main`, a clean worktree, no staged changes, no untracked files, and a normal `git push origin main` result. The final report will be updated once with the exact synchronized revision and then included in the final documentation commit.

## 35. Remaining Blockers

The remaining evidence blockers are populated authorized Xtream acceptance, real-provider subtitle interoperability, MAG production handshake/Live acceptance, MAG non-live acceptance, Windows-native VLC lifecycle and subtitle controls in an actual Windows environment, and optional native VLC track-shape validation in an environment with a resolvable `libvlc_new` symbol.

These blockers do not invalidate the deterministic synthetic and local results, but they prevent a stronger readiness classification. They must not be hidden behind passing tests or inferred from public protocol references.

## 36. Commercial Readiness Classification

**Classification: C — PARTIAL.** The current implementation has a strong deterministic reliability baseline and preserves the architecture, security boundaries, and existing Live EOF recovery. It is suitable for continued controlled development and synthetic/native validation. It is not commercially ready for an unconditional claim because the required real-provider and Windows/native evidence is incomplete and several provider-dependent capabilities remain unsupported or unresolved.

The evidence does support **IMPLEMENTED/VERIFIED** claims for the existing Xtream/MAG/M3U contracts, local subtitles, artwork safety, search/filter behavior, stale-result protection, and bounded large-catalogue UI behavior within their tested boundaries. It supports **PARTIAL**, **BLOCKED**, **DEFERRED**, **NOT EXECUTED**, and **UNSUPPORTED** classifications for the remaining areas shown in the matrices above.

## 37. Exact Next Steps

1. Execute the controlled authorized populated Xtream acceptance procedure, recording only aggregate authentication, Live/VOD/Series/Episode/EPG/artwork/search/playback/subtitle outcomes.
2. Execute the authorized MAG acceptance procedure against a portal that yields a structurally valid handshake, first validating the existing Live/EPG/search/stream contract before considering any non-live scope.
3. Run the Windows CI/native desktop gates, including VLC binding, media creation/replacement, cleanup, Live EOF recovery, and local subtitle attachment/removal/delay.
4. Re-run the optional VLC track-shape probe in an environment where the installed native binding resolves `libvlc_new`, and record only the observed return shapes.
5. Reassess the readiness classification after those evidence gaps are closed; do not add catch-up, remote subtitle, or MAG non-live behavior without a provider-neutral contract and verified acceptance evidence.

## References

[1]: https://github.com/engenex/xtream-codes-api-v2 "engenex/xtream-codes-api-v2 — public Xtream Codes API V2 documentation repository"
[2]: https://docs.rs/crispy-stalker/latest/crispy_stalker/ "crispy-stalker — public Stalker/MAG protocol client documentation"
[3]: https://m3u.codes/guides/m3u-format/ "M3U.codes — public M3U format and IPTV attribute guide"
[4]: https://wiki.xmltv.org/index.php/XMLTVFormat "XMLTV Wiki — public XMLTV format reference"
[5]: https://github.com/XMLTV/xmltv/blob/master/xmltv.dtd "XMLTV/xmltv — public XMLTV DTD"
[6]: https://github.com/kiddac/XStreamity "KiddaC XStreamity — public Xtream Codes Enigma2 plugin repository"
[7]: https://github.com/kiddac/EStalker "KiddaC EStalker — public Ministra/Stalker Enigma2 plugin repository"
[8]: https://github.com/XMLTV/xmltv "XMLTV/xmltv — public project repository and license metadata"
[9]: https://www.matroska.org/technical/subtitles.html "Matroska — public subtitle technical reference for SRT and SSA/ASS"
