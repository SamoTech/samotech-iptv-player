# Core Layer

## Responsibility

The `core` package contains infrastructure-independent primitives that every
other layer may import.  It has **no** business logic and **no** external
dependencies beyond the Python standard library.

## Modules

| Module | Purpose |
|--------|---------|
| `config.py` | Application configuration dataclasses (read from env / file) |
| `constants.py` | Named constants shared across all layers |
| `logging.py` | Structured-logging factory (stdlib `logging` wrapper) |
| `exceptions.py` | Base exception hierarchy |
| `result.py` | `Result[T, E]` / `Ok` / `Err` — functional error handling |
| `events.py` | `DomainEvent` base dataclass |
| `typing.py` | Shared `TypeVar`, `Protocol`, `TypeAlias` definitions |

## Allowed Dependencies

```
core  →  stdlib only
```

## Forbidden Dependencies

- `domain`, `application`, `infrastructure`, `presentation`
- Any third-party library

## Future Guidance

- Add new primitives here only when they are genuinely cross-cutting.
- Keep every module < 150 lines.
- Never place business logic here; that belongs in `domain`.
