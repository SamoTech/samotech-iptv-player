# Next Phase Provider and UI Audit

**Project:** SamoTech IPTV Player  
**Baseline commit:** `cc9f0c1bc49187e2d35e84b7420e7d0c1440f16b`  
**Release candidate:** `0.1.7`  
**Status:** Local and hosted blocking gates passed; the release decision is patch release recommended.

## 1. Baseline and evidence policy

The audit began from a clean working tree at the baseline commit above. Evidence is classified separately as documented, implemented, unit tested, integration tested, runtime verified, not verified, or blocked. Deterministic fakes, HTTP 200 responses, catalogue object creation, or URL construction are not treated as proof of provider compatibility or media playback.

The full baseline classification is recorded in [`PROVIDER_FORENSIC_BASELINE.md`](../historical/PROVIDER_FORENSIC_BASELINE.md).

## 2. Provider architecture

The provider chain is registration → secure credential storage and non-secret metadata → `ProviderFactory` → provider adapter → protocol DTO validation and translation → canonical domain entities → application use cases and typed ports → `PlaybackTarget`/`ResolvedPlayback` → `PlayerPort` → shared libVLC → PySide6 presentation.

Xtream is implemented through `XtreamRequestBuilder`, `XtreamApiClient`, `XtreamDomainTranslator`, and `XtreamProviderAdapter`. MAG/Stalker is implemented through `MagCredential`, `MagProviderAdapter`, the legacy `providers.mag` facade, and `MagDomainTranslator`. Provider DTOs and credentials do not cross into the presentation layer.

## 3. Xtream audit and evidence matrix

| Capability | Classification | Evidence | Boundary |
|---|---|---|---|
| URL, HTTP(S), ports, normalization, malformed URL rejection | Implemented and tested | Canonical URL object, request-builder tests, adapter tests | No real server was contacted in this phase. |
| Authentication and credential storage | Implemented and tested | Deterministic `player_api.php` responses and credential-store doubles | No authorized credential acceptance is available. |
| Account and server information | Implemented and tested synthetically | Translators map available status, expiration, connection, protocol, version, and related fields | Missing provider fields remain unavailable; fields are not fabricated. |
| Live categories and channels | Implemented and tested | API client, translator, adapter, application, and UI-model coverage | Populated real-provider acceptance is not verified. |
| VOD and Movie details | Implemented and tested synthetically | Catalogue/detail translation, capability gating, local presentation flow, and stream resolution tests | Real populated VOD acceptance is not verified. |
| Series, Seasons, Episodes | Implemented and tested synthetically | Detail translation, generation-safe navigation, episode resolution, and application tests | Series containers remain non-playable; real populated acceptance is not verified. |
| EPG | Implemented and tested synthetically | Short-EPG validation and canonical translation tests | Real-provider EPG acceptance is not verified. |
| Live/VOD/Episode stream resolution | Implemented and tested synthetically | Request builder and `ResolvedPlayback` tests | Provider URL resolution is not media-decoder or native playback verification. |
| Full real-server acceptance | **Not verified / blocked** | No authorized populated server fixture was available | No random or unauthorized provider probing was performed. |

## 4. MAG/Stalker audit and evidence matrix

The current adapter is a provider-specific legacy compatibility profile, not an Xtream equivalent. It supports an authorized MAC identity, bounded handshake discovery in the legacy implementation, volatile session state, refresh and close, Live channels, local search, EPG, and live stream resolution.

| Capability | Classification | Evidence | Boundary |
|---|---|---|---|
| Portal URL and identity handling | Implemented and tested | URL validation, `MagCredential`, and deterministic adapter tests | No production portal was contacted. |
| Authentication and handshake | Implemented and tested with deterministic facade | Non-empty session token is required; failures are translated safely | No authorized production handshake was obtained. |
| Token/session lifecycle | Implemented and tested | Refresh, close, session expiry, one-time reauthentication, and cleanup tests | Token-bearing production behavior remains unverified. |
| Live channels and local search | Implemented and tested synthetically | Legacy-provider double, canonical translation, and application integration tests | No populated authorized portal catalogue acceptance. |
| EPG | Implemented and tested synthetically | Channel-scoped retrieval and timestamp validation tests | No production EPG acceptance. |
| Live stream resolution | Implemented and tested synthetically | Numeric identity validation and `ResolvedPlayback` tests | Native libVLC playback is not verified. |
| Account/profile fields | Partially implemented | Session state and capability truth exist | No general account/profile normalization contract is established. |
| VOD, Series, archive, catch-up | Unsupported | No executable capabilities are advertised | Do not expose or claim these workflows. |
| Full production acceptance | **Not verified / blocked** | Authorized portal and approved identity are unavailable | No random scanning or unauthorized credentials. |

## 5. Implemented provider fixes and UX safeguards

The Xtream setup form now validates the canonical HTTP(S) URL before registration, provides protocol-specific guidance and placeholders, supports transient password reveal, disables duplicate submission while saving, and clears the password after submission or failure. The MAG/Stalker form provides the same treatment for the portal URL and transient device-identity reveal while explicitly stating that the current client supports the provider’s Live-TV profile only.

Registration success no longer implies that a provider is connected or ready. The main window now reports that a provider was saved and must be selected and loaded to establish a session. Provider management labels its user-initiated action as **Check Session Status**, clearly stating that it does not load a catalogue. Existing health-state vocabulary remains conservative and does not fabricate expired, disabled, connected, or catalogue-available states.

No automatic provider scanner, proxy, credential forwarder, CORS relay, aggressive probing, or new provider request was introduced.

## 6. UI/UX audit and changes

| Surface | Improvement | Evidence boundary |
|---|---|---|
| Provider setup | Clear help copy, protocol-relevant fields, placeholders, canonical URL validation, busy/save state, transient secret visibility, and safe secret clearing | Registration and validation remain application-bound; no automatic connection probe is introduced. |
| Provider management | Wider dialog, clearer session-status wording, safe provider summary, and visually distinct destructive removal action | The session status action reads adapter state; it is not a catalogue probe. |
| Dialog visual system | Shared token-based dark form style with focus, disabled, primary, destructive, help, and status treatments | Reuses existing theme tokens; no unlicensed assets were added. |
| Main shell status | Removed unconditional post-save “Ready” implication | Provider readiness is now established only by later provider/session/content actions. |
| Sidebar | Collapsed navigation retains compact glyphs but now exposes full section names through item tooltips; toggle text and accessible name remain explicit | Navigation behavior and remembered sidebar state are unchanged. |
| Main window and player | Existing player-first hierarchy, shared video surface, status bar, content cards, local search, loading/empty/error states, and keyboard playback behavior are preserved | No provider or `PlayerPort` architecture change. |

## 7. Icon audit

Visible action controls were reviewed for action labels, tooltips, accessible names, and destructive differentiation. Existing controls use text labels or accessible names; the collapsed sidebar uses a small consistent glyph vocabulary and now supplies full section tooltips. The new provider-management removal action is visually distinct through a danger token.

No external icon pack or unlicensed asset was introduced. A future visual pass may replace the remaining text glyphs with a bundled, licensed icon set, but that is not required for this increment and is not claimed as complete here.

## 8. Screens changed

The changed screens are the Xtream provider setup dialog, MAG/Stalker provider setup dialog, registered-provider management dialog, main-window post-registration status flow, and the shared compact-dialog style. The broader PlayerShell remains within the existing design system; its collapsed navigation now exposes tooltips for discoverability.

## 9. Accessibility

The provider fields and reveal controls have explicit accessible names, tooltips, keyboard-focusable controls, and visible focus styling. Save and cancel actions are labeled, secret fields remain masked by default, and transient reveal controls do not persist secret values. Existing PlayerShell tab order, Enter/Space/Escape handling, fullscreen keyboard behavior, and native player controls were not changed.

## 10. Performance

The setup improvements add only local validation and UI state changes. They do not add provider requests, duplicate catalogue loads, image downloads, retries, or blocking network work. Provider health/session status remains explicitly user initiated. Existing large-catalogue and local-search performance probes remain the relevant baseline.

## 11. Security

Credentials, MAC identities, tokens, cookies, authorization headers, credential-bearing URLs, and resolved stream URLs remain outside normal UI status and diagnostics. Secret fields are cleared after submission or failure. URL validation reuses the canonical HTTP(S) value object. No SSRF-prone automatic detection or broad server probing was added.

## 12. Tests and validation plan

Focused presentation tests cover setup success, required-field validation, invalid URL rejection, transient secret visibility, secret clearing, and safe status text. Existing deterministic provider tests cover Xtream authentication/account/server/catalogue/EPG/resolution and MAG authentication/session/live/EPG/resolution. The blocking gates are formatting, Ruff, Black, MyPy, pip integrity, scoped compilation, the non-presentation corpus, package build, wheel installation, resource loading, and the configured CI workflows.

## 13. Runtime evidence

No authorized Xtream credential, populated provider, MAG production portal, approved device identity, or live IPTV stream was available for this phase. Therefore:

> **Xtream real-server acceptance: NOT VERIFIED.**
>
> **MAG/Stalker production acceptance: NOT VERIFIED and BLOCKED BY AUTHORIZED FIXTURE AVAILABILITY.**
>
> **Native media playback acceptance: separate and not established by protocol tests.**

The fresh wheel and Qt-only startup smoke test may establish package/resource and application-startup behavior, but they do not establish provider compatibility or decoded playback.

## 14. Known limitations

Real-provider acceptance, populated catalogue behavior, native Windows manual GUI acceptance, and live media playback remain separate gates. MAG VOD/Series/catch-up are unsupported by the current adapter contract. Xtream server quirks and populated VOD/Series acceptance remain unverified. Artwork caching, richer metadata presentation, category-to-channel navigation, detailed player-state semantics, and a full licensed icon set remain future work.

## 15. Independent challenge

The Independent Challenger’s findings are:

1. Xtream tests are deterministic HTTP/client and adapter fakes; they do not prove a real provider.
2. MAG tests are deterministic legacy-provider and application doubles; they do not prove production portal compatibility.
3. Stream resolution is provider URL resolution into `ResolvedPlayback`; it is not native media playback proof.
4. The corrected UI no longer says “Ready” immediately after saving a provider.
5. Automatic detection remains local and bounded; no open scanner or SSRF-prone probing was introduced.
6. Secret-bearing values remain masked, cleared, or confined to secure infrastructure boundaries.
7. The UI increment does not change provider contracts, playback architecture, or the shared libVLC path.
8. Packaging/resource declarations and existing Windows workflow guards are preserved.
9. No provider compatibility claim is made without authorized runtime evidence.
10. Changes are limited to the requested provider UX, evidence documentation, status semantics, and release README/version work.

## 16. Release impact

The README is now intentionally short. It keeps essential badges, points downloads only to the [GitHub Releases page](https://github.com/SamoTech/samotech-iptv-player/releases), removes direct artifact references, and preserves the evidence boundary for providers. The package version is prepared as `0.1.7`.

A new release must be created only after all blocking local and hosted checks pass. The existing public release must not be modified.

## 17. Exact commit SHA

The verified implementation commit is `07718664fc181e4c7ae2fd364ae85e4844e3d1ae`. Hosted CI, CodeQL, and Windows portable validation all passed against this exact commit.

## 18. Final decision

**PATCH RELEASE RECOMMENDED.** The requested README and provider/UI increment is suitable for the next patch update. The release must use the verified implementation commit above and must not modify the existing public release.
