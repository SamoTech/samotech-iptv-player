# Dependency Graph (Phase B.0)

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
