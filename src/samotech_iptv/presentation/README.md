# Presentation Layer

## Responsibility

The `presentation` package contains the Windows UI.  It uses the MVVM
pattern: ViewModels consume application use-cases and expose observable
properties; Views bind to ViewModels.

## Current status

PySide6 is the selected desktop toolkit. The first reusable widget is `VlcVideoSurface`, a Qt-native `QFrame` that owns a native window handle and attaches it only through the abstract `PlayerPort`. The presentation package does not import the concrete libVLC adapter, provider clients, credentials, or sessions.

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
- `VlcVideoSurface` provides the native video handle used by the sole libVLC backend; it must be shown before provider playback begins.
- Main window: channel list, player area, EPG panel.
- System-tray integration.

## Initial main-window composition

`MainWindow` hosts `VlcVideoSurface` as its central widget and receives an abstract `PlayerPort` plus the application `PlayChannel` use case. Its asynchronous `play_channel(channel_id)` method first ensures that the native Qt surface is attached, then delegates the channel identifier to application orchestration. It does not resolve provider streams directly or access provider credentials, tokens, sessions, or concrete infrastructure adapters.

## Desktop bootstrap

`samotech_iptv.desktop_bootstrap.build_desktop_application(play_channel, argv)` creates or reuses `QApplication`, constructs the sole libVLC `PlayerPort`, and returns a composed `MainWindow`. It intentionally accepts an already configured `PlayChannel` use case rather than constructing a provider, authenticating credentials, or starting the Qt event loop. Provider selection, credentials, and lifecycle remain a separate composition concern.

## Manual provider entry

The first manual-provider flow is Xtream. `XtreamProviderDialog` collects a provider ID, server URL, username, and password only long enough to submit `RegisterXtreamProviderRequest` to the application use case, then clears the password field. Registration crosses the `ProviderRegistrationPort`; infrastructure validates the profile, stores the credential through `CredentialStorePort`, and registers non-secret metadata only. M3U and MAG/Stalker forms will use the same registration boundary rather than storing provider secrets in widgets or profile metadata.
