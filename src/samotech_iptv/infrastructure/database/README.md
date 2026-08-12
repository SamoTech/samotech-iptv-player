# Infrastructure / Database

The database package provides SQLite-backed persistence for **non-secret** local state. Each repository uses standard-library `sqlite3` work performed off the asyncio event loop; the project does not currently use `aiosqlite`.

| Repository | Persisted data | Explicit exclusions |
|---|---|---|
| `SQLiteProviderMetadataRepository` | Provider ID/type, sanitized base URL, activation, advertised capabilities, and secure-source marker. | Credentials, MAC identifiers, tokens, resolved URLs, and provider error text. |
| `SQLiteFavoriteRepository` | Canonical favorite IDs, item IDs/types, and timestamps. | Credentials, provider session state, and stream URLs. |
| `SQLiteHistoryRepository` | Canonical item IDs/types, watched time, duration, and position. | Credentials, provider session state, and stream URLs. |
| `SQLiteThemePreferenceRepository` | One validated non-secret system/light/dark preference. | Provider data and user credentials. |

The production composition root initializes these repositories and restores provider metadata before creating the desktop shell. The supported source-install lifecycle invokes that root and closes the shared HTTP resource after the qasync window loop exits. Provider-management UI, richer library workflows, and packaging remain separate work. See [../../../../PROJECT_STATUS.md](../../../../PROJECT_STATUS.md) and [../../../../ROADMAP.md](../../../../ROADMAP.md).
