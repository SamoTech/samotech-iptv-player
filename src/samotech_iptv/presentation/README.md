# Presentation Layer

## Responsibility

The `presentation` package contains the Windows UI.  It uses the MVVM
pattern: ViewModels consume application use-cases and expose observable
properties; Views bind to ViewModels.

## Phase A Status

Empty scaffold.  No PySide6 or WinUI code yet.

## Sub-packages

| Package | Contents |
|---------|----------|
| `views/` | Top-level window and page classes |
| `dialogs/` | Modal dialog classes |
| `viewmodels/` | ViewModel classes (data binding, commands) |
| `widgets/` | Reusable custom widgets |
| `theme/` | Colour palette, fonts, style sheets |

## Allowed Dependencies

```
presentation  →  application (use-cases, DTOs)
presentation  →  core
```

## Forbidden

- `domain` (use DTOs, never raw entities)
- `infrastructure`

## Phase D Plan

- PySide6 ViewModels with `QProperty` / `Signal` bindings.
- Main window: channel list, player area, EPG panel.
- System-tray integration.
