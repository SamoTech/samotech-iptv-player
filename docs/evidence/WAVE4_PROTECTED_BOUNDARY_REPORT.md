# Wave 4 Protected-Boundary Baseline

**Captured at HEAD:** `efa178502a597c610338c3a90b5ed414634a5ed7`
**Remote parity:** `HEAD == origin/main` at capture
**Purpose:** Preserve the exact Wave 3/release baseline before preparing the public-testing release required by Wave 4.

## Release and History Baseline

| Item | Recorded baseline | Protection |
|---|---|---|
| Current application version | `0.1.5` in `pyproject.toml` | Increment only after implementation and all pre-version release gates pass |
| Existing tag | `v0.1.5` → `fb83b67e3402ec3678fb3a0a570348744a0f9ff7` | Historical tag and release remain untouched |
| Existing release | `v0.1.5`, published, non-draft, non-prerelease | Do not edit, replace, or delete assets |
| Existing EXE asset | `SamoTech-IPTV-Player-Windows-x64-v0.1.5.exe`, 135,514,685 bytes, SHA-256 `ac3e04b9458bc8126180738164cba239a42c862e0f223575853f4827964b93c3` | Historic asset is immutable evidence |
| Existing checksum asset | `SHA256SUMS.txt`, 111 bytes | Historic asset is immutable evidence |
| Wave 3 implementation | `b1dd16090fc9de1e8a788af55b78b319d1401363` | Do not rewrite Wave 3 reports or classifications |
| Wave 3 documentation | `efa178502a597c610338c3a90b5ed414634a5ed7` | Preserve evidence and historical wording |
| Latest hosted results at capture | CI `32332576227`, Windows Portable EXE `32332576226`, CodeQL `32332576205` — all successful | New work must maintain equivalent/all required gates |

## Protected README and Workflow Boundaries

The README heading-plus-badge block (lines 1–15 in the captured file) has SHA-256 `d6310d733baae10823f9a84f2bb7ad157706930d993f4b26d78eb534d7da810d`; the complete captured README has SHA-256 `b5fae9edbbe346864c76547744aef294040f865243d349d46c56f850fa5bcd25`. The badge block is protected byte-for-byte. Documentation changes may occur only below this block and only when accurate evidence exists.

The existing workflows retain least-privilege permissions: CI has `contents: read`; CodeQL has `security-events: write` and `contents: read`; Windows Portable EXE has `contents: read`, with the existing release-publishing job scoped to tags and its existing `contents: write` permission. No workflow permission, validation gate, pinned VLC hash/version, or release condition is a Wave 4 simplification target.

## Architecture Baseline

| Boundary | Current verified implementation | Wave 4 preservation rule |
|---|---|---|
| Playback backend | One `VlcPlayerAdapter` implementing `PlayerPort` with libVLC | No second player backend, proxy, external player process, or speculative replacement |
| Native rendering | `VlcVideoSurface` is a Qt-owned native window attached once to the existing player | Preserve native surface ownership and platform output routing |
| Playback lifecycle | Typed `PlaybackStateMachine`, serialized lock, session/generation identities, bounded live recovery, liveness monitoring | Extend telemetry at existing typed boundary only; never bypass lifecycle ownership |
| Provider source types | M3U/M3U8 local file or URL, Xtream server/username/password, MAG/Stalker portal/device identity | Preserve only protocol-specific fields and existing legitimate MAG flow |
| Secret handling | Password/MAC input is masked and cleared; logs use bounded safe labels and sanitized data | Never expose credentials, private URLs, tokens, headers, cookies, or MAC addresses |
| Provider account/capability | Optional typed account expiration/trial model and four-state capability truth model | Do not infer provider support or subscription states from playback results |
| Existing diagnostics | Safe startup JSON diagnostics plus libVLC lifecycle logs; player shell’s Info control currently supplies only a minimal state/control summary | Add only sanitized local playback diagnostics; do not expose raw backend objects or unredacted user input |

## User-Feedback Investigation Baseline

The current manual M3U dialog already offers a playlist URL or local file picker, auto-generates an M3U provider identifier, and asks no extra provider-ID field. The Xtream dialog uses server URL, username, and password; the MAG/Stalker dialog uses portal URL and protected device identity. The combined add-provider entry point supports Smart Import and manual protocol choice, although Smart Import’s current “Test Connection” control only validates local detection and does not prove connectivity.

The main window already routes the Settings action directly to an in-shell settings page where `PlayerShell` exists, with a dialog fallback only for reduced test shells. It owns dialog references and uses transient dialogs, rather than replacing the Qt main-window architecture. The player shell uses genuine fullscreen toggling, hides VOD seek behavior for live playback, exposes audio/subtitle/aspect controls, and already polls safe public position/duration/volume/mute data.

## Evidence Limits at Capture

Wave 3’s classification is retained: architecture, deterministic controls, security gates, and Windows packaging are accepted; decoded IPTV media and commercial-provider compatibility are not verified. The Linux sandbox still lacks a local libVLC runtime and has an existing PySide6 collection segmentation-fault limitation. These facts do not prevent a public-testing release, but they prohibit unsupported compatibility claims.
