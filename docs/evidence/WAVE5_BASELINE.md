# Wave 5 Forensic Baseline

**Captured repository commit:** `cf28babf324b217e3e83da0b763f9bb18fc0de05`
**Release under preservation:** [`v0.1.6`](https://github.com/SamoTech/samotech-iptv-player/releases/tag/v0.1.6)
**Release classification:** **RELEASED — PUBLIC TESTING**

## Release and Protected-Boundary State

| Boundary | Baseline evidence | Wave 5 rule |
|---|---|---|
| Main branch | `HEAD == origin/main` when captured | Preserve linear history; no force push or rewrite |
| Current package version | `0.1.6` | Do not increment during this preparation wave |
| Published release | `v0.1.6`, published, non-draft, non-prerelease | Do not modify existing assets or release metadata |
| v0.1.6 tag target | `a1fd6cdf9eec4b8ee7439768494c869a31cb9440` | Do not modify the tag |
| README heading/badge block | SHA-256 `d6310d733baae10823f9a84f2bb7ad157706930d993f4b26d78eb534d7da810d` for lines 1–15 | Preserve byte-for-byte |
| Historical evidence | Wave 3, Wave 4, and Phase 27 audit records already committed | Create new Wave 5 evidence only; never rewrite history |
| CI and release gates | CI, CodeQL, Windows Portable EXE, and release-artifact acceptance workflows were all successful for the current head/release baseline | Do not weaken, remove, or expand workflow permissions |

## Current Architecture Map

| Surface | Current source evidence | Preservation requirement |
|---|---|---|
| Media backend | `infrastructure/player/vlc_player_adapter.py` implements the single `PlayerPort` libVLC path | No second backend, proxy, relay, or media-engine rewrite |
| Playback UI | `presentation/player_shell.py` and the Qt-native VLC video surface | Keep UI at the existing typed player boundary |
| Safe diagnostics | `application/dtos/player.py`, `PlayerPort.get_diagnostics`, `presentation/playback_diagnostics.py`, and `PlaybackDiagnosticsDialog` | Only allow-listed, redacted values; missing evidence is `NOT_AVAILABLE` |
| Debug launcher | `packaging/SamoTech-Debug.bat` | Optional local diagnostic mode only; normal EXE launch remains unchanged |
| M3U setup | `M3UProviderDialog` supports a playlist file or URL | No unnecessary identifier or credentials |
| Xtream setup | `XtreamProviderDialog` uses server URL, username, password, and generated local provider ID | Keep password masking and local credential handling |
| MAG/Stalker setup | `MAGProviderDialog` accepts only implemented portal/device inputs and generated local ID | Do not add unverified portal workflow behavior |
| Smart Import | `SmartImportDialog` presents protocol-specific fields and generated IDs | Do not infer connectivity from format detection |
| Provider boundary | Provider adapters resolve streams before typed playback; player shell and VLC adapter are provider-neutral | Keep provider protocol separate from media protocol |

## User-Experience Surface Map

The source tree exposes existing player shell routing for Settings, playback info/diagnostics, live/VOD/series presentation, search, favorites/history, EPG, audio/subtitle/aspect controls, and context-aware live seeking behavior. Existing dialog implementations include accessible labels, password masking, placeholders, status messages, local cancellation, and typed registration responses. Wave 5 must determine which of these paths have observable deficiencies before changing them.

The current Settings page has General, Playback, Appearance, Network, Diagnostics, and Privacy sections. Its visible controls must be audited for truthful presentation rather than expanded with unsupported options. The fullscreen implementation remains Qt-native; Windows focus, taskbar, multi-monitor, and restoration behavior require platform evidence rather than an unqualified pass claim.

## Existing Evidence Limits

| Topic | Correct baseline classification |
|---|---|
| Real IPTV provider/media compatibility | **NOT VERIFIED** |
| Linux decoded media proof | **NOT AVAILABLE** because the sandbox has no local libVLC runtime |
| Local monolithic Qt pytest collection | **BLOCKED_ENVIRONMENT** because PySide6/shiboken collection can exit 139; individual presentation files and hosted Windows smoke paths remain usable evidence |
| Public release package | **VERIFIED** by v0.1.6 tagged workflow and published-artifact acceptance |
| Capability claims | Limited to actual provider declarations or measured runtime observations; no codec/container/stream claim may be invented |

## Wave 5 Scope Decision

Wave 5 begins as a non-release hardening audit. Any proposed change must be justified by existing code/tests, measurable behavior, a concrete security finding, or an objectively actionable usability defect. A new release is prohibited unless a confirmed public-testing P0/P1 defect is discovered and independently validated.
