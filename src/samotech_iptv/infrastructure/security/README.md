# Infrastructure / Security

`KeyringCredentialStore` implements the application `CredentialStorePort` through the operating-system keyring. It stores, retrieves, deletes, and checks availability of provider credentials asynchronously without returning raw secret values outside the infrastructure boundary.

The credential boundary is used for Xtream account credentials, MAG device identity material, and sensitive tokenized M3U source strings. Non-secret provider metadata belongs in the SQLite metadata repository; session tokens/cookies remain private volatile state in live provider adapters.

Never log or persist provider passwords, MAC/device identities, tokens, tokenized URLs, resolved playback URLs, or local recording paths. The store surfaces generic storage errors rather than secrets. See [../../../../SECURITY.md](../../../../SECURITY.md) and [../../../../PROJECT_STATUS.md](../../../../PROJECT_STATUS.md).
