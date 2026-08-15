# Infrastructure / Providers

This package implements the provider boundary: provider-specific credentials, sessions, payloads, and remote operations stay in infrastructure and are translated into canonical domain records before application use cases see them.

| Provider/service | Current status | Verified behavior |
|---|---|---|
| `M3UProviderAdapter` | Partially implemented | Secure local/file/HTTP(S) source loading, extended-M3U parsing, canonical live catalogue/search, and parsed HTTP(S) stream resolution through `PlaybackProvider`. Non-HTTP(S) transports remain outside the current player URL boundary. |
| `XtreamProviderAdapter` | Partially implemented | Authentication; live, category-family, VOD/movie, series, short-EPG, local search, and live stream-resolution methods. It does not implement or advertise the provider-neutral Movie-resolution, Series-detail, or Episode-resolution contracts. |
| `MagProviderAdapter` | Partially implemented | Authorized MAC identity handling, private session lifecycle, live catalogue, local search, EPG, and live stream resolution through the legacy MAG provider implementation. |
| `ProviderRegistrationService` | Implemented | Secure M3U/Xtream/MAG registration, non-secret metadata persistence, and keyring-owned secrets. |
| `ProviderCatalogService` / `ProviderResolutionService` | Implemented | Credential-safe listing and capability-specific construction of registered providers. |
| `ProviderFactory` / `ProviderRegistry` / `ProviderContext` | Implemented | Explicit adapter registration, safe metadata registry, and host-owned construction context. |
| Ministra | Planned | A separate-adapter design is assessed but no runtime client exists; implementation is gated on authorized sanitized fixtures and approved device identity. |

Provider capabilities must be advertised only when executable. Categories, VOD browsing, Series browsing, Movie playback, Series detail, Episode playback, EPG, catch-up, and Live playback are independent capabilities—not generic provider promises. Never expose provider DTOs, credentials, MAC addresses, session tokens, secure source URLs, or resolved playback URLs outside the infrastructure boundary.

The repository-root `providers/` package remains the legacy MAG protocol implementation used behind `MagProviderAdapter`. See [../../../../PROJECT_STATUS.md](../../../../PROJECT_STATUS.md), [../../../../ARCHITECTURE.md](../../../../ARCHITECTURE.md), and [../../../../MINISTRA_COMPATIBILITY_ASSESSMENT.md](../../../../MINISTRA_COMPATIBILITY_ASSESSMENT.md).
