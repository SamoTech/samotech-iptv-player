# Current-State Execution Decision

## Current Feedback Triage

| Issue | Evidence | Frequency | Severity | Reproducibility | Affected users/subsystem | Recommended action |
|---|---|---:|---:|---|---|---|
| Provider-management dialog requires manual provider-ID entry | Current `ProviderListDialog` renders a `QLineEdit` labelled **Provider ID** and resolves Edit/Remove/Health only from exact typed text; existing regression asserts this flow. | One or more historical simplicity/menu reports | P2 | Deterministic source/test reproduction | Any user managing a registered provider | Replace manual entry with a safe non-editable selection control carrying the opaque ID as item data. |
| M3U setup complexity | M3U file/URL manual setup and generated ID behavior were previously reviewed and test-covered. No new reproducible fault exists. | Historical signal | P3 | Not currently reproduced | New M3U users | Preserve; improve only if a safe report identifies a specific path. |
| Xtream connection issue | No newly authorized/sanitized reproduction is available. | At least one historical report | P1 if reproduced | **BLOCKED_EXTERNAL** | Xtream users | Use the existing safe diagnostic/feedback path; do not modify auth/session logic speculatively. |
| Large playlist/EPG performance | 10,000-item deterministic measure exists; no current bottleneck or 50k/100k workload requirement is evidenced. | Historical signal | P3 | 10k verified; higher scale not measured | Large-catalogue users | Preserve 10k regression and defer vanity-scale work. |
| Settings/theme/fullscreen/screenshots | Current direct settings, three-choice theme selector, fullscreen controls, and documentation paths have prior evidence; no new report is available. | Historical signals | P3 | Not currently reproduced | Desktop users | Preserve current behavior and wait for safe reproducible report. |

## Specialist Findings

| Role | Current-cycle finding | Verdict |
|---|---|---|
| Chief Architect | Selection belongs in the presentation dialog. Provider ID remains an internal value and must not cross protocol/playback boundaries. | Approve bounded UI patch. |
| IPTV Protocol Engineer | Changing how a registered provider is selected does not alter M3U, Xtream, MAG/Stalker, XMLTV, EPG, session, header, redirect, timeout, or capability behavior. | No protocol risk. |
| VLC/Playback and Media Engineers | The dialog does not resolve, play, decode, or diagnose media. | No playback/media risk. |
| UI/UX Principal | A visible provider choice is more discoverable and less error-prone than manually typing an opaque identifier for every management action. A neutral placeholder prevents accidental selection. | P2 justified. |
| Windows Specialist | A standard Qt `QComboBox` is native, keyboard accessible, and does not affect fullscreen, DPI, path, package, or libVLC behavior. Hosted Windows validation remains required because production presentation code changes. | Low risk. |
| Performance Engineer | Provider-list population is bounded to registered profiles; no catalogue, EPG, search, resolver, or player work is introduced. | No performance regression expected. |
| Security Engineer | Display labels remain safe registered metadata. The opaque provider ID stays in combo item data only; credentials, base URLs, tokens, cookies, MAC values, and resolved stream URLs remain absent. | Approve subject to redaction regression. |
| Test/QA Engineer | Add positive selection, no-selection, safe-summary, edit/remove, and refresh regression cases in the existing provider-management suite. | Required. |
| Release/CI Engineer | No version/tag/release/asset/permission change is justified. Run the normal Windows Portable workflow for the application UI change before final decision. | No release. |

## Value-Based Selection

| Candidate | Value | Evidence | User impact | Risk | Feasibility | Decision |
|---|---:|---:|---:|---:|---:|---|
| Safe provider selection in management dialog | High | High | Medium | Low | High | **SELECTED** |
| Real Xtream authentication investigation | High | Low | High | Medium | Low | Defer: blocked external |
| 50k/100k performance benchmark | Medium | Low | Medium | Medium | Medium | Defer: no measured bottleneck |
| Backend/recovery/proxy redesign | Low | Low | Low | High | Low | Reject |

## Independent Pre-Implementation Challenge

The Independent Auditor challenged whether the selected work merely disguises an identifier rather than simplifying the workflow. The challenge is resolved because the current UI requires a user to know and type a safe but opaque identifier before three ordinary profile-management actions can proceed. The proposed selector presents an explicit safe choice, stores the same identifier only as non-rendered item data, preserves the placeholder/no-selection guard, and does not add duplicate state, provider logic, or credential exposure.

> **APPROVED IMPLEMENTATION:** Replace manual Provider ID entry in `ProviderListDialog` with a non-editable, accessible safe provider selector. No provider protocol, playback, media, diagnostics, release, or persistence behavior may change.

## References

[1]: [`src/samotech_iptv/presentation/dialogs/provider_list_dialog.py`](../../src/samotech_iptv/presentation/dialogs/provider_list_dialog.py)
[2]: [`tests/test_presentation_provider_management.py`](../../tests/test_presentation_provider_management.py)
[3]: [`docs/REDDIT_FEEDBACK_INTAKE_CHECKLIST.md`](../testing/REDDIT_FEEDBACK_INTAKE_CHECKLIST.md)
