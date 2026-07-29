# Application Layer

## Responsibility

The `application` package orchestrates use-cases.  It translates
incoming requests (from the presentation layer or external callers)
into domain operations and delegates I/O to infrastructure through
port interfaces.

## Rules

- **Depends only on interfaces** — never on concrete infrastructure.
- **No I/O** — all I/O is delegated through ports.
- **DTOs cross the boundary** — domain entities never leave this layer;
  DTOs (Request/Response) are what the presentation layer receives.

## Modules

| Module | Contents |
|--------|----------|
| `ports.py` | `ProviderPort`, `PlayerPort`, `StoragePort`, `CredentialStorePort`, `NotificationPort` |
| `use_cases/` | One class per use-case |
| `dtos.py` | `ProviderMetadata`, `ProviderCapabilities`, request/response DTOs |

## Allowed Dependencies

```
application  →  domain
application  →  core
application  →  stdlib
```

## Forbidden

- `infrastructure`, `presentation`
- Direct instantiation of repository implementations
- `aiohttp`, `SQLite`, `keyring`

## Future Guidance

- Each use-case should be a class with a single `async def execute(request)` method.
- Raise `core.exceptions.*` on validation failures; let infrastructure
  exceptions propagate wrapped in `core.exceptions.ProviderError`.
- Emit `domain.events.*` after successful state changes.
