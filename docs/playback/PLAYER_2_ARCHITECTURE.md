# SamoTech Player 2 Architecture

## Purpose

Player 2 turns the original play/pause/stop abstraction into a commercial playback engine while preserving the existing provider, resolution, shared-libVLC, qasync, and Live EOF recovery architecture. The presentation layer remains provider-neutral: `PlayerShell` receives application-owned callbacks and an injected `PlayerPort`; it never imports libVLC, constructs provider URLs, reads credentials, or resolves streams.

## Runtime boundary

The authoritative playback path remains:

> `PlaybackTarget` → provider resolver → `ResolvedPlayback` → `PlayerPort` → `VlcPlayerAdapter` → libVLC.

Provider adapters continue to own provider-specific authentication, catalogue requests, and stream resolution. `VlcPlayerAdapter` is the only supported media backend. The adapter receives already-resolved playback values and does not expose raw backend objects to the application or UI.

| Layer | Player 2 responsibility | Explicitly preserved boundary |
| --- | --- | --- |
| Domain | Provider-scoped history identity and progress invariants | No provider URLs, credentials, or backend types |
| Application | Typed player DTOs, state machine, target orchestration, resume-safe seek, progress recording | Provider adapters remain unchanged |
| Port | Play lifecycle, state-independent controls, position, duration, seek, volume, mute, tracks, aspect ratio, restart | UI does not depend on libVLC |
| Infrastructure | Native libVLC calls, event translation, serialization, recovery | One shared player; existing Live recovery policy is not rewritten |
| Presentation | Overlay controls, mode separation, keyboard/fullscreen interaction, generic safe errors | No stream construction, URL handling, or credentials |

## Typed capability model

`application/dtos/player.py` defines `PlaybackState`, `AudioTrack`, `SubtitleTrack`, `PlaybackContext`, `PlayerDiagnostics`, and `PlayerCapabilities`. Capabilities are evidence-based. Position, duration, percentage seek, absolute seek, volume, mute, audio tracks, subtitle tracks, restart, and aspect-ratio controls are exposed only because the installed python-vlc binding provides the corresponding native methods. Malformed native track metadata is skipped rather than fabricated.

The `PlayerPort` contract now includes native position and duration reads, millisecond and fractional seek, software volume and mute, typed audio/subtitle enumeration and selection, restart, and aspect-ratio override operations. All mutations are asynchronous and the VLC adapter serializes commands with its existing playback lock.

## State and stale-work safety

`PlaybackStateMachine` is application-owned and maps the adapter's preserved internal `_PlaybackState` values into the public state vocabulary. It rejects stale media generations and stale session tokens, tolerates duplicate native events, and prevents terminal stop state from being overwritten by late callbacks. The adapter retains its established recovery state, watchdogs, backoff, stability window, and Live EOF policy.

Playback attempts remain monotonic through `PlaybackAttemptRegistry`. A newer target invalidates older resolution work before it may mutate the player. `PlayerShell` separately guards provider, catalogue, artwork, non-live detail, and playback-generation results. Provider changes clear playback context, artwork state, non-live requests, and mode-specific controls.

## Commercial controls

The overlay provides elapsed and duration labels, a seek slider for Movie and Episode only, ±10-second and ±30-second actions, volume, mute, audio tracks, subtitles, aspect ratio, restart, diagnostics, fullscreen, pause, resume, stop, and exit behavior. Live playback displays `LIVE` and disables VOD seek and restart controls. Controls are driven by qasync-owned tasks, and progress polling is bounded to one in-flight poll per shell.

Mouse movement and keyboard activity reveal the overlay; the existing timer hides it after inactivity when playback is active. `F` toggles real window fullscreen, `Escape` exits fullscreen, and `Space`, `Left`/`J`, `Right`/`L`, and `M` provide keyboard actions without intercepting editable text fields. The native video surface remains the single Qt-owned output window.

## Native track semantics

python-vlc converts libVLC track-description linked lists to `list[(id, name)]`. The adapter converts only structurally valid records into immutable `AudioTrack` and `SubtitleTrack` DTOs and marks the native active ID. Audio and subtitle selection validates that the requested ID was reported by the current input. Subtitle disable is the native `-1` operation, not a fabricated track.

## History, progress, and resume

History now supports optional `provider_id`, `started_at`, `updated_at`, `watched_percentage`, and `completed` fields while retaining old duration and position defaults. SQLite initialization creates missing columns with backward-compatible `ALTER TABLE` statements. Existing rows retain their original semantics; optional timestamps remain nullable, and known-duration watched percentage is backfilled safely.

Record IDs are deterministic for provider, item type, and item identity, allowing progress writes to upsert the same logical record. Live records may have unknown duration and position, but are never marked completed and are never resumed. Movie and Episode resume is restored only after successful playback, only for a matching provider-scoped record, only when the record is not completed, and only when the stored position is positive. Resume failure never fails playback.

`PlayerShell` persists throttled position updates only for Movie and Episode. The progress request contains canonical provider/item identity and runtime values; it never contains a stream URL, credential, token, or raw provider payload. Completion requires known duration and full position, and watched percentage is derived from the stored duration and position.

## Error and security behavior

User-facing errors are generic and context-specific: load failure, playback failure, seek unavailable, track unavailable, volume unavailable, and aspect-ratio unavailable. Backend exception types, URLs, credentials, and tokens are not shown in the UI. Track parsing and history migration are defensive, and asynchronous presentation tasks are owned and cancelled with their Qt owner.

## Preservation rules

The implementation does not replace MAG, M3U, Xtream, `ResolvedPlayback`, provider resolver contracts, shared VLC composition, qasync ownership, or the established five-attempt/45-second Live EOF recovery policy. EStalker and XStreamity were reviewed as technology references only; no external provider architecture or source code was copied.

## Validation status

Deterministic tests, offscreen PlayerShell native and performance probes, source quality gates, and the Linux-side skip behavior of the Windows-only VLC probe are recorded in [`PLAYER_2_RUNTIME_VALIDATION.md`](PLAYER_2_RUNTIME_VALIDATION.md). Windows native VLC execution and populated authorized-provider acceptance remain explicitly unexecuted in the Linux environment and are not represented as passing evidence.
