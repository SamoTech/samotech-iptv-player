# MAG/Stalker/Ministra Middleware Compatibility

## Evidence classes

This document distinguishes **OFFICIAL INFOMIR BEHAVIOR**, **OPEN-SOURCE IMPLEMENTATION**, **SOURCE-OBSERVED** behavior from supplied reverse-engineered clients, and **SIMULATED** behavior from the local deterministic laboratory. None of these categories by itself proves that the supplied production portal belongs to a particular middleware family.

## Official Infomir findings

Infomir's Ministra installation documentation states that the product was previously called Stalker Middleware and documents the classic portal project under a `/stalker_portal/` web path. The same documentation distinguishes installation/configuration from administrative/API facilities and documents STB authorization by login/password or authorization with a key. [1]

Infomir's configuration reference documents a configurable `portal_url`, `stalker_api_url`, `strict_stb_type_check`, an `allowed_stb_types` list, and device-class API options. These controls establish that portal routing, STB model acceptance, and authorization behavior can be middleware configuration decisions rather than universal client properties. [2]

The official documentation does **not** identify the supplied authorized portal's exact middleware version, rewrite rules, STB authorization mode, MAC registration state, allowed STB models, or device-registration policy. Therefore the real portal's 404 and empty response cannot be attributed to one cause from official documentation alone.

## Open-source candidates

| Candidate | Evidence obtained | Lab suitability | Classification |
|---|---|---|---|
| [`lloesche/stalker_portal`](https://github.com/lloesche/stalker_portal) | MIT license; repository identifies as Middleware Stalker; classic `server/load.php`; readable configuration and dispatcher structure; shallow-cloned core DataLoader/STB files are opaque ASCII/base64-like artifacts. | Not practical as a runnable local reference in this sandbox because the core implementation is not inspectable and the historical PHP/web/database stack is unavailable. | **OPEN-SOURCE IMPLEMENTATION; PARTIALLY INSPECTABLE** |
| [`iptvhakr/stalker_portal`](https://github.com/iptvhakr/stalker_portal) | Middleware Stalker tree with release 5.1.1 notes; classic `server/load.php`; `portal_url = /stalker_portal/`; separate `stalker_api_url`; `strict_stb_type_check = false`; commented allowed STB model list; core DataLoader/STB files opaque in the shallow clone. | Not practical as a runnable local reference in this sandbox for the same legacy-runtime and opaque-core reasons. | **OPEN-SOURCE IMPLEMENTATION; PARTIALLY INSPECTABLE** |
| [`ricosharp/Ministra`](https://github.com/ricosharp/Ministra) | Installer README states Ministra 5.6.0 on Ubuntu 16.04 and expects a separate Ministra archive. | Not a self-contained middleware source tree or server; no local deployment from the clone alone. | **INSTALLER ONLY** |

The readable `server/load.php` in both Stalker trees is a classic dispatcher. It sets no-cache headers, loads common bootstrap code, constructs `DataLoader($_REQUEST['type'], $_REQUEST['action'])`, passes the result to `AjaxBackend`, and sends the response. This confirms the classic request shape but does not reveal the opaque token algorithm.

## Middleware-version matrix

Only cells supported by the inspected evidence are filled.

| Middleware family/version | Classic endpoint | Handshake contract | Token contract | Cookie/identity contract | Catalogue contract | `create_link` |
|---|---|---|---|---|---|---|
| Stalker Middleware 4.x | **Documented/source-supported family:** classic `/stalker_portal/server/load.php` exists in the open-source tree; exact version mapping of the cloned tree is not proven. | **UNKNOWN** from the opaque core files. | **UNKNOWN** from the opaque core files. | **UNKNOWN** beyond the existence of STB/MAC-related configuration and classes. | **UNKNOWN** in exact response shape from the opaque core files. | **UNKNOWN** in exact response shape from the opaque core files. |
| Stalker Middleware 5.x | **SOURCE-OBSERVED:** the 5.1.1 candidate contains `/stalker_portal/server/load.php` and `portal_url = /stalker_portal/`. | **SOURCE-OBSERVED dispatcher only:** `type` and `action` are passed to DataLoader; exact token algorithm is unavailable from the opaque core. | **UNKNOWN** from the cloned core. | **OFFICIAL/SOURCE-OBSERVED:** STB model and authorization controls exist; exact per-portal requirements remain unknown. | **SOURCE-OBSERVED dispatcher only;** exact list semantics remain unknown from the opaque core. | **UNKNOWN** from the cloned core. |
| Ministra 5.x | **OFFICIAL:** installation documentation describes the classic `/stalker_portal/` project path. **INSTALLER:** `ricosharp/Ministra` targets 5.6.0. | **UNKNOWN** for a specific release from the available source. | **UNKNOWN** for a specific release from the available source. | **OFFICIAL:** login/password and authorization-key methods are documented; model restrictions and API options are configurable. | **UNKNOWN** for a specific release. | **UNKNOWN** for a specific release. |

This matrix intentionally does not convert common Stalker client behavior into an official version guarantee.

## Local middleware laboratory

A historical middleware deployment was not practical in this sandbox. Docker, PHP, MySQL/MariaDB, Nginx, and Apache runtimes were unavailable as runnable binaries, and the open-source candidates require legacy multi-service environments. Their core DataLoader/STB files were opaque in the inspected shallow clones.

The repository therefore adds a deterministic **SOURCE-DERIVED / SIMULATED** local middleware laboratory in `tests/providers/mag/test_middleware_lab.py`. It models the verified classic dispatcher route and uses known local test data only. The server accepts:

| Operation | Lab contract |
|---|---|
| Handshake | `GET /stalker_portal/server/load.php` with `type=stb`, `action=handshake`, empty `token`, and `JsHttpRequest=1-xml`; returns a deterministic lab token and TTL. |
| Authenticated session | Requires Bearer authorization, token cookie, and MAC cookie on subsequent requests. |
| Profile/account | Provides optional `get_profile` and `get_main_info` responses, but does not require them before live catalogue access because no inspected source proves they are mandatory for the classic handshake. |
| Genres | `type=itv`, `action=get_genres`, returning one deterministic category. |
| Ordered list | `type=itv`, `action=get_ordered_list`, `genre`, `JsHttpRequest=1-xml`, and pages `p=1` then `p=2`, returning three deterministic channels. |
| Stream resolution | `type=itv`, `action=create_link`, `JsHttpRequest=1`, command-based request, and a deterministic local stream URL in the test response. |

The lab drives the real MAG provider, connection, session, profile, catalogue, adapter, canonical channel translation, pagination, and stream resolver. It does not emulate hardware, contact a real provider, or establish production portal support.

## Real-portal classification

The authorized real portal remains **UNRESOLVED**. The bounded candidate set returned four HTTP 404 responses, one empty HTTP-200 `text/javascript` response, and one HTTP-404 GUI fingerprint response. The corrected raw GUI MAC-cookie representation was revalidated and remained HTTP 404. No candidate returned structurally valid JSON with a token. Consequently, no evidence identifies the real portal as Stalker 4.x, Stalker 5.x, Ministra 5.x, a middleware fork, or a non-Ministra implementation.

The exact next evidence boundary is a current Windows application run using the committed build and safe diagnostics, or provider-supplied middleware/version/authorization details. Neither path justifies additional arbitrary endpoint permutations.

## References

[1]: https://wiki.infomir.eu/eng/ministra-tv-platform/ministra-installation-guide/ministra-tv-platform-installation "Infomir Ministra TV Platform installation"
[2]: https://wiki.infomir.eu/eng/ministra-tv-platform/ministra-installation-guide/configuration-file "Infomir Ministra configuration file"
[3]: https://github.com/lloesche/stalker_portal "lloesche/stalker_portal"
[4]: https://github.com/iptvhakr/stalker_portal "iptvhakr/stalker_portal"
[5]: https://github.com/ricosharp/Ministra "ricosharp/Ministra installer"
