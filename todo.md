# Phase 27 — Real User Feedback, UI/UX Simplification & Large Playlist Acceptance

- [x] Read the complete Phase 27 specification and the required Phase 24, 25, and 26 reports.
- [x] Inspect repository status, protected release boundaries, and existing architecture before changes.
- [x] Reproduce, trace, classify, and prioritize the reported navigation, settings, provider-import, and Xtream compatibility issues.
- [x] Audit provider configuration, M3U import UX, Xtream request handling, user-facing errors, and onboarding without using or storing real credentials.
- [x] Inventory player controls, fullscreen behavior, menus, keyboard accessibility, and focus behavior without regressing Phase 24.
- [x] Create deterministic large-data fixtures and measure catalogue, EPG, category, search, switching, responsiveness, memory, CPU, and thread behavior.
- [x] Implement only confirmed, architecture-compatible UI, provider-flow, error-message, and performance fixes.
- [x] Add focused regression and large-data coverage, then run the required focused and full validation suites.
- [x] Audit README and release presentation for accurate existing screenshots only; preserve the protected badge block and create no release.
- [x] Restore Windows compatibility for the deterministic Phase 27 large-data probe without weakening its Linux memory measurement.
- [x] Write one evidence-based Phase 27 audit report with completed tasks, verification, changes, blockers, remaining actions, classifications, and final status.
- [x] Read the newly attached authoritative specification completely and map it to the current repository state.
- [x] Produce the Wave 3 repository forensic audit without implementation changes.
- [x] Derive and execute a dependency-ordered checklist, preserving protected boundaries and completed Phase 27 work.
- [x] Verify all confirmed requirements and document any exact blockers without weakening validation gates.
- [x] Deliver one final audit report against the newly attached authoritative specification.

## Wave 3 dependency order

- [x] Phase 1: Create a truthful provider/media/backend/platform capability matrix with evidence levels.
- [x] Phases 2–4: Audit and extend provider server/account/expiration/capability models only where repository evidence confirms a gap.
- [x] Phase 5: Audit resolved-stream metadata and ensure no credential-bearing playback URL is persisted or exposed.
- [x] Phases 6–8: Write the media-backend decision and contract evidence; preserve the sole libVLC path unless a proven defect requires a change.
- [x] Phases 9–14: Classify HLS, MPEG-TS, MP4/fMP4, codec, audio, subtitle, and multi-track evidence without overstating runtime support.
- [x] Phases 15–17: Audit existing buffering, liveness, recovery, switching, VOD, and series behavior against the same playback lifecycle.
- [x] Phases 18–22: Audit EPG, catch-up, player UI, server/account dashboard, and diagnostics; implement only capability-backed items.
- [x] Phases 23–24: Reuse and extend large-data and UX evidence without replacing verified Phase 27 work.
- [x] Phases 25–30: Run security, platform, authorized-runtime, negative-runtime, performance, and test-pyramid validation; record external blockers honestly.
- [x] Phases 31–33: Reconcile only evidence-backed documentation, validate hosted workflows, preserve release protections, and write the final Wave 3 report.

## Newly Attached Authoritative Specification

- [x] Read the newly attached Wave 4 specification completely and map every requirement to the current repository state.
- [x] Convert confirmed requirements into a dependency-ordered implementation and validation checklist.

## Wave 4 — Public Real-World Playback Validation + User Test Release

- [x] Phase A — Establish and document the forensic baseline: HEAD/origin parity, v0.1.5 history/assets, Wave 3 audit, playback/provider/account/capability architecture, diagnostics, Windows workflow, tests, and byte-exact README badge block.
- [x] Phase B — Investigate the listed user feedback and classify each item as confirmed/fixed, not reproduced, out of scope, or requiring Windows validation; do not redesign without evidence.
- [x] Phase C — Audit and simplify the selected-protocol source configuration path for M3U/M3U8, Xtream, and only existing MAG/Stalker behavior; retain local credential boundaries.
- [x] Phase D — Implement only confirmed safe diagnostics, explicit local playback telemetry, a sanitized one-click diagnostic report, and focused tests proving redaction.
- [x] Phase E — Add an optional Windows debug launcher that emits only meaningful, sanitized local lifecycle events; test its packaging behavior without changing normal launch behavior.
- [x] Phase F — Add a clear user feedback path and GitHub issue template that requests safe diagnostics and explicitly prohibits credentials, tokens, MAC addresses, cookies, and private URLs.
- [x] Phase G — Measure/reuse existing 1,000, 5,000, and practical 10,000+ playlist validation; fix only measurable responsiveness, memory, CPU, catalogue, search, category, and selection defects.
- [x] Phase H — Audit and make only confirmed targeted improvements to settings navigation, top-level window behavior, fullscreen/focus control, and content-aware player controls.
- [x] Phase I — Document safe public-testing installation, source setup, playback, fullscreen, diagnostics, and reporting guidance without changing the protected README badge block.
- [x] Phase J — Run focused diagnostics/provider/VLC/presentation/security/playlist/large-playlist regressions, the complete applicable corpus, Ruff, Black, MyPy, Bandit, a secret scan, and a protected-boundary diff check.
- [x] Phase K — Build and hosted-validate the Windows portable EXE: clean startup, bundled VLC/Qt, PATH/CWD, provider dialogs, source import, player controls, fullscreen, diagnostics, debug launcher, shutdown, artifact contents, checksum, and metadata.
- [x] Phase L — After every required validation gate passes, update only legitimate version sources to 0.1.6, create release notes that explicitly classify the release as public testing, commit, push, tag, publish, and wait for all required workflows.
- [x] Phase M — Download and independently verify the exact published artifact: SHA256, PE metadata, bundled VLC, launch, displayed version, release asset/tag, repository cleanliness, and byte-exact README badge block.
- [x] Phase N — Create `PHASE27_PUBLIC_TEST_RELEASE_AUDIT.md` with baseline, findings, fixes, diagnostics, launcher, performance, security, test/Windows evidence, release identity, limitations, provider status, classification, and next milestone; deliver it as the one final report.
