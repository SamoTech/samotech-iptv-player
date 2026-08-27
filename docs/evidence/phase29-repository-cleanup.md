# Phase 29 — Repository Forensic Cleanup

**Repository:** SamoTech IPTV Player  
**Baseline:** `0ab62e123317b7a4eec789e3f0af974588d97683` (`main`, tag `v0.1.7`)  
**Scope:** Structural cleanup and documentation organization only.  
**Release protection:** No version, tag, published release, or release asset is changed by this phase.

## Initial repository condition

The initial audit began with `HEAD == origin/main` and a clean working tree at the baseline commit. The repository had a valid Clean Architecture implementation under `src/samotech_iptv/`, active legacy provider modules under the root `providers/` package, active plugin examples under `plugins/`, packaging resources under `resources/`, Windows and package build logic under `packaging/`, `scripts/`, root PyInstaller configuration, and CI workflows under `.github/workflows/`.

The root also contained a large collection of historical audit reports and completed phase checklists. These records were valuable evidence but made the root difficult to navigate. The working tree additionally contained ignored local outputs and caches including `build/`, `dist/`, `*.egg-info`, `__pycache__/`, `.mypy_cache/`, `.pytest_cache/`, and `.ruff_cache/`.

The tracked baseline inventory contained approximately 74 root-level files, 53 files under `docs/`, 245 files under `src/`, 132 files under `tests/`, 21 files under `providers/`, 7 files under `scripts/`, 5 files under `packaging/`, 5 files under `resources/`, 3 files under `tools/`, 2 files under `plugins/`, and 11 files under `.github/`. The inventory was captured before cleanup in `/tmp/phase29_initial_inventory.txt` during execution; it is not a repository dependency.

## Discovery and dependency mapping

The audit followed **DISCOVER → CLASSIFY → TRACE REFERENCES → VERIFY PURPOSE → DECIDE → MOVE/CONSOLIDATE/DELETE → UPDATE REFERENCES → TEST → BUILD → PACKAGE → VERIFY → DOCUMENT**. Root reports were checked for references, source package imports were traced, dynamic plugin and resource paths were reviewed, packaging specs and CI workflows were inspected, and test discovery was preserved through `pytest.ini`, `pyproject.toml`, and the CI commands.

The current source architecture is already coherent. Domain entities, value objects, repositories, and events are split into packages with compatibility shims; application DTOs, ports, and use cases are grouped by concern; infrastructure separates network, parsing, providers, database, security, configuration, and player; presentation owns Qt dialogs, views, models, theme, and the shared player shell. No source move was justified.

The provider boundary remains explicit: M3U, Xtream, MAG/Stalker, and XMLTV handling are grouped under provider/parsing infrastructure, while HLS/DASH parsing and libVLC media handling remain separate. The root `providers/` package is an active legacy MAG compatibility dependency behind `MagProviderAdapter`, not a duplicate that can be deleted.

The player boundary is already separated into `PlayerPort`, `VlcPlayerAdapter`, `vlc_runtime.py`, playback/application DTOs, and presentation diagnostics. No playback or VLC move was justified because changing this boundary would create more risk than value.

## Decision matrix

| Decision | Scope | Evidence and rationale |
|---|---|---|
| **MOVE** | Historical root audit reports and completed checklists | They are date/commit-scoped records, not active root guidance. No code, CI, packaging, or runtime imports depend on their root location. They now live under `docs/historical/`. |
| **MOVE** | Active docs currently in `docs/` root | The files have clear architecture, provider, playback, packaging, development, or testing ownership. They now live under conceptual directories without changing their substantive content. |
| **DELETE** | `docs/ARCHITECTURE.md` | It was a two-line stub pointing to root `ARCHITECTURE.md`, had no active dependency, and duplicated the canonical document. The deletion is the only tracked-file deletion in this phase. |
| **REMOVE LOCAL OUTPUT** | Ignored caches and generated outputs | `build/`, `dist/`, `*.egg-info`, `__pycache__/`, `.mypy_cache/`, `.pytest_cache/`, and `.ruff_cache/` were local/generated and not tracked. They were removed from the working tree; ignore rules already covered the relevant Python/build outputs. |
| **KEEP** | Root `README.md`, `LICENSE`, `ARCHITECTURE.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `PROJECT_STATUS.md`, `ROADMAP.md`, `SECURITY.md`, configs, `conftest.py`, specs, and workflow-facing directories | These are conventional repository entrypoints, active policy/current-state files, or tooling locations referenced by GitHub, pytest, packaging, and CI. |
| **KEEP** | Compatibility shims, root `providers/`, `plugins/`, probe scripts, resource marker files, and packaging scripts | Imports, dynamic loading, tests, CI, PyInstaller, or package discovery reference them. Static “unused” appearance is insufficient for deletion. |
| **INVESTIGATE_FURTHER** | Historical references to retired `build/` evidence and old commit-scoped paths | Their files are not active dependencies. The references are retained as historical meaning and explicitly identified as non-active evidence in `docs/historical/README.md`. |

## Files moved

### Historical reports moved from repository root

The historical audit/report set moved to `docs/historical/` includes the advanced Xtream, AI team, architecture, baseline, build/release, commercial, current-state, final-audit, implementation, IPTVnator, IPTV continuation, KiddaC, MAG, Ministra, next-phase, Phase 24–28, Player 2/3, product-gap, protocol/playback, provider, real-IPTV, smart-import, stability, test, UI, VLC, Wave 3, Windows, Xtream, zero-touch, and completed `todo.md` records. Their filenames and contents are preserved, with only relative link targets repaired where necessary to reflect the new location.

### Active documentation reorganized

| New directory | Moved content |
|---|---|
| `docs/development/` | `API.md`, `PLUGIN_SDK.md` |
| `docs/providers/` | MAG reports/research/protocol notes, Xtream/MAG implementation record, KiddaC compatibility/adaptation notes, and secure M3U source design |
| `docs/playback/` | Protocol/playback architecture, Player 2 architecture/runtime validation, and Player 3 architecture/acceptance/runtime validation |
| `docs/packaging/` | Windows acceptance and Live EOF runtime validation procedures |
| `docs/testing/` | Public testing guide and feedback intake checklist |
| `docs/historical/` | Prior phase/audit records and the historical index |
| `docs/evidence/` | Existing active evidence plus this report |

## Files deleted

`docs/ARCHITECTURE.md` was deleted because it contained only a duplicate pointer to `../ARCHITECTURE.md`. The canonical root architecture document remains, and all references now point directly to it.

No source module, provider implementation, player/media implementation, packaging spec, workflow, resource, test, policy, or historical evidence record was deleted.

## Files consolidated and archived

No executable implementation was consolidated. The documentation consolidation consists of relocating records into explicit categories and retaining a single canonical root architecture document. Historical records were **archived by location**, not rewritten as current-state guidance. The `docs/historical/README.md` index explains this boundary.

## Duplicate and dead-code analysis

The exact-hash scan found only intentionally empty package/marker files: directory `.gitkeep` markers, `py.typed`, and test/package `__init__.py` markers. These are not duplicates for removal because their locations have packaging, namespace, or directory-preservation purposes.

Near-duplicate-looking provider modules were retained after tracing imports: the root `providers/mag/` implementation is the legacy MAG protocol stack used behind `src/samotech_iptv/infrastructure/providers/mag_adapter.py`; it is not an accidental second UI or application layer. The `src/samotech_iptv` compatibility shims are retained because package imports and historical compatibility tests depend on them. Probe scripts are retained because CI and manual Windows/runtime validation reference them.

No file was classified **PROVEN_UNUSED** for deletion beyond the architecture stub. Unknown dynamic resources and plugin paths were not deleted. No unreferenced function or class was automatically removed; that would require a separate semantic dead-code review and is outside safe structural cleanup.

## Root cleanup results

The root now contains repository entrypoints, policy/current-state documents, build and test configuration, active source-adjacent directories, and tooling directories. Historical reports no longer compete with `README.md`, `PROJECT_STATUS.md`, `ARCHITECTURE.md`, and `SECURITY.md` for root attention. Generated outputs were removed locally and remain ignored.

## Documentation cleanup results

Current documents now have conceptual homes under `docs/architecture/`, `docs/development/`, `docs/providers/`, `docs/playback/`, `docs/packaging/`, `docs/testing/`, and `docs/evidence/`. Historical records are under `docs/historical/`. Relative links in active documentation were repaired and checked. The release-notes template retains its `{{WORKFLOW_URL}}` placeholder intentionally; it is substituted by the release workflow and is not a broken repository link.

Historical reports remain evidence and were not silently re-authored. Link-only path repairs are recorded as structural maintenance, not changes to historical findings.

## Test structure results

The test tree was not moved because its current arrangement preserves pytest discovery and historical traceability: application/domain/infrastructure tests remain discoverable at `tests/`, MAG protocol tests are grouped under `tests/providers/mag/`, presentation tests retain their `test_presentation_` naming, and native/performance probes remain at the paths referenced by CI and Windows workflows. No test was renamed or weakened.

## Packaging and resource safety

The root PyInstaller spec remains in place because CI and release workflows reference it directly. The forensic spec and runtime hook remain under `packaging/` because the Windows workflows and packaging tests reference those exact paths. Package metadata continues to discover `src/samotech_iptv`, the root `resources` package remains the runtime asset location, and both themes plus marker directories remain available to setuptools and PyInstaller. No resource or packaging file was moved.

## Provider and media safety

M3U, Xtream, MAG/Stalker, and XMLTV provider boundaries were inspected and retained. Provider protocol handling remains separate from HLS/DASH parsing, URI classification, and libVLC media playback. `VlcPlayerAdapter`, `vlc_runtime.py`, `PlayerPort`, diagnostics, stream DTOs, and platform-specific packaging behavior were not moved or rewritten.

## Security results

The current tracked tree was scanned for credential-shaped literals and sensitive transport patterns. Existing synthetic test values and security-boundary code were classified as expected fixtures or implementation logic. No production credentials, cookies, tokens, authorization values, private provider URLs, or raw diagnostic dumps were added or moved into documentation. Historical documents retain their original evidence context and are not used as runtime inputs.

## Final structure summary

```text
.
├── .github/                 # policies, templates, CI, CodeQL, Windows workflows
├── docs/
│   ├── architecture/       # architecture decision and module notes
│   ├── development/        # API and plugin SDK guidance
│   ├── evidence/           # active audit and validation evidence
│   ├── historical/         # preserved prior phase and audit records
│   ├── packaging/          # Windows/native packaging acceptance procedures
│   ├── playback/           # player/protocol/runtime documentation
│   ├── providers/          # provider protocol and compatibility documentation
│   ├── testing/            # public testing and feedback procedures
│   └── diagrams/
├── packaging/              # specs, runtime hook, build requirements, release template
├── plugins/                 # trusted local example plugin
├── providers/               # active legacy MAG compatibility package
├── resources/               # themes, icons, translations markers
├── scripts/                 # build, VLC preparation, release-note, audit scripts
├── src/samotech_iptv/       # application source and layered architecture
├── tests/                   # unit, integration, presentation, packaging, runtime probes
├── tools/                   # controlled manual/runtime probes
├── ARCHITECTURE.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── PROJECT_STATUS.md
├── README.md
├── ROADMAP.md
├── SECURITY.md
├── pyproject.toml
├── pytest.ini
└── samotech-iptv-player.spec
```

## Validation and blockers

Final validation must include Git status and parity, duplicate/dead-reference/structure scans, imports, Ruff, Black, MyPy, pip integrity, scoped compilation, focused provider/presentation tests, the complete non-presentation corpus, presentation modules independently, packaging tests, `python -m build`, fresh wheel installation, resource access, startup smoke, security/redaction scans, and hosted CI, CodeQL, and Windows packaging workflows where applicable.

The known full monolithic PySide6 pytest collection crash must be recorded if reproduced; it must not be hidden by weakening tests. Linux must not be described as native Windows runtime verification, although hosted Windows workflow results may be reported separately.

## Release impact

This phase is protected against version/tag/release changes. The existing `v0.1.7` release and its published assets remain untouched. The cleanup is a forward structural/documentation commit only. A future release recommendation is outside this phase and requires a separate explicit authorization.

## Final commit and decision

**Final commit SHA:** pending the cleanup validation commit.  
**Repository parity:** pending final push verification.  
**Decision:** pending final validation; expected result is **A — CLEANUP COMPLETE** if all required gates pass, otherwise **B — PARTIALLY COMPLETE WITH BLOCKERS**. No release action is authorized by this phase.
