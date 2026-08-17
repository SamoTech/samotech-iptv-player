# Architecture Audit

## Executive result

**Architecture: PASS, with a documented transitional legacy-provider boundary.** The repository implements a clear hexagonal/ports-and-adapters desktop architecture. The domain is infrastructure-independent; application use cases depend on ports; infrastructure contains concrete HTTP, keyring, SQLite, provider, parser, and VLC adapters; presentation composes these parts and owns Qt task lifecycles.

An AST import graph covered 243 modules and found zero circular dependencies and zero forbidden reverse-layer edges. The audit did not find a confirmed dependency inversion violation, hidden singleton that controls application behavior, or generic application code containing provider-specific protocol logic.

## Layer map

| Layer | Responsibilities | Audit result |
|---|---|---|
| Domain | Entities, value objects, invariants, repository contracts, provider-independent types. | PASS; no infrastructure imports. |
| Application | Use cases, DTOs, ports, stale-operation guards, safe error boundaries. | PASS; async cancellation and generation checks are explicit. |
| Infrastructure | aiohttp, keyring, SQLite, M3U/XMLTV, Xtream, MAG, VLC implementations. | PASS; adapters implement application ports. |
| Presentation | PySide6 widgets/dialogs, PlayerShell, task ownership, qasync integration. | PASS; no blocking provider work on GUI path. |
| Composition | Desktop wiring, provider runtime cache, shutdown order, packaged runtime. | PASS; lifecycle is explicit and awaited. |

## Canonical and legacy providers

The canonical implementation is `src/samotech_iptv/infrastructure/providers`. The legacy implementation is the top-level `providers/` package. The legacy package cannot currently be removed safely: `src/samotech_iptv/infrastructure/providers/mag_adapter.py` lazily imports `providers.mag.provider.MAGProvider`, and the compatibility object remains the runtime MAG implementation behind the canonical adapter. The PyInstaller spec explicitly includes both package trees and collects legacy provider submodules.

The migration boundary is narrow rather than duplicated throughout the application. Canonical code owns provider metadata, credentials, application ports, error translation, and lifecycle composition. The legacy MAG code owns protocol-specific session/connection/profile compatibility behavior. No circular import was found. The boundary is covered by MAG adapter and legacy transport tests, and the reason for retaining it is documented in the package and packaging configuration.

| Question | Evidence-based answer |
|---|---|
| Which implementation is canonical? | `src/samotech_iptv` and its infrastructure provider adapters. |
| Which is legacy? | Top-level `providers/`, especially legacy MAG/Stalker protocol code. |
| Is legacy executed? | Yes, through lazy `MAGProvider` import from `mag_adapter`. |
| Is legacy packaged? | Yes, via setuptools package discovery and PyInstaller hidden imports/submodule collection. |
| Can it be deleted now? | No; doing so would break MAG runtime resolution. |
| Is behavior duplicated? | Some protocol concerns overlap, but the compatibility boundary is explicit and not a general duplicate application architecture. |

## Dependency and security boundaries

Credential values enter through application registration DTOs, become domain `Credential` objects, and cross into infrastructure only through the credential-store/provider ports. Provider metadata excludes secrets. The database repositories persist non-secret identities and capability information. URL-bearing provider data is sanitized at log and exception boundaries. The player port receives resolved playback targets without making the domain depend on VLC.

The network client is shared through desktop composition. Provider adapters do not construct independent aiohttp sessions for ordinary operations. The provider runtime cache owns live provider instances and closes stale or removed instances. Desktop shutdown first awaits UI task owners, then provider runtime cache, then player, then shared HTTP resources.

## Persistence architecture

SQLite repositories use one connection per operation in a worker thread. The connection context manager commits successful operations, rolls back exceptions, and closes in all paths. Repositories use parameterized SQL. Foreign keys are enabled for XMLTV mappings. Migrations are additive and limited to known schema fields. No repository stores password, MAC, session-token, cookie, or authorization-header fields.

## Player architecture

`VlcPlayerAdapter` implements the player port and isolates native python-vlc objects. A state machine tracks typed playback state, media generation, and session token. Native callbacks are annotated with the generation/session captured at subscription time and are ignored if stale. PlayerShell talks through ports and application orchestration rather than embedding provider protocol logic. The Qt video surface owns only the native widget binding.

## Findings and recommendations

The principal architecture finding is not a defect but a migration condition: the repository has one canonical application architecture with a legacy MAG protocol island. Removing that island requires a deliberate protocol migration, replacement of its tests, and a packaged Windows validation cycle. The current audit therefore classifies this as **CONDITIONAL architecture maturity**, not as a runtime failure.

A future migration should preserve the keyring flow, safe exception taxonomy, transport limits, and native lifecycle contracts. It should not be performed as a blind package deletion or cosmetic namespace rewrite.

## References

[1]: build/import_graph.json "AST import graph evidence"
[2]: build/legacy_provider_trace.txt "Canonical and legacy provider trace"
[3]: src/samotech_iptv/infrastructure/providers/mag_adapter.py "Canonical MAG compatibility boundary"
[4]: providers/mag/provider.py "Legacy MAG provider"
[5]: samotech-iptv-player.spec "PyInstaller package inclusion"
[6]: src/samotech_iptv/desktop_composition.py "Runtime composition and shutdown"
[7]: src/samotech_iptv/infrastructure/database/sqlite_connection.py "SQLite operation lifecycle"
