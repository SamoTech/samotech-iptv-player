# Interface Segregation — Historical Phase B.0 Note

> **Historical scope:** This Phase B.0 design note is retained to explain the move toward capability-oriented provider ports. Its capability examples and migration statements are not the current support matrix; at the time of this note, M3U did not implement `PlaybackProvider`. Use [PROJECT_STATUS.md](../../PROJECT_STATUS.md) for verified current capability claims and [ARCHITECTURE.md](../../ARCHITECTURE.md) for current boundaries.


## Problem: The Monolithic ProviderPort

Phase A defined a single `ProviderPort` with seven methods covering
authentication, session management, catalogue loading, stream resolution,
and EPG retrieval.  This forces every provider to implement the full
surface, even if the underlying protocol only supports a subset.

For example:
- An **M3U provider** can load channels and resolve streams, but has no
  concept of authentication or EPG.
- A **Xtream provider** supports authentication and EPG but uses a
  different session model to MAG.

Forcing all providers to satisfy `ProviderPort` directly violates the
Interface Segregation Principle (ISP).

## Solution: Capability Interfaces

Phase B.0 introduces seven fine-grained interfaces in
`application/ports/provider_capabilities.py`:

| Interface | Methods | Implements |
|-----------|---------|------------|
| `AuthenticationProvider` | `authenticate`, `is_authenticated`, `provider_id` | MAG, Xtream |
| `SessionProvider` | `refresh_session` | MAG, Xtream |
| `CatalogProvider` | `load_channels` | MAG, Xtream, M3U |
| `EPGProvider` | `load_epg` | MAG, Xtream |
| `SearchProvider` | `search_channels` | MAG, Xtream |
| `PlaybackProvider` | `resolve_stream` | MAG, Xtream, M3U |
| `CapabilityProvider` | `supported_capabilities` | All |

## Capability Matrix (Planned)

```
                     MAG    Xtream   M3U
AuthenticationProvider  ✓      ✓      ✗
SessionProvider         ✓      ✓      ✗
CatalogProvider         ✓      ✓      ✓
EPGProvider             ✓      ✓      ✗
SearchProvider          ✓      ✓      ✗
PlaybackProvider        ✓      ✓      ✓
CapabilityProvider      ✓      ✓      ✓
```

## ProviderPort Compatibility

`ProviderPort` is retained as a convenience base class for providers that
implement all capabilities (currently MAG).  It does **not** extend the
capability interfaces; it remains a standalone ABC for the migration window.

Once all providers are migrated to capability interfaces, `ProviderPort`
will be deprecated and eventually removed.

## Use-Case Adaptation

Use-cases that previously depended on `ProviderPort` will migrate to the
minimum required capability:

```python
# Before
class LoadChannels:
    def __init__(self, provider: ProviderPort) -> None: ...

# After (Phase B.1)
class LoadChannels:
    def __init__(self, provider: CatalogProvider) -> None: ...
```

This makes use-cases testable with minimal stubs.
