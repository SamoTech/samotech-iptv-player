# Audit Baseline

## Scope and method

This baseline was captured before any audit-driven source change. The repository was synchronized with `origin/main` using a fast-forward-only update; the branch was `main`, the worktree was clean, and no application, test, workflow, or packaging file was modified during baseline capture. Raw command output is retained locally in `build/AUDIT_BASELINE_RAW.txt` and `build/AUDIT_BASELINE_TOOLS.txt` as audit evidence.

## Repository identity

| Item | Baseline value |
|---|---|
| Repository | `SamoTech/samotech-iptv-player` |
| Branch | `main` |
| Commit | `65e4ff8eab40cf770799a5e2139f8497778362cc` |
| `origin/main` | `65e4ff8eab40cf770799a5e2139f8497778362cc` |
| Worktree | Clean |
| Python | 3.12.3 |
| Operating system | Linux x86_64, kernel 6.1.102 |
| Project version | 0.1.1 |
| Python requirement | >=3.12 |
| License | MIT |

## Tooling baseline

| Tool | Version/status |
|---|---|
| pytest | 9.1.1 |
| Ruff | 0.16.3 |
| Black | 26.5.1 |
| MyPy | 2.3.1 |
| PyInstaller | 6.22.1 |
| Bandit | Not installed in the baseline virtual environment |
| pip-audit | Not installed in the baseline virtual environment |
| PySide6 | Present in the project environment; exact package inventory is retained in the raw baseline |
| python-vlc | Project dependency; exact package inventory is retained in the raw baseline |
| qasync | Project dependency; exact package inventory is retained in the raw baseline |

The project declares runtime dependencies on `aiohttp`, `defusedxml`, `keyring`, `python-vlc`, `PySide6`, and `qasync`. Development dependencies include pytest, pytest-asyncio, pytest-cov, aioresponses, Black, MyPy, Ruff, types-defusedxml, and pinned PyInstaller 6.22.1. Package discovery intentionally includes both `src/samotech_iptv*` and `providers*`; this is a critical audit subject, not a finding by itself.

## Repository inventory

The repository contains the following principal categories:

| Category | Baseline inventory |
|---|---|
| Canonical source | `src/samotech_iptv/`, including domain, application, infrastructure, presentation, runtime, security, networking, parsing, and player packages |
| Legacy/provider compatibility | `providers/`, including the legacy MAG provider and M3U/XMLTV provider modules |
| Tests | `tests/`, including domain, application, infrastructure, provider, MAG laboratory, presentation, security, packaging, native VLC, and performance tests |
| Packaging | `samotech-iptv-player.spec`, `packaging/`, `scripts/build_windows.ps1`, `scripts/prepare_windows_vlc.ps1` |
| CI/CD | `.github/workflows/ci.yml`, `codeql.yml`, `windows-portable-build.yml`, and `windows-release-artifact-acceptance.yml` |
| Security | `SECURITY.md`, `src/samotech_iptv/core/safe_logging.py`, keyring integration, artifact auditing, CodeQL workflow, security regression tests |
| Documentation | Architecture, protocol, compatibility, release, security, reliability, and previous audit reports at repository root and under `docs/` |
| Assets | `resources/` themes/icons/translations, packaged VLC handled by workflow/build scripts |
| Scripts/tools | `scripts/` and `tools/`, including artifact audits, release notes, VLC preparation, MAG transport probes, and Windows packaging helpers |
| Generated/local evidence | `.venv`, caches, coverage, `build/`, egg-info, and local inspection logs; these are environment artifacts and are not treated as source implementation |

The complete tracked-file inventory is preserved in `build/AUDIT_BASELINE_RAW.txt`.

## Baseline constraints

The previous repository work includes substantial security logging remediation, provider compatibility work, Windows packaging validation, and README/Sponsors documentation. Those changes are preserved. This audit must not treat prior reports as proof; each relevant claim will be re-inspected against source, tests, workflows, and executable evidence.

The specification requires a complete audit rather than a cosmetic rewrite. Every confirmed defect must have a root cause, impact, severity, evidence, smallest safe fix, regression test, and post-fix verification. Unsupported or environment-blocked claims must be classified as **NOT VERIFIED — ENVIRONMENT LIMITATION** rather than reported as passing.
