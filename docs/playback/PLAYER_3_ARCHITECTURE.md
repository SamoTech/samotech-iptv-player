# Player 3 Architecture Supplement

**Date:** 2026-08-16  
**Status:** Implemented within the preserved Player 2 architecture  
**Authority:** [PROJECT_STATUS.md](../../PROJECT_STATUS.md) and [PLAYER_3_FINAL_AUDIT.md](../historical/PLAYER_3_FINAL_AUDIT.md)

## Purpose

Player 3 is a commercial-hardening increment, not a provider or playback rewrite. Its objective is to make the existing SamoTech boundaries more tolerant, diagnosable, and safe under malformed provider data, stale asynchronous work, bounded catalogue growth, and ordinary user-facing failures.

> The authoritative rule is preservation: provider adapters own provider protocols and credentials; application use cases own orchestration and safe DTOs; `PlayerShell` owns presentation behavior; `PlayerPort` owns playback operations; libVLC remains the sole playback backend.

## Preserved dependency direction

```text
Provider payloads and sessions
        ↓
Xtream/MAG/M3U infrastructure adapters and translators
        ↓
Canonical domain entities and capability-gated provider ports
        ↓
Application use cases and presentation-safe DTOs
        ↓
PlaybackTarget → ResolvedPlayback → PlayerPort
        ↓
VlcPlayerAdapter → libVLC
        ↓
PySide6 PlayerShell / native video surface
```

The UI does not import libVLC, construct provider URLs, access credentials, inspect provider payloads, or bypass `PlayerPort`. The Xtream adapter remains responsible for request construction and provider-specific stream resolution. The MAG adapter remains the owner of session state and live protocol interpretation.

## Player 3 hardening seams

| Seam | Player 3 behavior | Boundary preserved |
|---|---|---|
| Xtream catalogue translation | Malformed and duplicate live, VOD, Series, Season, and Episode records are skipped individually; valid records remain available. | Provider payload interpretation remains in infrastructure. |
| MAG capability declaration | `ProviderCapability.CATEGORIES` is advertised for the implemented live-category path. | No MAG VOD/Series/Episodes or catch-up capability is inferred. |
| EPG DTO mapping | Safe `description` and `category` values are retained; output is bounded at 500 entries. | Remote fetching, caching, and playback are not introduced. |
| Episode navigation | Previous/next controls use the current provider-scoped canonical episode list and existing playback use case. | UI never constructs a provider stream URL. |
| Backend state | Typed public player state maps to safe labels such as buffering and reconnecting. | UI does not infer state from libVLC internals. |
| History validation | Domain construction rejects `updated_at < started_at`. | Existing provider-scoped progress/resume contract remains authoritative. |
| Error taxonomy | Use cases map domain failures to stable credential-free user copy. | Raw provider/exception text does not cross into status feedback. |

## Concurrency and identity safety

Episode navigation and playback remain subject to provider/content/action generation guards. A completion from a previous provider, selected item, navigation context, or disposed owner is rejected before UI or playback mutation. The adjacent-episode action changes only the selected canonical item and schedules the same established application path; it does not create a second player or a parallel resolver.

The existing shared HTTP session and qasync task ownership remain intact. Qt-heavy test modules are validated in isolated invocations because cross-module offscreen Qt teardown can segfault even when each module passes independently; this is recorded as a test-environment limitation rather than hidden by a broad pass claim.

## Security boundary

Provider credentials and volatile session tokens remain in the credential store or adapter runtime. Resolved playback URLs remain ephemeral. The Player 3 changed-file scan found no authorized-provider literals or quoted secret assignments in source or documentation, and no credential-bearing values were added to tests or reports.

## Deliberate non-implementations

Catch-up/archive is not implemented because no current provider advertises `ProviderCapability.CATCHUP`. MAG VOD/Series/Episodes remain not executed because the authorized portal contract is unproven. Windows-native validation is not executed in the Linux environment. Populated authorized Xtream acceptance is not executed. No fake resume, fake track list, guessed transport capability, raw timeshift URL, or alternate backend was added to improve a status label.

## References

1. [ARCHITECTURE.md](../../ARCHITECTURE.md) — dependency direction and provider/player boundaries.
2. [PROJECT_STATUS.md](../../PROJECT_STATUS.md) — authoritative implementation and limitation matrix.
3. [docs/PLAYER_3_REAL_PROVIDER_ACCEPTANCE.md](PLAYER_3_REAL_PROVIDER_ACCEPTANCE.md) — credential-safe real-provider procedure.
4. [PLAYER_3_FINAL_AUDIT.md](../historical/PLAYER_3_FINAL_AUDIT.md) — complete evidence record.
