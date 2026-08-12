# Dependency Graph — Historical Phase B.0 Note

> **Historical scope:** This diagram records the Phase B.0 architecture snapshot. The current dependency rule, provider terminology, player policy, and lifecycle limitation are defined in [ARCHITECTURE.md](../../ARCHITECTURE.md). Current implementation status is in [PROJECT_STATUS.md](../../PROJECT_STATUS.md).


## Allowed Direction

```
┌─────────────────────────────────────────────────────┐
│               Presentation (Phase D)                │
└────────────────────────┬────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│     Application: ports/ dtos/ use_cases/            │
└──────────┬──────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────┐
│     Domain: entities/ value_objects/ repos/ events/ │
└──────────┬──────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────┐
│     Core: config / logging / exceptions / result    │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Infrastructure: providers/ db/ network/ security/  │
└──────────┬──────────────────────────────────────────┘
           │ implements ports in
           ▼
       Application  →  Domain  →  Core
```

## New in Phase B.0: ISP Layer

Within Application, use-cases now pick the minimum interface:

```
LoadChannels    →  CatalogProvider
LoadEPG         →  EPGProvider
ResolveStream   →  PlaybackProvider
Authenticate    →  AuthenticationProvider + CredentialStorePort
RefreshSession  →  SessionProvider
```

## Forbidden Arrows (Unchanged)

| From | To |
|------|----|
| `domain` | `infrastructure` / `application` / `presentation` |
| `application` | `infrastructure` / `presentation` |
| `core` | Anything |
| `infrastructure` | `presentation` |
