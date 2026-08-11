# Ministra Compatibility Assessment

**Status:** Assessed on 2026-08-11

**Decision:** Design Ministra as a **separate provider adapter**. Do not implement it as an Xtream variant and do not reuse administrative REST credentials for subscriber playback.

## Scope and conclusion

Ministra is the renamed successor to Stalker Middleware, but its deployed portal behavior remains version- and device-dependent.[1] The repository's existing MAG adapter is useful as a reference for session ownership and canonical translation, while the Xtream adapter is useful as a reference for capability declarations and stateless request composition. Neither may be treated as a drop-in Ministra transport.

> **Architecture decision:** A future `MinistraProviderAdapter` should share only the stable domain entities, application capability interfaces, factory registration mechanism, error vocabulary, and HTTP abstractions. It must own its own credential interpretation, device identity, session/token lifecycle, device-facing portal routes, temporary link handling, and protocol DTO translation.

## Evidence summary

| Finding | Evidence | Architectural implication |
|---|---|---|
| Ministra is the renamed Stalker platform, with documentation and version history under both names. | The official platform page explicitly documents the name change and retains historical Stalker materials.[1] | Provider discovery should use an explicit `ministra` type; implementation diagnostics may mention both names, but routing must not guess protocol compatibility from branding alone. |
| The documented REST API v1 is an administrative API. It uses Basic HTTP authentication and includes STB/account management, subscriptions, messages/events, and IPTV channel resources.[2] | The API exposes mutating account and device operations, including STB and account resources.[2] | The player must **not** use that API as a content-client transport, must never send admin credentials through a media adapter, and must not perform account/device provisioning. |
| Device identity is part of the platform model. Documented STB/account fields include MAC address, serial number, and STB type.[2] | Device facts are stored and used at the platform layer.[2] | A Ministra credential boundary needs an explicit device identity model, validation, and redaction. Generic username/password alone is insufficient as a protocol design. |
| Historical changelogs contain repeated changes around authorization, access tokens, authorization keys, strict STB type checks, temporary URLs, EPG/archive handling, and secure playback links.[3] | These changes span authentication, catalogue, playback, and archive behavior.[3] | Token, cookie, user-agent/device headers, and time-limited resolved URLs must remain volatile infrastructure state. Capabilities must be advertised only after the adapter can execute them against the target portal. |

## Compatibility with the current architecture

| Existing boundary | Reuse | Ministra-specific implementation requirement |
|---|---|---|
| Domain entities (`Channel`, `Category`, `EPGEntry`, `Movie`, `Series`, `Stream`) | Yes | Translate all portal DTOs at the infrastructure boundary; do not expose portal payloads or opaque session state to application code. |
| Capability interfaces | Yes | Implement only capabilities verified against an authorized portal fixture. Likely initial candidates are authentication, live catalogue, EPG, category families, and stream resolution. VOD, series, archive, and catch-up remain capability-gated. |
| `ProviderFactory` registration | Yes | Register a distinct `ministra` provider type. Do not route a portal to `mag` or `xtream` based on URL shape. |
| Generic `Credential` input | Limited | Introduce a dedicated internal `MinistraCredential` value object that validates and redacts a MAC/device identity, optional device serial/type, and any portal-supported user secret. Do not persist access tokens, cookies, or resolved links. |
| MAG session ownership pattern | Conceptual only | Use a Ministra-specific client with explicit handshake/profile/session methods; preserve all tokens and cookies as private volatile state. |
| Xtream URL builder pattern | No transport reuse | Ministra playback may require a portal-issued temporary link; resolve it through the device-facing protocol instead of constructing a deterministic URL. |

## Recommended provider shape

```text
Application capability interfaces
              │
              ▼
MinistraProviderAdapter
  ├─ MinistraCredential (validated device identity; no token persistence)
  ├─ MinistraPortalClient (handshake, profile, catalogue, EPG, link resolution)
  ├─ MinistraDomainTranslator (portal DTO → canonical domain)
  └─ volatile session state (token/cookies/device headers only)
              │
              ▼
Shared AsyncHttpClient + ProviderFactory
```

The adapter should begin with a small feature slice rather than a broad emulator. Its first execution path should be: validate device identity, perform the portal handshake, load the authenticated profile, retrieve a live catalogue, and resolve exactly one authorized live channel into a playable URL. Catalogue categories and EPG should follow only after the first path has a stable fixture contract.

## Non-goals and safety boundaries

The implementation must not provision accounts, register devices, change subscriptions, send STB events, or invoke administrative REST resources. Those actions are out of scope for a player and can alter a provider account or device state.[2] It must also not scan portals, use unknown MAC addresses, or attempt to bypass device or subscription controls. Development and integration tests require an authorized test portal plus a provider-approved device identity.

## Implementation roadmap and decision gate

| Increment | Deliverable | Required evidence before merge |
|---|---|---|
| 1 | `MinistraCredential`, portal normalization, redaction tests | Authorized test portal URL and approved test MAC/device profile. |
| 2 | Handshake/profile client with private volatile session state | Captured, sanitized contract fixture from the authorized portal. |
| 3 | Live catalogue translator and `CatalogProvider` support | Fixture coverage for at least an empty, valid, and malformed response. |
| 4 | Secure temporary-link resolution and `PlaybackProvider` support | A verified resolvable live link, expiration behavior, and no credentials/tokens in logs. |
| 5 | EPG, categories, VOD, series, archive/catch-up | Each capability must be separately demonstrated and advertised only when executable. |

**Decision gate:** Do not start Ministra client code until an authorized, sanitized portal fixture and approved device identity are available. This prevents protocol guessing, protects provider accounts, and keeps the adapter's runtime capabilities truthful.

## References

[1] [Infomir — Ministra TV platform](https://wiki.infomir.eu/eng/ministra-tv-platform)

[2] [Infomir — REST API v1](https://wiki.infomir.eu/eng/ministra-tv-platform/ministra-setup-guide/rest-api-v1)

[3] [Infomir — Stalker Middleware 4.8 changelog](https://wiki.infomir.eu/eng/ministra-tv-platform/changelog/stalker-middleware-4-8)

[4] [External Stalker portal implementation reference](https://github.com/DimitarCC/iptv-m3u-reader/blob/main/src/StalkerProvider.py)
