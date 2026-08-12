# Infrastructure / Configuration

`ConfigurationProvider` is the repository’s environment configuration boundary. It parses supported `IPTV_*` settings with explicit constructor override → environment → default precedence and supplies configuration used by infrastructure services such as MAG networking.

The current project does **not** implement the previously planned TOML configuration loader. Configuration files, production data-directory lifecycle, and a complete desktop startup configuration policy remain part of the Runnable Desktop Composition and Provider Lifecycle milestone.

Do not place provider credentials, MAC/device identities, tokens, secure M3U sources, or resolved playback URLs in environment examples, configuration files, logs, or persisted non-secret metadata. See [../../../../PROJECT_STATUS.md](../../../../PROJECT_STATUS.md) and [../../../../SECURITY.md](../../../../SECURITY.md).
