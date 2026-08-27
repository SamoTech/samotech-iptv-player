# Presentation Layer

## Responsibility

The `presentation` package provides the sole supported PySide6/Qt desktop interface. It invokes application use cases and renders presentation-safe DTOs; it does not resolve provider streams, access provider credentials, own sessions, import concrete provider clients, or import the libVLC adapter directly.

## Current components

| Component | Current responsibility |
|---|---|
| `views/MainWindow` | Hosts the native libVLC video surface; exposes provider-entry, provider-list, live-channel browsing, EPG, recording, and settings actions. |
| `widgets/VlcVideoSurface` | Owns a Qt native window handle and attaches it only through abstract `PlayerPort`. |
| Provider dialogs | Secure manual M3U, Xtream, and MAG/Stalker profile entry; fields clear sensitive input after submission. |
| Channel browser | Loads/searches registered-provider live channels, double-clicks playback, and adds a selected channel to favorites. |
| EPG grid | Displays provider EPG title/start/end data only. |
| Theme settings dialog | Loads/saves a non-secret system/light/dark preference and returns generic failure feedback. |
| Theme engine | Applies deterministic application-wide Qt stylesheets for system/light/dark preferences. |

## Dependency rules

```text
presentation → application use cases and DTOs
presentation → core utilities where required
```

Presentation must not import concrete infrastructure adapters or expose provider credentials, MAC identities, tokens, secure source URLs, resolved playback URLs, or provider protocol DTOs. User feedback for infrastructure failures must remain generic where detailed messages could reveal sensitive information.

## Playback and runtime

`MainWindow` attaches `VlcVideoSurface` before delegating playback to `PlayChannel` or `PlayRegisteredChannel`. The abstract player port is composed outside the presentation layer; **libVLC through `python-vlc` is the sole supported player backend**. `desktop_runtime.run_desktop_application()` supplies the qasync event loop for asynchronous Qt behavior.

The current bootstrap accepts externally composed use cases and an initial theme. No production composition root or executable launcher currently initializes repositories, restores provider metadata, builds the use-case graph, loads the persisted theme, starts the runtime, and closes resources. That lifecycle gap is the current roadmap milestone.

## Current UI limitations

The current UI focuses on registered-provider live channels. It has no complete VOD/movie/series/episode browsing, provider edit/remove flow, favorites/history management screens, XMLTV source setup, subtitle/audio controls, playback state UX, picture-in-picture, system-tray flow, packaging, or updater. See [../../../PROJECT_STATUS.md](../../../PROJECT_STATUS.md) and [../../../PRODUCT_GAP_ANALYSIS.md](../../../docs/historical/PRODUCT_GAP_ANALYSIS.md).
