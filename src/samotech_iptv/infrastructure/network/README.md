# Infrastructure / Network

The network package provides the shared asynchronous HTTP boundary used by provider adapters and secure remote M3U source loading. It supplies the `AsyncHttpClient` abstraction and safe network error translation used by infrastructure code; application and presentation layers do not perform provider HTTP requests directly.

Configuration determines supported network settings such as timeouts, retry limits, and TLS verification. Provider adapters remain responsible for their own protocol request construction, credentials, session ownership, payload translation, and capability advertisement.

Network diagnostics must not log credentials, MAC identities, session tokens, tokenized source URLs, or resolved playback URLs. See [../../../../SECURITY.md](../../../../SECURITY.md) and [../../../../ARCHITECTURE.md](../../../../ARCHITECTURE.md).
