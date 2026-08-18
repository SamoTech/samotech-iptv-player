# SamoTech IPTV Player — Protocol and Playback Architecture Investigation Report

**Repository:** [`SamoTech/samotech-iptv-player`](https://github.com/SamoTech/samotech-iptv-player)

**Investigation date:** 2026-08-18

**Author:** **Manus AI**

**Authority:** `/home/ubuntu/upload/pasted_content_3.txt` and current repository source

**Scope:** Documentation and protocol/playback architecture investigation only. No application/source code, provider implementation, tests, CI, workflow, dependency, or configuration changes were permitted or made.

## Final status

**COMPLETE — DOCUMENTATION-ONLY INVESTIGATION FINISHED.** The current repository was inspected, the current M3U, Xtream, MAG/Stalker, provider-neutral, HTTP, authentication, libVLC, Qt, buffering, recovery, subtitle, and Windows-runtime paths were traced, KiddaC’s public EStalker and XStreamity source was checked directly, and the documentation was updated to describe the current implementation rather than an idealized future architecture.

The most important architectural conclusion is explicit: **KiddaC’s values `1`, `4097`, `5001`, `5002`, and `8193` are Enigma2 service/player backend selectors, not generic IPTV protocols and not VLC/libVLC options.** SamoTech is a Windows/PySide6/libVLC application. Its equivalent playback boundary is `ResolvedPlayback` → `PlayerPort` → `VlcPlayerAdapter` → libVLC `MediaPlayer`.

## 1. Ordered Todo List and completion audit

The specification was converted into the following dependency-ordered sequence and executed in order.

| Order | Task | Result | Evidence |
|---:|---|---|---|
| 1 | Read the attached specification completely and extract constraints | **COMPLETE** | `pasted_content_3.txt` was read in full. |
| 2 | Inspect repository structure, history, current documentation, and README badge block | **COMPLETE** | `build/DOC_INVESTIGATION_REPOSITORY_BASELINE.txt`; README badge block captured before editing. |
| 3 | Trace current M3U, Xtream, MAG/Stalker, provider-neutral, and playback code paths | **COMPLETE** | `build/DOC_INVESTIGATION_CODE_TRACE_INDEX.txt`; `build/DOC_INVESTIGATION_CURRENT_ARCHITECTURE_FINDINGS.md`. |
| 4 | Audit current VLC/libVLC, HTTP, authentication, buffering, recovery, subtitles, and Windows integration | **COMPLETE** | Direct source review of `vlc_player_adapter.py`, `playback.py`, `http_session.py`, MAG session/profile/connection, Qt surface, and packaged runtime. |
| 5 | Research KiddaC EStalker and XStreamity references | **COMPLETE** | Public repository pages, GitHub CLI source trees, and fetched source files under `build/DOC_INVESTIGATION_KIDDAC/`. |
| 6 | Research authoritative VLC/libVLC playback mechanisms | **COMPLETE** | VideoLAN command-line help, VLC feature/libVLC pages, and python-vlc documentation; findings saved in `build/DOC_INVESTIGATION_VLC_DOCUMENTATION_FINDINGS.md` and `build/DOC_INVESTIGATION_VIDEOLAN_FINDINGS.md`. |
| 7 | Synthesize protocol matrix, control/media-plane mapping, limitations, and recommendations | **COMPLETE** | `docs/PROTOCOL_PLAYBACK_ARCHITECTURE.md`. |
| 8 | Update documentation only while preserving README badges byte-for-byte | **COMPLETE** | README, architecture, KiddaC adaptation/matrix, and new protocol architecture document changed; badge block hash remained identical. |
| 9 | Verify documentation scope, whitespace, links, protected badge block, and repository diff | **COMPLETE** | `git diff --check` passed; `BADGE_BLOCK=UNCHANGED`; no non-document implementation changes. |
| 10 | Produce one authoritative report | **COMPLETE** | This file. |

## 2. Files inspected

The investigation inspected the repository structure, recent history, current README and architecture documents, the provider adapters and protocol layers, the provider-neutral playback DTOs, the VLC adapter, the Qt video surface, the networking boundary, the MAG legacy provider, focused playback/provider tests, the packaged Windows runtime, and existing KiddaC adaptation records.

The highest-value current-source files were:

| Area | Files inspected |
|---|---|
| M3U | `src/samotech_iptv/infrastructure/parsing/m3u_source_loader.py`, `m3u_parser.py`, `src/samotech_iptv/infrastructure/providers/m3u_adapter.py` |
| Xtream | `xtream_adapter.py`, `xtream_api_client.py`, `xtream_request_builder.py`, `xtream_domain_translator.py` |
| MAG/Stalker | `providers/mag/provider.py`, `connection.py`, `session.py`, `protocol_profile.py`, `stream.py`, `catalogue.py`, and `src/.../infrastructure/providers/mag_adapter.py` |
| Provider-neutral boundary | `application/dtos/playback.py`, provider capability ports, `domain/value_objects/url.py`, `stream_uri.py`, `stream_protocol.py` |
| VLC/libVLC | `src/samotech_iptv/infrastructure/player/vlc_player_adapter.py`, `application/player_state_machine.py` |
| Qt/Windows | `presentation/widgets/vlc_video_surface.py`, `packaged_runtime.py`, desktop composition/runtime paths |
| Tests | VLC adapter, native surface, M3U, Xtream, MAG session/profile/stream, provider lifecycle, player state, subtitle, and native probe tests |
| Documentation baseline | `README.md`, `ARCHITECTURE.md`, `PROJECT_STATUS.md`, `ROADMAP.md`, `docs/KIDDAC_TECHNOLOGY_ADAPTATION.md`, `docs/KIDDAC_COMPATIBILITY_MATRIX.md`, and related audit documents |

## 3. Files modified

Only Markdown documentation files were modified or added:

| File | Change |
|---|---|
| `README.md` | Updated current release and acceptance evidence, linked the new architecture document, corrected Windows incident status, and added the explicit Enigma2 service-type clarification. The badge block was not changed. |
| `ARCHITECTURE.md` | Added the current protocol/media-plane boundary and linked the detailed protocol architecture document. |
| `docs/PROTOCOL_PLAYBACK_ARCHITECTURE.md` | Added the authoritative current-state protocol, provider, libVLC, buffering, KiddaC comparison, limitations, and recommendations document. |
| `docs/KIDDAC_TECHNOLOGY_ADAPTATION.md` | Added direct source-audit findings for XStreamity and EStalker service selection, portal behavior, watchdog, and `create_link`. |
| `docs/KIDDAC_COMPATIBILITY_MATRIX.md` | Added control-plane/media-plane and Enigma2 service-type comparison rows. |
| `PROTOCOL_PLAYBACK_ARCHITECTURE_INVESTIGATION_REPORT.md` | Added this final audit report. |

No Python source, provider implementation, VLC adapter, tests, CI workflow, dependency, configuration, credential, or release metadata was modified.

## 4. Protocols and source types investigated

The investigation covered every source type named in the specification and the additional current repository classification boundary.

| Source type | Current finding |
|---|---|
| M3U/M3U8 | Local/file/HTTP(S) source loading and extended-M3U live parsing are implemented. HLS/MPEG-TS/AAC decoding is delegated to libVLC after an HTTP(S) URL is resolved. M3U VOD/Series semantics and provider-specific media headers are not claimed. |
| Xtream Codes / Xtream API | Authentication, account/server info, live/VOD/series catalogue, details, short EPG, local search/filter/sort, and provider-owned live/movie/episode URL generation are implemented at the current adapter boundary. Playback is URL-based; no Xtream media-session or provider-specific cookie/header contract is currently populated. |
| MAG/Stalker | Bounded profile discovery, handshake, optional profile/account-info/do-auth stages, MAC/cookie/header handling, volatile token refresh, live categories/channels/EPG, and `create_link`-based live stream resolution are implemented in a provider-specific boundary. MAG VOD/Series/catch-up are not advertised as application capabilities. |
| Additional classified transports | `StreamURI` recognizes RTMP(S), RTSP, UDP, RTP, and SRT schemes, but the executable `URL` and `ResolvedPlayback` boundary accepts only HTTP(S). These are classified, not current playback promises. |

## 5. VLC/libVLC playback findings

The current libVLC implementation is concrete and provider-neutral. `VlcPlayerAdapter` creates one `vlc.Instance`, one media player, and one fresh `Media` per playback generation. It adds `:http-header`, `:http-user-agent`, `:http-referrer`, `:network-caching`, and optional `:avcodec-hw=none` media options. The default network cache is 1000 ms and is not differentiated between live and VOD. Hardware acceleration is left to libVLC in normal/automatic mode and disabled only for software mode or automatic retry fallback. The adapter does not force a D3D11-specific option.

Qt creates a native window surface with `WA_NativeWindow`. On Windows, the adapter calls `set_hwnd`; on Linux it calls `set_xwindow`; on macOS it calls `set_nsobject`. The packaged runtime selects bundled VLC using `_MEIPASS` for frozen builds or an explicit `VLC_RUNTIME_DIR` in source mode, validates `libvlc.dll`, `libvlccore.dll`, and the plugin directory, and replaces stale VLC environment variables.

The adapter observes Opening, Buffering, Playing, EncounteredError, EndReached, and Stopped when available. It distinguishes Loading, Playing, Buffering, Recovering, Stopping, Stopped, Paused, and Error through the typed state machine. Buffering alone does not restart a healthy stream; a timeout can request bounded recovery. END/EOF and STOPPED can request bounded media rebuilds with exponential backoff, maximum attempts, a recovery window, and a stability window that resets the budget after sustained Playing. A dedicated recovery branch for `EncounteredError` is not currently implemented.

VideoLAN’s documentation corroborates the current mechanism: VLC exposes media-specific options, HTTP user-agent/referrer controls, network caching, hardware-decoding controls, and broad input support including HTTP/FTP, UDP/RTP, MPEG transport streams, and AAC. python-vlc documents the `Instance` → `Media` → `MediaPlayer` flow used by SamoTech.[1] [2] [3] [4]

## 6. MAG/Stalker findings

MAG/Stalker has a clear control/media-plane split in the current code. The control plane owns portal discovery, profile selection, handshake, token TTL, optional account/profile/auth stages, cookies, MAC identity, Authorization, User-Agent, X-User-Agent, Referer, `JsHttpRequest`, catalogue requests, EPG, and `create_link`. The media plane begins when `MAGStream` extracts `js.url` or `js.cmd` from the portal response and validates a returned URL.

The legacy MAG stream boundary accepts HTTP, HTTPS, RTSP, and RTMP command results, but the application’s `URL` value object narrows the final provider-to-player handoff to HTTP(S). This is an important current-state limitation and is now documented explicitly. MAG token refresh is implemented as a control-plane session task. A Stalker watchdog/event request during active libVLC playback is not currently implemented in SamoTech, so portal-specific media-session requirements remain unknown and require an authorized trace.

The strongest potential buffering risk is a control/media session mismatch: a portal may require watchdog events, token refresh, or media-specific headers/cookies while the current VLC layer only receives a URL. This is a ranked hypothesis, not a proven cause of any particular playback report.

## 7. Xtream findings

The current Xtream control plane uses `player_api.php` for authentication, account/server metadata, live/VOD/series lists and categories, details, and short EPG. Final media URLs are generated from provider-owned IDs and extensions using `/live`, `/movie`, and `/series` URL paths containing the configured username/password. Those URLs are ephemeral sensitive material and must not be logged or persisted.

The current Xtream client does not retain a provider playback session, cookie jar, token refresh loop, or provider-specific media header policy. The adapter returns `ResolvedPlayback.from_url()` with default empty transport metadata. This is consistent with the current code but does not guarantee compatibility with Xtream provider variations that require a special user-agent, referrer, cookie, or expiring token.

Series are containers; Series detail produces seasons and episodes, and Episode playback resolves through the shared provider-neutral path. Catch-up remains outside the executable current capability contract.

## 8. M3U findings

M3U loading is a source boundary, not an authentication/session provider. Local files, `file:` URIs, and remote HTTP(S) playlists are bounded and parsed into canonical channels and streams. Local CRLF/CR is normalized to LF. Extended-M3U metadata includes common `tvg-*` fields and group names. The M3U adapter advertises Live, Search, and Stream Resolution and only turns valid HTTP(S) stream URLs into `ResolvedPlayback` targets.

The application does not implement an M3U-specific Python demuxer, HLS engine, MPEG-TS decoder, AAC decoder, reconnect option, or stream header policy. Once the HTTP(S) URL crosses the provider-neutral boundary, libVLC owns buffering, network connection, demuxing, decoding, and rendering. M3U entries using other classified schemes are outside the current executable handoff even if the domain classifier can represent them.

## 9. KiddaC references investigated

The public [kiddac/XStreamity repository][5] was inspected through its repository page, source tree, and fetched `server.py`, `liveplayer.py`, `catchup.py`, and `vodplayer.py` source. The public [kiddac/EStalker repository][6] was inspected through its repository page, source tree, and fetched `server.py`, `playlists.py`, `liveplayer.py`, and `vodplayer.py` source.

XStreamity constructs user-entered Xtream playlist/API URLs, uses `player_api.php`, and invokes `eServiceReference` plus `session.nav.playService`. Its `streamtypelist` starts with `1` and `4097`, optionally adds `5001`, `5002`, and `8193` based on Enigma2 system/player availability, and can switch HLS input from service type `1` to `4097`.

EStalker carries MAC, token, token-random/play-token, cookies, User-Agent, X-User-Agent, Referer, and Bearer Authorization. It issues Stalker portal operations, invokes `watchdog` event requests during playback, calls `create_link` for portal-confirmed commands, and finally invokes Enigma2 `eServiceReference`/`session.nav.playService`. VOD/series flows use portal detail and link operations, followed by the same Enigma2 player boundary.

The transferable concepts are request sequencing, provider authentication, MAC/session/token handling, cookies, headers, Referer, `JsHttpRequest`, `create_link`, catalogue/detail resolution, watchdog concepts, provider-specific archive behavior, and bounded failure handling. The non-transferable concepts are Enigma2 service types, `eServiceReference`, `session.nav.playService`, Enigma2 native decoder/player binaries, and global playlist/UI state.

## 10. Differences between Enigma2 playback and libVLC playback

| Concern | KiddaC EStalker/XStreamity | SamoTech |
|---|---|---|
| Operating environment | Enigma2 set-top box | Windows desktop |
| UI/runtime | Enigma2 screens, session, timers, global playlist state | PySide6 widgets, qasync, application ports, generation-safe tasks |
| Playback invocation | `eServiceReference(int(service_type), ..., url)` then `session.nav.playService` | `ResolvedPlayback` then `PlayerPort` and libVLC `MediaPlayer` |
| Backend selection | Integer service/player types and installed Enigma2 binaries | One libVLC backend; media options configure the URL/media object |
| Native video output | Enigma2 service/player surface | Qt native window handle passed to libVLC (`set_hwnd` on Windows) |
| Protocol values `1/4097/5001/5002/8193` | Enigma2 service/player selectors | **Not used and not VLC protocols** |
| Provider session state | Legacy/global plugin state and portal helpers | Infrastructure-owned credentials/session state; canonical application records are secret-free |
| Catch-up | Provider-specific live/timeshift URL construction and Enigma2 playback | Not currently executable; provider-neutral event/resolution contract is required |
| Recovery | Legacy player callbacks, timers, and service re-invocation | Typed libVLC events, buffering watchdog, bounded media rebuild, generation/session guards |

## 11. Buffering findings and ranked potential issues

The most likely current causes of repeated buffering are provider media URL expiration or a missing control/media session mechanism, missing stream-level headers/cookies, network instability relative to the fixed 1000 ms cache, and URL/container mismatch. Hardware decoding and Windows rendering remain possible but have an automatic software fallback after immediate start failure. The current recovery policy may also miss a provider failure that appears only as `EncounteredError`, because that event is subscribed but does not currently trigger a dedicated recovery branch.

Increasing network caching is not a universal fix. It may reduce sensitivity to short network jitter at the cost of startup latency, but it cannot repair an expired URL, missing cookies, missing Referer, absent Stalker watchdog, incorrect container, or a provider control/media mismatch. The next investigation should correlate redacted provider/session events with libVLC event sequences and stream expiry rather than changing cache values speculatively.

## 12. Potential issues discovered

| Finding | Evidence | Impact | Recommended change |
|---|---|---|---|
| Transport classification is broader than executable playback | `StreamURI` classifies RTMP(S), RTSP, UDP, RTP, SRT; `URL` accepts only HTTP(S) | Users or future code may mistake classification for playback support | Define an explicit provider/player transport capability contract before widening URL support |
| Transport metadata is modeled but not populated by current provider resolvers | `TransportMetadata` and VLC option mapping exist; M3U/Xtream/MAG return URL-only playback | Provider-specific stream headers/cookies cannot reach libVLC today | Add ephemeral transport metadata only after authorized fixtures prove requirements |
| MAG control refresh is not a media watchdog | `MAGSession` refreshes tokens; no active-playback Stalker watchdog in player/session boundary | Some portals may expire or buffer media despite a valid control token | Validate with an authorized portal trace and model provider-session/media lifetime explicitly |
| VLC error events lack a dedicated recovery branch | `EncounteredError` subscription exists; handler recovers Buffering/END/STOPPED only | Some error paths may not rebuild media | Add only after a focused event/recovery contract and regression tests are defined |
| Catch-up is reference-specific and not current product support | No current `CATCHUP` capability; KiddaC uses provider-specific timeshift behavior | Copying a timeshift URL would invent a SamoTech contract | Define provider-neutral event listing/resolution and authorized fixtures first |

These are **FINDING / EVIDENCE / IMPACT / RECOMMENDED CHANGE** records only. No recommended implementation was made during this task.

## 13. Verification results

| Verification | Result |
|---|---:|
| Full specification read | **PASS** |
| Current repository source inspection | **PASS** |
| KiddaC EStalker/XStreamity direct source inspection | **PASS** |
| VideoLAN/python-vlc reference inspection | **PASS** |
| Documentation-only modification scope | **PASS** |
| README badge block byte comparison | **PASS — unchanged** |
| `git diff --check` | **PASS** |
| Credentials added | **NO** |
| Application/source code modified | **NO** |
| Provider/VLC/tests/CI/workflows modified | **NO** |
| Full application test suite rerun | **NOT RUN — documentation-only scope; no implementation code changed** |

The badge block before and after editing has the same SHA256: `aed49790437763e1a73d2da0123563071138c87e38677386d44ad212d3edd686`. The working change set contains only Markdown files.

## 14. Blocked items and exact reasons

No task in the documentation specification was blocked. The following implementation validations remain outside this task or require evidence unavailable in the repository:

| Item | Classification | Exact reason |
|---|---|---|
| Populated authorized Xtream playback acceptance | **NOT TESTED / REQUIRES AUTHORIZED VALIDATION** | No current authorized populated provider fixture was part of this documentation-only task. |
| Production MAG/Stalker watchdog requirement | **UNKNOWN / REQUIRES VALIDATION** | No authorized portal trace proves whether watchdog/event requests are required during media playback. |
| Provider-specific M3U/Xtream/MAG media headers/cookies | **UNKNOWN / REQUIRES VALIDATION** | Current resolvers do not populate `TransportMetadata`; no authorized sanitized request/stream trace was available. |
| Non-HTTP(S) executable playback | **NOT IMPLEMENTED / REQUIRES DESIGN** | Domain classification is broader than the HTTP(S)-only `URL`/`ResolvedPlayback` boundary. |
| Catch-up/timeshift | **BLOCKED BY CONTRACT EVIDENCE** | No provider-neutral event/resolution contract or authorized fixture exists. |
| Full application test rerun | **NOT RUN** | The specification prohibited implementation changes; this task changed documentation only and did not require a code regression run. |

## 15. Remaining actions

The next implementation phase should first define a provider-neutral transport metadata contract and collect authorized sanitized fixtures for headers, cookies, referrers, token expiry, and MAG watchdog behavior. It should then decide whether to broaden executable transport support beyond HTTP(S), add an explicit libVLC `EncounteredError` recovery policy, and define a catch-up/event contract before copying any provider-specific archive URL behavior. These actions are recommendations and were intentionally not implemented.

## 16. Git diff summary

Before adding this report, the documentation change set consisted of five Markdown files: `README.md`, `ARCHITECTURE.md`, `docs/PROTOCOL_PLAYBACK_ARCHITECTURE.md`, `docs/KIDDAC_TECHNOLOGY_ADAPTATION.md`, and `docs/KIDDAC_COMPATIBILITY_MATRIX.md`. This report is the sixth documentation file in the final change set. `git diff --check` passed, the protected badge block is byte-identical, and no non-Markdown implementation file is changed.

## References

[1]: https://github.com/SamoTech/samotech-iptv-player/blob/main/src/samotech_iptv/application/dtos/playback.py "SamoTech provider-neutral playback DTOs"
[2]: https://github.com/SamoTech/samotech-iptv-player/blob/main/src/samotech_iptv/infrastructure/player/vlc_player_adapter.py "SamoTech libVLC player adapter"
[3]: https://github.com/SamoTech/samotech-iptv-player/blob/main/src/samotech_iptv/presentation/widgets/vlc_video_surface.py "SamoTech Qt native video surface"
[4]: https://python-vlc.readthedocs.io/en/latest/ "python-vlc documentation"
[5]: https://github.com/kiddac/XStreamity "KiddaC XStreamity repository"
[6]: https://github.com/kiddac/EStalker "KiddaC EStalker repository"
[7]: https://github.com/SamoTech/samotech-iptv-player/blob/main/src/samotech_iptv/infrastructure/parsing/m3u_source_loader.py "SamoTech M3U source loader"
[8]: https://github.com/SamoTech/samotech-iptv-player/blob/main/src/samotech_iptv/infrastructure/providers/xtream_api_client.py "SamoTech Xtream API client"
[9]: https://github.com/SamoTech/samotech-iptv-player/blob/main/src/samotech_iptv/infrastructure/providers/xtream_request_builder.py "SamoTech Xtream request builder"
[10]: https://github.com/SamoTech/samotech-iptv-player/blob/main/providers/mag/protocol_profile.py "SamoTech MAG protocol profiles"
[11]: https://github.com/SamoTech/samotech-iptv-player/blob/main/providers/mag/session.py "SamoTech MAG session lifecycle"
[12]: https://wiki.videolan.org/VLC_command-line_help/ "VideoLAN VLC command-line help"
[13]: https://images.videolan.org/vlc/features.html "VideoLAN VLC features"
[14]: https://images.videolan.org/vlc/libvlc.html "VideoLAN libVLC overview"
[15]: https://raw.githubusercontent.com/kiddac/XStreamity/master/XStreamity/usr/lib/enigma2/python/Plugins/Extensions/XStreamity/liveplayer.py "KiddaC XStreamity live player source"
[16]: https://raw.githubusercontent.com/kiddac/EStalker/master/EStalker/usr/lib/enigma2/python/Plugins/Extensions/EStalker/liveplayer.py "KiddaC EStalker live player source"
[17]: https://raw.githubusercontent.com/kiddac/EStalker/master/EStalker/usr/lib/enigma2/python/Plugins/Extensions/EStalker/vodplayer.py "KiddaC EStalker VOD/series player source"
[18]: https://github.com/SamoTech/samotech-iptv-player/blob/main/docs/PROTOCOL_PLAYBACK_ARCHITECTURE.md "Detailed current protocol/playback architecture document"
