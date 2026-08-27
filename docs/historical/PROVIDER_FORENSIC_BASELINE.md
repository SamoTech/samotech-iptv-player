# Provider Forensic Baseline

**Repository:** SamoTech IPTV Player  
**Baseline commit:** `cc9f0c1bc49187e2d35e84b7420e7d0c1440f16b`  
**Baseline branch:** `main`  
**Scope:** Xtream Codes and MAG/Stalker provider acceptance, with the desktop UI as the presentation boundary.

## Evidence rules

This baseline distinguishes documentation, executable implementation, deterministic tests, integration tests, and authorized real-runtime evidence. A synthetic response or HTTP success is not treated as playback or provider compatibility proof.

## Architecture trace

The provider path is:

```text
Provider registration
    → secure credential store and non-secret metadata repository
    → ProviderFactory and ProviderContentResolverPort
    → provider adapter
    → provider-specific DTO validation and translator
    → canonical domain entities
    → application use cases and typed ports
    → PlaybackTarget / ResolvedPlayback
    → PlayerPort and shared libVLC adapter
    → PySide6 presentation
```

Xtream uses `XtreamRequestBuilder`, `XtreamApiClient`, `XtreamDomainTranslator`, and `XtreamProviderAdapter`. MAG/Stalker uses `MagCredential`, `MagProviderAdapter`, a legacy provider facade from `providers.mag`, and `MagDomainTranslator`. The presentation layer receives safe summaries and canonical records; it does not construct credential-bearing URLs or read secrets.

## Role-separated review team

The review was organized into dependency-ordered roles: Lead Architect; UI/UX Designer; Graphic & Icon Designer; Qt/PySide6 UI Engineer; Xtream Protocol Specialist; MAG/Stalker Protocol Specialist; IPTV Data Model Engineer; Playback Integration Engineer; Security Engineer; QA Engineer; Windows Packaging Engineer; Performance Engineer; Accessibility Reviewer; Independent Challenger; and Final Auditor. In this single-agent execution, each role is an explicit review lens and no role’s conclusion is treated as evidence for another role.

## Provider evidence matrix

| Provider | Documented | Implemented | Unit tested | Integration tested | Runtime verified | Not verified | Blocked |
|---|---|---|---|---|---|---|---|
| Xtream Codes | Yes: request builder, supported actions, canonical adapter capabilities, provider status documents | Yes, partially: authentication, account/server metadata, Live/VOD/Series categories and records, Movie details, Seasons/Episodes, short EPG, local search, and supported stream URL resolution | Yes: request builder, API client, translator, adapter, malformed/duplicate records, realistic response variations | Yes in-process: adapter and application/use-case paths use deterministic HTTP and credential-store doubles | **No authorized populated provider run available** | Real portal compatibility, populated non-live catalogue, server-specific quirks, and native playback | Authorized credentials and a populated real provider are unavailable; native media playback remains a separate gate |
| MAG/Stalker | Yes: adapter documents a bounded legacy compatibility profile, session lifecycle, and supported capabilities | Yes, partially: authorized MAC identity, bounded discovery delegated to legacy provider, session token lifecycle, Live channels, local search, EPG, and live stream resolution | Yes: credential conversion, authentication, session refresh/close, reauthentication, translation, capability declaration, error mapping | Yes in-process: adapter and application integration use a deterministic legacy-provider double | **No authorized production portal handshake or stream handoff available** | Portal-generation compatibility, production endpoint routing, VOD, Series, archive/catch-up, and native playback | Authorized portal fixture and approved device identity are unavailable; legacy profile may not match every portal |

## Xtream audit

| Requirement | Classification | Evidence and boundary |
|---|---|---|
| Server URL, HTTP/HTTPS, port handling, path normalization | Implemented and tested | `URL` validates HTTP(S), `XtreamRequestBuilder` preserves host/port and a service path, and request-builder tests cover generated endpoints. |
| Malformed URL rejection and timeout handling | Implemented and tested | Canonical URL validation and shared asynchronous HTTP timeout/error boundaries are covered. No real network acceptance is implied. |
| Username/password authentication | Implemented and tested | `player_api.php` authentication response is normalized; credentials are stored only through the credential store after success. |
| Authentication failure, 401/403/404, timeout | Implemented at error boundary; deterministic tested | The shared HTTP client translates transport/status failures; adapter tests cover failure contracts. No authorized server was contacted for this phase. |
| Account status, expiration, created date, trial, active/max connections | Partially implemented and tested | Account translator accepts available `user_info` fields and preserves unknown values as unavailable. Field availability is provider-dependent. |
| Server URL, hostname, protocol, timezone, timestamp, version, message | Partially implemented and tested | Server translator maps available server metadata. Missing provider fields are not fabricated. |
| Live categories and streams | Implemented and tested | `get_live_categories` and `get_live_streams` flow through canonical category/channel translation with malformed and duplicate records skipped. |
| VOD categories and streams | Implemented and tested synthetically | VOD list/detail translation and local presentation paths exist. Populated authorized catalogue acceptance is not verified. |
| Series categories, metadata, seasons, episodes | Implemented and tested synthetically | Series detail, season/episode translation, identity ownership, and episode resolution are covered. Series containers are not themselves playable. |
| EPG | Implemented and tested synthetically | Short EPG is validated and translated into canonical entries. No real-provider EPG acceptance is established. |
| Live, VOD, and episode stream resolution | Implemented and tested synthetically | URLs are constructed through the request builder and returned as `ResolvedPlayback`. This proves provider resolution only, not media decoding. |
| Provider-to-UI normalization | Implemented and tested synthetically | DTOs become canonical records, application DTOs, and model-backed presentation data. |
| Provider-to-playback handoff | Implemented and tested synthetically | `PlaybackTarget`/`ResolvedPlayback` cross the provider-neutral player boundary. Native playback remains unverified. |

**Xtream real-server acceptance:** **NOT VERIFIED.** No unauthorized probing or random IPTV service testing was performed.

## MAG/Stalker audit

The current implementation is a provider-specific compatibility adapter around a legacy MAG facade. It is not treated as equivalent to Xtream. The adapter keeps the MAC identity and portal URL inside the credential/session boundary, holds the session token in volatile state, translates legacy errors, retries once after session expiry, and exposes only the declared Live/EPG/search/session capabilities.

| Requirement | Classification | Evidence and boundary |
|---|---|---|
| Portal URL normalization | Implemented and tested | Canonical HTTP(S) URL validation and `MagCredential` conversion are covered. |
| Device identity and MAC handling | Implemented and tested | The application credential is converted to the MAG identity boundary; the identity is not stored in provider metadata or normal logs. |
| Handshake/authentication | Implemented and tested with deterministic facade | `connect()` must establish a non-empty session token; failures are translated to safe authentication errors. No production portal handshake was obtained. |
| Token/session lifecycle | Implemented and tested | Authentication, refresh, close, session-expiry reauthentication, and owned-resource cleanup are covered. |
| Profile/account/capabilities | Partially implemented | Session state and declared capability truth exist. Account/profile fields from a production portal are not normalized by the current adapter. |
| Live categories/channels | Live channels implemented and tested; categories provider-dependent | Channel translation and local search are covered. Category loading requires the legacy facade’s explicit support flag. |
| EPG | Implemented and tested synthetically | Channel-scoped EPG retrieval and timestamp validation are covered. |
| VOD, Series, archive/catch-up | Unsupported by current adapter contract | No executable capability is advertised and no claim is made. |
| Live stream resolution | Implemented and tested synthetically | Numeric channel identity is validated, the legacy facade returns a URL, and `ResolvedPlayback` is produced. Native playback is not proven. |
| Security | Implemented and tested | Tokens remain volatile; MACs, cookies, authorization headers, and credential-bearing URLs are not intended for logs or UI. |

**MAG/Stalker classification:** **IMPLEMENTED AND TESTED** for the deterministic Live/session/EPG subset; **PARTIALLY IMPLEMENTED** as a provider overall; **BLOCKED BY AUTHORIZED FIXTURE AVAILABILITY** for production-portal acceptance.

## UI/provider boundary baseline

Provider setup currently offers explicit M3U, Xtream, and MAG/Stalker flows. Smart Import performs local bounded detection and masks secrets in its preview; it does not probe arbitrary servers. Registration stores non-secret metadata separately from credentials. Before this phase, setup forms had minimal labels and validation, no transient visibility controls, and post-save feedback could imply readiness before authentication or catalogue loading.

The UI must therefore distinguish these states: configuration saved; session not yet established; session authenticated; authentication failed; catalogue available; catalogue empty; provider error; and unknown/not available. A registered configuration alone is never evidence of connection or catalogue availability.

## Baseline security and runtime evidence

No authorized credentials, production MAC addresses, provider tokens, cookies, private stream URLs, or raw production payloads were used. Deterministic fixtures use synthetic domains and identities. Linux/offscreen Qt tests and Windows CI contracts do not establish populated real-provider compatibility or native playback on a consumer machine.

## Baseline decision

Xtream is **partially implemented and deterministically tested**, but real-server acceptance is **not verified**. MAG/Stalker is **partially implemented**, with deterministic Live/session/EPG coverage, but production-portal acceptance is **blocked by the absence of an authorized fixture**. Any stronger claim would exceed the evidence.
