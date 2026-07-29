# Dependency Graph

## Allowed Dependency Direction

```
┌─────────────────────────────────────────────────────┐
│                    Presentation                     │
│           (views, viewmodels, dialogs)              │
└────────────────────────┬────────────────────────────┘
                         │ depends on
                         ▼
┌─────────────────────────────────────────────────────┐
│                    Application                      │
│              (ports, use-cases, DTOs)               │
└──────────┬──────────────────────────────────────────┘
           │ depends on
           ▼
┌─────────────────────────────────────────────────────┐
│                      Domain                         │
│         (entities, value objects, repos)            │
└──────────┬──────────────────────────────────────────┘
           │ depends on
           ▼
┌─────────────────────────────────────────────────────┐
│                       Core                          │
│      (config, logging, exceptions, result)          │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│                  Infrastructure                     │
│      (providers, database, network, security)       │
└──────────┬──────────────────────────────────────────┘
           │ implements ports defined in
           ▼
       Application  →  Domain  →  Core
```

## Forbidden Arrows

| From | To | Reason |
|------|----|--------|
| `domain` | `infrastructure` | Domain must be framework-free |
| `domain` | `application` | Domain has no knowledge of use-cases |
| `domain` | `presentation` | Domain has no knowledge of UI |
| `application` | `infrastructure` | Use-cases depend only on ports (interfaces) |
| `application` | `presentation` | Application has no knowledge of UI |
| `core` | Anything | Core is the foundation — zero upward deps |
| `infrastructure` | `presentation` | I/O layer has no knowledge of UI |

## Infrastructure → Application Direction

Infrastructure **implements** application ports, so it imports application
interfaces.  This is the Dependency Inversion Principle in action: the
high-level policy (application) defines the interface; the low-level detail
(infrastructure) satisfies it.

## Circular Import Prevention

- Each layer's `__init__.py` imports only from **within its own package** or
  from **lower layers**.
- Infrastructure sub-packages (`providers/`, `database/`, etc.) do not import
  from each other at Phase A; shared utilities go into `infrastructure/network/`.
- Use `TYPE_CHECKING` blocks for forward-reference type hints that would
  otherwise create circular imports.
