# Internal API and Boundary Reference

SamoTech IPTV Player does not currently expose a stable public HTTP, plugin-marketplace, or command-line API. The supported interfaces in this repository are internal Python boundaries intended for the project’s Clean Architecture layers and tested composition work.

## Primary internal boundaries

| Boundary | Role |
|---|---|
| Domain entities/value objects | Canonical provider-independent IPTV records and validation. |
| Application ports | Abstract provider capabilities, player, credential, registration, resolution, catalog, storage, and theme-preference contracts. |
| Application use cases | Provider registration, registered-provider browse/search/play/EPG, favorites/history, recording, and theme preference orchestration. |
| Infrastructure adapters | M3U, Xtream Codes, MAG/Stalker, parsers, SQLite repositories, keyring store, libVLC player, and trusted local plugin loader. |
| Presentation contracts | PySide6 dialogs/views that invoke use cases and render safe DTOs. |
| Plugin SDK API v1 | Trusted explicitly selected local provider-plugin API; see [PLUGIN_SDK.md](PLUGIN_SDK.md). |

The executable status of these boundaries is maintained in [PROJECT_STATUS.md](../PROJECT_STATUS.md). `build_production_desktop_application()` now composes the existing safe state, provider, use-case, theme, and shared-player graph. The current product still has no supported command-line launcher or lifecycle owner; do not treat the composition, bootstrap, and runtime modules as a complete external API until startup/shutdown delivery is complete.

For architecture terminology and dependency direction, read [ARCHITECTURE.md](../ARCHITECTURE.md). For provider-specific and media support claims, use the authoritative capability matrices in [PROJECT_STATUS.md](../PROJECT_STATUS.md).
