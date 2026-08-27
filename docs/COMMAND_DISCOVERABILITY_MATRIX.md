# Command Discoverability Matrix

This matrix records where high-value commands are exposed in the current desktop application. It distinguishes intentional multiple entry points from duplicate implementations. It does not add menu entries merely because an internal use case exists.

| Command | Primary location | Secondary location | Keyboard path | Icon treatment | Current assessment |
|---|---|---|---|---|---|
| Add IPTV provider | Providers menu | Home/Providers management surface | Standard menu navigation; no dedicated shortcut | Text label; no bespoke icon | Discoverable; combined entry point intentionally complements protocol-specific forms |
| Add Xtream/M3U/MAG provider | Providers menu and combined Add dialog | Provider management workflow | Standard menu navigation | Text labels | Discoverable and capability-specific; do not merge away without usage evidence |
| Show registered providers | Providers menu | Home/Providers page | Standard menu navigation | Text label | Discoverable; safe summary and edit/remove/health actions |
| Browse channels | Providers menu | Live TV page | Select list then Enter/double-click | Text label | Discoverable; list activation is explicit |
| Load live channels | Live TV page | Home Live TV action when capability exists | No QAction shortcut | Text label with primary styling | Primary workflow is clear |
| Search loaded content | Top-bar search field | Search page | Return/selection path; no global shortcut | Text label/field | Scope is honest and local-only; no server-side search claim |
| Browse live categories | Live TV page | Providers menu/category dialog | Standard focus navigation | Text label | Intentional dual entry point; category dialog is browse-only |
| Show/configure EPG | Providers menu and selected-channel flow | XMLTV local-guide dialog | Standard focus navigation | Text label | Two paths are intentional: provider-native EPG and local XMLTV configuration |
| Favorites | Sidebar | Library menu and Home library page | Standard navigation | Text label or compact star glyph | Discoverable but dialog-mediated; direct rich library remains future work |
| History | Sidebar | Library menu and Home library page | Standard navigation | Text label or compact history glyph | Discoverable but dialog-mediated; clear-all requires destructive-action review |
| Pause/resume/stop | Player overlay | Playback menu | Evidence-backed player key handling; no QAction shortcut | Text labels | Intentional duplicate entry points; preserve mode gating |
| Seek/volume/mute/audio/subtitles/aspect | Player overlay | Context menus where supported | Slider/list keyboard navigation | Text labels | Visible and accessible; must remain disabled when unsupported by active mode/state |
| Start/stop recording | Playback menu | Player overlay/context where exposed | No dedicated shortcut | Text labels | Available through existing use case; no new recording workflow inferred |
| Playback diagnostics | Playback menu | Player overlay Info | No dedicated shortcut | Text label | Good dual entry point; sanitized report only |
| Settings | Menu bar action | Top-bar button, sidebar, Home context | Standard menu/focus navigation | Text label | Discoverable and direct |

## Findings

No `QAction.setShortcut`, `QShortcut`, or `QKeySequence` usage was found in the inspected presentation code. PlayerShell does implement a small evidence-backed key-handling path for Space, F, Escape, and mute-related behavior. The current menu and overlay duplication is intentional: menus support discoverability and keyboard/menu navigation, while the overlay supports immediate player use.

No `QAction.setIcon` or `QIcon` usage was found in the inspected presentation code, and `resources/icons` contains only `.gitkeep`. This phase therefore preserves visible text labels and compact glyphs rather than introducing an unreviewed icon family. Any future icon-only action must retain a tooltip and accessible name.

The highest-value discoverability work is not adding more commands. It is clarifying destructive actions, retaining capability-gated navigation, standardizing labels and spacing, and validating focus order across dialogs and compact navigation.
