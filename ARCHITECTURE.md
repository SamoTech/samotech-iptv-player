# Architecture

SamoTech IPTV Player follows **Clean Architecture** (Robert C. Martin).

## The Dependency Rule

Source code dependencies must point **inward only**:

```
[Presentation] → [Application] → [Domain]
      ↓                ↓
[Infrastructure] implements [Application Ports]
[Core] used by all layers
[Plugins] extend via SDK interfaces
```

The **Domain** layer has zero imports from Qt, aiohttp, vlc, or sqlite3.
This allows swapping VLC for MPV or Qt for a web frontend with zero business logic changes.

## Layers

| Layer | Package | Responsibility |
|---|---|---|
| Core | `samotech_iptv.core` | Shared primitives (Result monad, EventBus, logging) |
| Domain | `samotech_iptv.domain` | Entities, value objects, repo interfaces, pure services |
| Application | `samotech_iptv.application` | Use cases, DTOs, abstract I/O ports |
| Infrastructure | `samotech_iptv.infrastructure` | VLC, aiohttp, SQLite, Keychain adapters |
| Presentation | `samotech_iptv.presentation` | PySide6 MVVM UI, DI container wiring |
| Plugins | `samotech_iptv.plugins` | Plugin SDK host and loader |

## Dependency Injection

`presentation/app.py` is the single composition root. All concrete dependencies are
wired once at boot; every use case receives its dependencies through constructor injection.

## Security Model

- Credentials → Windows Credential Manager (keyring, WinCred backend)
- All URLs → `url_sanitizer.py` before passing to VLC (prevents SSRF)
- Input validation → Pydantic v2 validators on all DTO boundaries
- No `eval()`, `exec()`, or `pickle` deserialization

## Plugin Sandboxing

Plugins are loaded into restricted `importlib` namespaces and may only call
methods on the `IPlugin` SDK interfaces. A capability-token model restricts
what each plugin can access at runtime.
