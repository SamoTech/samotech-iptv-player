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

## Wave 5 — Pre-Feedback Hardening, UX Polish & Real-World Test Readiness

- [x] Read the complete authoritative Wave 5 specification and preserve the v0.1.6 public-testing classification.
- [x] Phase 1 — Create `docs/evidence/WAVE5_BASELINE.md` from HEAD/origin parity, v0.1.6 release identity, Wave 4 audit, diagnostics, launcher, player/provider surfaces, workflow gates, and byte-exact README badge evidence.
- [x] Phase 2 — Run and classify the complete first-run user-journey audit; implement only confirmed P0/P1 and clearly justified low-risk P2 findings.
- [x] Phase 3 — Audit M3U, Xtream, MAG/Stalker, and Smart Import setup labels, masking, validation, source-specific fields, loading/error/retry/cancel behavior, and duplicate-source handling.
- [x] Phase 4 — Audit actionable empty states and user-facing error classifications without exposing technical secrets or fabricating provider capabilities.
- [x] Phase 5 — Audit context-sensitive live/VOD/series playback controls, fullscreen, focus, keyboard/remote-like controls, search, and large-playlist UI-thread risks without changing libVLC lifecycle ownership.
- [x] Phase 6 — Audit EPG, favorites/history/resume, settings, safe diagnostics, debug launcher, logs, provider/media boundaries, and capability-truth surfaces.
- [x] Phase 7 — Improve documentation only where required, create the developer-facing Reddit feedback intake checklist, and preserve the README badge block byte-for-byte.
- [x] Phase 8 — Add/update focused deterministic coverage and run presentation/provider/VLC/diagnostics/security/large-data regressions, official non-presentation corpus, Ruff, Black, MyPy, Bandit, secret/credential/redaction scans, and diff checks.
- [x] Phase 9 — Run the Windows Portable workflow only if implementation changes exist; document every pass, failure, or Windows-only validation gap without creating a release.
- [x] Phase 10 — Create `PHASE28_PRE_FEEDBACK_HARDENING_AUDIT.md`, state the evidence-based final decision, commit/push only verified repository changes, and deliver that file as the one final report.

## Newly Attached Authoritative Specification

- [x] Read the complete authoritative multi-agent engineering specification and map its requirements to the Phase 28 repository baseline.
- [x] Convert confirmed requirements into the following dependency-ordered initialization, audit, implementation, validation, and push checklist.

## AI Engineering Team — First Engineering Cycle

- [x] Phase A1 — Create a version-controlled AI engineering team charter defining all 14 roles, responsibilities, evidence standards, decision boundaries, handoffs, and no-automation scope.
- [x] Phase A2 — Record the team initialization baseline: HEAD/origin parity, v0.1.6 release/tag/assets, Phase 28 audit, protected README digest, architecture, provider, playback, UI, diagnostics, tests, CI/CD, and known feedback.
- [x] Phase B1 — Complete independent Chief Architect, provider protocol, media, VLC/playback, UI/UX, Windows, performance, security, QA, feedback, research/compatibility, release/CI, and documentation evidence reports.
- [x] Phase B2 — Complete the independent-auditor challenge report without using its findings to edit production code directly.
- [x] Phase C — Produce a cross-agent review that deduplicates findings, rejects unsupported claims, resolves architecture conflicts, and prioritizes only P0/P1/P2 work.
- [x] Phase D — Approve no change, patch, defer, research, or release-candidate decisions for every confirmed finding; prohibit a v0.1.7 release unless new evidence justifies it.
- [x] Phase E — Implement only approved low-risk evidence-backed changes at the correct layer, with focused deterministic regression coverage. No production change was approved; additive governance documentation is the sole accepted patch.
- [x] Phase F — Run Ruff, Black, MyPy, Bandit, credential/secret scans, relevant unit/integration/provider/playback/presentation/large-data tests, full non-presentation corpus, isolated Qt presentation corpus, protected-boundary checks, and Windows Portable validation when implementation changes exist. Windows validation was not re-run because no production implementation changed.
- [x] Phase G — Complete the final independent audit and Chief Architect decision; capture all accepted, rejected, deferred, unsupported, external, and environmental outcomes.
- [x] Phase H — Create `AI_TEAM_STATUS.md` with all 20 required sections and deliver it as the first initialization result; commit/push only after all applicable tests pass.

## Newly Attached Authoritative Specification

- [x] Read the complete autonomous current-state assessment specification and map its requirements to the repository state at commit `0e21c9172ba4bf76830f61bbd87ffd2444313c70`.
- [x] Convert confirmed requirements into the following dependency-ordered assessment, selection, implementation, validation, and push checklist.

## Autonomous Current-State Assessment & Execution Cycle

- [x] Phase 1 — Reconcile current AI team status, charter, Phase 28 audit, Git state, v0.1.6 release/tag/assets, workflows, README digest, architecture, providers, playback/VLC, UI, diagnostics, tests, feedback, launcher, and performance probes.
- [x] Phase 2 — Produce the current prioritized feedback table with evidence, frequency, severity, reproducibility, affected subsystem, specialist owner, and recommended action.
- [x] Phase 3 — Complete focused role-separated protocol, playback, UX, Windows, performance, diagnostics, security, QA, compatibility, CI, and documentation investigations using current repository evidence.
- [x] Phase 4 — Cross-review all candidates, select the highest-value actionable issue using value × evidence × user impact × risk × feasibility, and complete an independent pre-implementation challenge.
- [x] Phase 5 — Implement the approved production improvement at the correct architectural layer, including focused positive and negative regression coverage.
- [x] Phase 6 — Run focused tests, full non-presentation corpus, isolated presentation corpus, Ruff, Black, MyPy, Bandit, credential/redaction scans, relevant performance tests, protected-boundary checks, and Windows Portable validation.
- [x] Phase 7 — Complete independent final audit, update only current-cycle documentation, commit/push verified non-empty changes, wait for all required workflows, and inspect results.
- [x] Phase 8 — Deliver the final decision with issue, evidence, implementation, tests, security, performance, Windows, independent-audit, blockers, release impact, commit SHA, remote parity, and next action.

## Phase 28 — UI/UX, Visual Design & Complete Menu Audit

- [x] Read the complete Phase 28 UI/UX, visual-design, and menu-audit specification and reconcile its release instruction with its explicit protection boundaries.
- [x] Phase 1 — Formally assign the Interface & Visual Design Engineer role, preserve v0.1.6/release/README/workflow boundaries, and capture current repository, workflow, architecture, feedback, diagnostics, launcher, and performance baseline.
- [x] Phase 2 — Build a machine-readable inventory of every user-facing window, dialog, page, panel, menu, action, button, control, list, form, setting, keyboard shortcut, state, and hidden/discoverability gap.
- [x] Phase 3 — Complete menu, icon, player-control, fullscreen, provider, settings, large-playlist, EPG, state, typography/spacing, theme, accessibility, discoverability, and Reddit-feedback mapping audits.
- [x] Phase 4 — Produce a no-feature-loss exposure matrix, role-separated findings, visual/design cross-review, and independent pre-implementation challenge; select only actual capability-backed P0/P1/P2 work.
- [x] Phase 5 — Implement the highest-value approved presentation/UI improvements without changing provider, playback, security, release, or media architecture; add focused positive and negative regression coverage.
- [x] Phase 6 — Run focused UI/provider/PlayerShell/menu/settings/navigation/accessibility/large-data tests, full non-presentation corpus, isolated presentation corpus, Ruff, Black, MyPy, Bandit, secret/protected-boundary scans, Windows Portable, CI, and CodeQL validation.
- [x] Phase 7 — Complete the independent final UI audit, create `PHASE28_UI_VISUAL_DESIGN_AUDIT.md` with all 30 required sections, and decide A/B/C/D from actual user-facing evidence.
- [x] Phase 8 — If all release criteria are satisfied and the design decision supports release qualification, update legitimate version sources, create/push a non-empty release commit and v0.1.7 tag, publish, verify assets/checksum/workflows, and report final status. Otherwise preserve v0.1.6 and explain why.
