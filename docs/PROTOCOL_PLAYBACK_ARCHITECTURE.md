# SamoTech IPTV Player — Protocol and Playback Architecture

**Status:** Current-state documentation derived from repository source and verified public references

**Scope:** M3U/M3U8, Xtream Codes, MAG/Stalker, provider-neutral playback, libVLC media handling, buffering/recovery, and KiddaC reference comparison

**Authority:** The implementation is the source of truth. This document does not claim capabilities that are absent from the current adapters, ports, or tests.

## 1. Executive architecture overview

SamoTech is a Windows/PySide6 desktop application whose sole media backend is `python-vlc` over libVLC. The provider layer does not hand raw provider payloads to Qt and the Qt presentation layer does not construct provider URLs. Instead, provider adapters authenticate or load a source, translate catalogue data into canonical records, resolve an authorized stream, and return a provider-neutral `ResolvedPlayback` object. The application then passes that object through `PlayerPort` to one shared `VlcPlayerAdapter`, which creates a libVLC `Media`, attaches it to a `MediaPlayer`, and renders through a Qt-owned native window surface.[1] [2] [3]

```text
Authorized source or provider
        ↓
Provider adapter / parser / protocol DTOs
        ↓
Credential and session boundary
        ↓
Canonical domain entities and capability ports
        ↓
PlaybackResource → provider stream resolver
        ↓
ResolvedPlayback(URL + ephemeral transport metadata)
        ↓
PlayerPort → VlcPlayerAdapter → libVLC MediaPlayer
        ↓
Qt/PySide6 native video surface
        ↓
Typed state, buffering watchdog, bounded live recovery
```

The architecture distinguishes four concepts that must not be collapsed into one another. A **provider or source** supplies catalogues, authentication, EPG, or stream links. A **manifest or playlist** describes content or renditions. A **media transport** is the URI delivery scheme. A **player backend** is the engine that connects, demuxes, decodes, and renders the resolved media. An M3U file is therefore not a transport protocol, Xtream is not a VLC protocol, and an Enigma2 service type is not a libVLC media option.

## 2. Control plane and media plane

The **control plane** performs authentication, catalogue retrieval, category and EPG queries, detail lookup, session/token maintenance, and stream-link resolution. Its output is a canonical content record or an ephemeral final playback target. The **media plane** begins only after resolution: libVLC connects to the final URL, applies any explicitly supplied transport metadata, buffers input, selects a demuxer and decoder, and renders through the Qt surface.

| Plane | SamoTech responsibility | Typical evidence in the current code |
|---|---|---|
| Control plane | Source loading, provider authentication, session state, catalogue/channel/VOD/series/EPG resolution, stream URL construction | `M3USourceLoader`, `M3UParser`, `XtreamApiClient`, `XtreamRequestBuilder`, `MAGSession`, `MAGCatalogue`, `MAGStream` |
| Boundary | Convert provider-owned content into `PlaybackResource` and then `ResolvedPlayback` | `application/dtos/playback.py`, provider `resolve_*` methods |
| Media plane | Create libVLC media, apply caching and transport options, start/stop/pause/recover, query tracks/state, attach native output | `infrastructure/player/vlc_player_adapter.py` |
| Presentation | Own Qt navigation, capability-gated screens, native surface, and user controls | `presentation/player_shell.py`, `presentation/widgets/vlc_video_surface.py` |

The current transport metadata model can carry ephemeral HTTP headers, a user-agent, a referrer, a protocol hint, and a container hint. However, current M3U, Xtream, and MAG resolvers return `ResolvedPlayback.from_url()` without populating provider-specific headers or cookies. The model is therefore a safe extension point, not evidence that every provider’s media-plane authentication is already implemented.[1]

## 3. Current provider matrix

| Source | Control plane | Media plane | Authentication/session | URL resolution | Headers/cookies | Current status |
|---|---|---|---|---|---|---|
| M3U/M3U8 source | Load local path, `file:` URI, or remote HTTP(S); parse bounded extended-M3U metadata | libVLC receives the resolved HTTP(S) URL; HLS/MPEG-TS/AAC decoding is delegated to libVLC | No provider session; secure tokenized sources may be retrieved from the OS credential boundary | Parsed channel URI is wrapped as `ResolvedPlayback` only when it is a valid HTTP(S) URL | No M3U-specific header/cookie injection in the current adapter | **Partially implemented** |
| Xtream Codes API | `player_api.php` authentication, account/server info, categories, live/VOD/series, details, short EPG | libVLC receives URL-shaped `/live`, `/movie`, or `/series` path | Username/password are used for API calls and URL construction; no retained Xtream playback session object | Live, Movie, and Episode URLs are built from provider IDs and validated extensions | No provider-specific media headers/cookies are currently populated | **Partially implemented** |
| MAG/Stalker | Bounded profile discovery, handshake, optional profile/account-info/do-auth, live categories/channels/EPG, and `create_link` | Legacy stream layer validates portal-returned HTTP(S)/RTSP/RTMP commands; application handoff narrows to HTTP(S) | Volatile MAC/session token, cookies, Authorization, refresh loop, bounded GET retries | Portal `js.url`/`js.cmd` or direct channel command becomes a validated URL | Control-plane profile headers/cookies are implemented; they are not currently attached as media-plane `ResolvedPlayback` metadata | **Partially implemented and provider-specific** |
| Additional source | No additional production adapter is currently advertised beyond M3U, Xtream, MAG/Stalker, and trusted local plugins | URI classification recognizes more schemes, but the executable `URL`/player boundary remains HTTP(S) | Provider-specific | No general-purpose fallback resolver | No generic header/cookie inference | **Unknown / requires validation** |

The matrix intentionally distinguishes **classified** from **playable**. `StreamURI` can classify RTMP(S), RTSP, UDP, RTP, and SRT, but the current `URL` value object accepts only HTTP and HTTPS. The current provider-to-player contract therefore does not promise executable playback for every classified transport.

## 4. M3U and M3U8 architecture

### 4.1 Flow

```text
Local path / file URI / HTTP(S) playlist
        ↓
M3USourceLoader
  - bounded bytes
  - UTF-8 decode
  - local CRLF/CR → LF normalization
  - shared HTTP client for remote source
        ↓
M3UParser
  - #EXTM3U and #EXTINF validation
  - tvg-id/name/logo/group/chno metadata
  - canonical Channel + Stream entities
        ↓
M3UProviderAdapter
  - local loaded-catalogue search
  - HTTP(S) stream URL resolution
        ↓
ResolvedPlayback
        ↓
libVLC MediaPlayer
```

`M3USourceLoader` accepts Windows drive paths, generic local paths, `file:` URIs, and remote `http`/`https` URLs. Local input is bounded to 64 MiB, decoded as UTF-8, and normalized to canonical LF. Remote input uses the shared asynchronous HTTP client with an explicit large read/total timeout and the same byte bound. The loader has no provider token refresh, cookie jar, or stream-specific header policy.[4]

`M3UParser` requires `#EXTM3U`, requires a stream URI after each `#EXTINF` record, and maps common extended-M3U attributes into canonical channel and stream entities. It preserves URI schemes at the `StreamURI` classification boundary, but `M3UProviderAdapter.resolve_stream()` constructs the narrower HTTP(S)-only `URL` value object. Consequently, an M3U entry may be syntactically classifiable as RTSP, UDP, RTP, SRT, or RTMP while remaining outside the current executable playback contract.

For HTTP streams, HTTPS streams, HLS `.m3u8` manifests, MPEG transport streams, and AAC or other media formats, SamoTech does not implement a Python demuxer or decoder. It passes the final HTTP(S) URL to libVLC. VideoLAN documents VLC input support for HTTP/FTP and UDP/RTP families and common MPEG/AAC media formats, while noting that exact input behavior depends on the build and runtime modules.[10] [11]

## 5. Xtream Codes architecture

### 5.1 Control-plane flow

```text
Xtream base URL + username/password
        ↓
CredentialStore / XtreamProviderAdapter.authenticate()
        ↓
XtreamRequestBuilder → player_api.php
        ↓
XtreamApiClient JSON control calls
  - base account/server
  - live/VOD/series lists and categories
  - VOD/series details
  - short EPG
        ↓
XtreamDomainTranslator
        ↓
Canonical live/movie/series/season/episode records
```

The current Xtream client uses `player_api.php` for authentication, account and server metadata, live/VOD/series lists, categories, details, and short EPG. The adapter rejects malformed records or skips invalid individual catalogue records according to the current translator policy. The application receives provider-scoped canonical identities and does not receive raw credentials or provider DTOs.[5] [6]

### 5.2 Media-plane flow

```text
Selected live channel / movie / episode
        ↓
Provider-owned stream ID + validated extension
        ↓
XtreamRequestBuilder
  /live/{username}/{password}/{id}.{ext}
  /movie/{username}/{password}/{id}.{ext}
  /series/{username}/{password}/{id}.{ext}
        ↓
ResolvedPlayback(URL)
        ↓
libVLC MediaPlayer
```

The current implementation treats Xtream playback as a URL-based handoff. The API client does not keep a provider playback session, attach cookies, refresh a media token, or populate a provider-specific user-agent/referrer in `TransportMetadata`. The username and password are part of the generated stream path, so URLs are ephemeral sensitive material and must not be logged, persisted, or displayed unnecessarily.

The exact container extension comes from the provider record for live content and from the provider’s detail/resource descriptor for VOD and episodes. Current code validates that the extension is alphanumeric; it does not independently probe or transcode the resulting media. HTTP versus HTTPS is inherited from the configured Xtream base URL.

## 6. MAG/Stalker architecture

### 6.1 Control-plane flow

```text
Portal URL + MAC/device credential
        ↓
MAGProvider / MAGConnection
        ↓
Optional bounded protocol discovery
  - approved profile/endpoint candidates only
        ↓
Selected MAGProtocolProfile
        ↓
MAGSession
  - handshake/token
  - optional account-info/get-profile/do-auth
  - volatile token TTL
  - scheduled refresh with bounded retry
        ↓
MAGCatalogue
  - live categories/channels/EPG
  - profile-specific request forms
        ↓
MAGStream / create_link
        ↓
ResolvedPlayback(URL)
```

The current MAG implementation is explicitly profile-driven rather than a generic portal crawler. Profiles construct fixed endpoint families and request parameters; the connection layer uses a dedicated asynchronous HTTP session, bounded JSON response reads, exponential retry for GET requests, and no retry for POST requests. Depending on the selected profile, request headers may include a MAG-style `User-Agent`, `X-User-Agent`, `Referer`, MAC cookie, language/timezone cookies, `Authorization: MAC ...`, or `Authorization: Bearer ...`. `JsHttpRequest` is part of selected Stalker request profiles, not a VLC option.[7] [8]

The application-facing `MagProviderAdapter` currently advertises authentication, session, live, categories, EPG, search, and stream resolution. Although the legacy catalogue contains VOD/series methods and the stream layer has VOD/series operation names, the current application does **not** advertise MAG VOD, Series, or catch-up playback as supported capabilities. This distinction prevents an internal legacy method from becoming an unsupported product claim.

### 6.2 `create_link` and the media boundary

`MAGStream` either validates a direct channel command for profiles that use direct channel URLs or calls the profile-selected `create_link` operation. It extracts `js.url` or `js.cmd`, searches command text for a URL when required, and accepts HTTP, HTTPS, RTSP, and RTMP at the legacy stream layer. The application’s `URL` boundary then limits the current executable `ResolvedPlayback` handoff to HTTP(S). The portal command and token are control-plane material; the returned URL is media-plane material.

The current code refreshes the MAG token through `MAGSession`, but it does not send a Stalker watchdog/event request from `VlcPlayerAdapter` during active media playback. A portal may therefore require an additional media-session lifetime mechanism that is not yet part of the current provider-neutral contract. This is a known uncertainty, not an implemented capability.

## 7. VLC/libVLC playback architecture

### 7.1 Media creation and options

The current `VlcPlayerAdapter` creates one libVLC instance and one media player. Each playback generation creates a new `Media` from the resolved URL. The adapter adds typed transport metadata to the media using:

| Transport input | Current libVLC option |
|---|---|
| One explicit header | `:http-header=name: value` |
| User-agent | `:http-user-agent=value` |
| Referrer | `:http-referrer=value` |
| Network cache | `:network-caching=1000` by default, configurable in milliseconds |
| Software fallback | `:avcodec-hw=none` when software mode is selected or automatic retry falls back |

VideoLAN’s help documents the corresponding `http-referrer`, `http-user-agent`, `network-caching`, and `avcodec-hw` option families.[9] The VideoLAN feature documentation describes hardware decoding with software fallback, but the current SamoTech adapter does not force a D3D11-specific value; it leaves normal hardware selection to libVLC and explicitly disables hardware acceleration only for software mode/fallback.[10]

The current defaults do not distinguish live and VOD network-caching values. Both use the adapter’s `network_caching_ms` setting. There is no separate file-caching policy in the adapter, and no provider-specific reconnect option is passed to the media. Reconnect behavior is implemented at the application lifecycle level by rebuilding media after bounded failure conditions rather than by claiming that a VLC input option guarantees reconnection.

### 7.2 Qt surface and Windows integration

`VlcVideoSurface` creates a Qt widget with `WA_NativeWindow`. Its `showEvent()` attaches the native handle once. On Windows, `VlcPlayerAdapter.attach_video_output()` calls `MediaPlayer.set_hwnd()`. Linux uses `set_xwindow()` and macOS uses `set_nsobject()`. This is the correct conceptual separation: Qt owns the native surface; libVLC renders into the handle.[2] [3]

The packaged Windows runtime configures bundled `libvlc.dll`, `libvlccore.dll`, and the VLC plugin directory before `python-vlc` import. Frozen bundles use `_MEIPASS`; source mode may use an explicit `VLC_RUNTIME_DIR`. The runtime keeps Windows DLL-directory handles alive and replaces stale VLC environment variables so the process does not accidentally mix installations.[12]

### 7.3 State, buffering, EOF, and recovery

The adapter subscribes to Opening, Buffering, Playing, EncounteredError, EndReached, and Stopped when the binding exposes them. The public typed state machine distinguishes loading, playing, buffering, recovering, stopping, stopped, paused, and error states. `BUFFERING` does not immediately restart media. It starts a watchdog; only prolonged buffering or a later END/STOPPED condition can request a rebuild. Recovery is bounded by attempt count and time window, uses exponential delay, invalidates stale media generations, and resets its budget only after sustained Playing. Immediate start failure can retry once with software fallback in automatic mode.

The current event handler subscribes to `EncounteredError`, but a dedicated error-event recovery branch is not implemented. This is a concrete finding for future work rather than a reason to claim that all network failures are automatically recovered. Likewise, a healthy stream is not restarted merely because a transient Buffering callback occurs.

### 7.4 Subtitles, tracks, seek, and recording

The player exposes native audio/subtitle track enumeration and selection, local subtitle attachment for bounded SRT, ASS, SSA, and VTT files, subtitle delay, aspect-ratio control, and `.ts` duplicate-output recording. The Qt shell exposes seek, restart, and persisted playback progress only for Movie/Episode modes. Live inputs are treated as non-seekable and display live status instead of a resume workflow.

## 8. KiddaC EStalker and XStreamity comparison

### 8.1 What the references are

KiddaC’s public [XStreamity repository](https://github.com/kiddac/XStreamity) identifies itself as an **Enigma2 plugin for playing official Xtream Codes IPTV playlists**. Its source constructs user-entered Xtream playlist/API URLs, uses provider API endpoints, and invokes Enigma2 `eServiceReference`/`session.nav.playService`. KiddaC’s public [EStalker repository](https://github.com/kiddac/EStalker) identifies itself as an **Enigma2 IPTV Ministra/Stalker player**. Its source carries MAC, token, cookie, `User-Agent`, `X-User-Agent`, Referer, and Authorization state, performs portal requests and `create_link`, and invokes the Enigma2 service player.[13] [14] [15]

The values `1`, `4097`, `5001`, `5002`, and `8193` are therefore **Enigma2 service/player transport selectors**. They are selected when constructing `eServiceReference` and when trying alternate Enigma2 playback backends. They are not generic IPTV protocols, not HTTP methods, not HLS modes, and not VLC/libVLC options. SamoTech must never copy those numbers into the Windows/libVLC player as if they selected a VLC transport.

### 8.2 Transferable concepts

The references are useful for protocol behavior and provider compatibility requirements. The transferable concepts are Stalker request sequencing, MAC/session/token handling, cookies, User-Agent/X-User-Agent/Referer requirements, `JsHttpRequest`, `create_link`, catalogue and detail resolution, watchdog/session maintenance, catch-up URL derivation as a provider-specific behavior, and bounded retry/failure handling. SamoTech already incorporates some of these concepts through infrastructure-owned MAG profiles and session state, while deliberately keeping them out of domain records and Qt.

| Reference concept | SamoTech equivalent or status |
|---|---|
| Xtream `player_api.php` control calls | Current `XtreamApiClient` and request builder |
| Xtream live/VOD/series URL construction | Current provider-owned `XtreamRequestBuilder` and resolver methods |
| Stalker handshake/profile/session behavior | Current bounded MAG profiles and `MAGSession` |
| MAC/cookie/Authorization/User-Agent/Referer request details | Current MAG control-plane profiles; not yet propagated to media-plane `ResolvedPlayback` |
| `create_link` and portal command resolution | Current `MAGStream` control-to-media boundary |
| Watchdog/event requests | Not currently implemented in the SamoTech media/session boundary; requires authorized evidence |
| Catch-up/timeshift | Not currently advertised or executable in SamoTech |
| Provider-specific retries | Current bounded MAG GET retry and token refresh; libVLC recovery is provider-neutral |

### 8.3 Non-transferable concepts

The following are not directly transferable to SamoTech: Enigma2 service types, `eServiceReference`, `session.nav.playService`, native Enigma2 decoder/player binaries, Enigma2-specific hardware/backend fallback lists, global playlist dictionaries, keymap/UI assumptions, and legacy filesystem persistence. SamoTech’s equivalent of “play this URL” is not an integer service type; it is a `ResolvedPlayback` URL plus explicit ephemeral transport metadata passed into libVLC media options.

## 9. Buffering and playback issue assessment

The current architecture can enter repeated buffering for several distinct reasons, and the evidence does not justify treating cache size as a universal fix. The ranked hypotheses are:

| Rank | Potential cause | Evidence and current status |
|---:|---|---|
| 1 | Provider media URL expiration or control/media session mismatch | Strong for MAG-like portals because the current code refreshes the control-plane token but does not send a media-playback watchdog. Requires authorized trace. |
| 2 | Missing provider-specific media headers or cookies | Plausible for M3U, Xtream, and MAG variants because current resolvers do not populate `TransportMetadata` even though libVLC can consume it. Requires provider evidence. |
| 3 | Network path instability or insufficient fixed cache for a particular live source | Plausible; current default is 1000 ms for both live and VOD. Increasing it may trade startup latency for tolerance but is not a proven fix. |
| 4 | Stream URL/container/demuxer mismatch | Plausible when provider extensions or returned commands do not describe the actual media. Current code validates URL shape, not media content. |
| 5 | Hardware-decoding or Windows output issue | Possible when media reaches decode/render, but the adapter already provides automatic software fallback after immediate start failure. Requires native event/log evidence. |
| 6 | Application recovery policy | The current policy intentionally waits for sustained buffering timeout or END/STOPPED before rebuilding. A provider that needs error-event recovery or a watchdog may not be covered. |

The current implementation therefore distinguishes `BUFFERING`, `PLAYING`, `STOPPED`, `ERROR`, `EOF`/END, and `RECOVERING` at the player boundary, but it cannot infer why a remote stream is buffering from libVLC state alone. Future diagnostics should correlate provider URL expiry, HTTP status, request headers/cookies, native libVLC event sequences, and media generation without logging secrets.

## 10. Known limitations and uncertainties

| Area | Current classification |
|---|---|
| M3U local/remote loading and extended-M3U live parsing | Implemented and tested at the stated boundary |
| M3U VOD/series catalogue semantics | Not implemented by the current M3U adapter |
| M3U stream-level headers/cookies | Not populated by current adapter; requires validation |
| Xtream live/VOD/series control-plane and URL resolution | Implemented at the stated adapter boundary; populated authorized acceptance remains separate |
| Xtream playback headers/cookies/session refresh | Not implemented as a provider-specific media contract |
| MAG handshake/profile/session/control plane | Partially implemented and provider-specific; authorized portal evidence remains required |
| MAG VOD/Series/catch-up product support | Not advertised; no claim |
| Stalker watchdog during playback | Unknown / requires authorized validation |
| HTTP(S) through libVLC | Current executable boundary |
| RTSP/RTMP from MAG legacy layer | Legacy layer can validate returned schemes, but current `ResolvedPlayback` URL boundary narrows application playback to HTTP(S) |
| UDP/RTP/SRT/RTMPS | Classified by domain URI model but not an executable current provider-to-player promise |
| Separate live/VOD caching policy | Not implemented; one adapter setting applies |
| Dedicated libVLC error-event recovery | Not implemented; subscription exists, recovery branch does not |
| Windows hardware-decoding policy | Automatic libVLC default with explicit software fallback; no D3D11-specific forced mode |
| Real-provider compatibility | Requires authorized sanitized fixtures and Windows validation |

## 11. Current verification status

The repository contains focused tests for M3U loading/parsing and registered playback, Xtream API/request building and VOD/Series translation, MAG protocol profiles/session/stream behavior, provider capability boundaries, the VLC adapter, player state machine, Qt native surface, subtitle handling, and native Windows/VLC lifecycle probes. The previous Windows release work also verified the bundled VLC runtime, Qt surface startup, and exact published EXE acceptance. Those tests validate the current software boundaries; they do not establish compatibility with every IPTV provider or portal.

The current status should be read as **implemented at the tested boundary**, **partial/provider-specific**, or **unknown/requires validation**, not as a universal claim that a URL supplied by any provider will play. No production credentials or provider payloads belong in this repository.

## 12. Recommended next implementation steps

These are recommendations only. This documentation-only task does not implement them.

1. Define an explicit provider-neutral media transport contract before widening `URL`/`ResolvedPlayback` beyond HTTP(S). The contract should specify which transports the Windows/libVLC build is expected to accept and how media options are validated.
2. Add authorized, sanitized fixtures that prove when M3U, Xtream, or MAG media requires a user-agent, referrer, cookie, Authorization header, or other stream-level option. Populate `TransportMetadata` only from that evidence and keep it ephemeral.
3. Decide whether MAG session lifetime requires a media-playback watchdog. If it does, model the lifecycle between provider session and player generation instead of copying a legacy Enigma2 timer into Qt.
4. Add a deliberate libVLC `EncounteredError` policy with tests if native error events are shown to be the missing recovery trigger. Do not restart healthy streams on ordinary Buffering callbacks.
5. Establish a provider-neutral catch-up/event contract before implementing any `timeshift` URL behavior. KiddaC’s provider-specific archive URLs are references, not a current SamoTech capability.
6. Add separate, evidence-backed live and VOD caching profiles only after controlled measurements show that a fixed cache is the relevant bottleneck.
7. Run populated authorized Xtream and MAG acceptance on Windows with redacted request/event telemetry, and keep real-provider validation separate from synthetic protocol tests.

## References

[1]: https://github.com/SamoTech/samotech-iptv-player/blob/main/src/samotech_iptv/application/dtos/playback.py "SamoTech provider-neutral playback DTOs"
[2]: https://github.com/SamoTech/samotech-iptv-player/blob/main/src/samotech_iptv/infrastructure/player/vlc_player_adapter.py "SamoTech libVLC player adapter"
[3]: https://github.com/SamoTech/samotech-iptv-player/blob/main/src/samotech_iptv/presentation/widgets/vlc_video_surface.py "SamoTech Qt native video surface"
[4]: https://github.com/SamoTech/samotech-iptv-player/blob/main/src/samotech_iptv/infrastructure/parsing/m3u_source_loader.py "SamoTech M3U source loader"
[5]: https://github.com/SamoTech/samotech-iptv-player/blob/main/src/samotech_iptv/infrastructure/providers/xtream_api_client.py "SamoTech Xtream API client"
[6]: https://github.com/SamoTech/samotech-iptv-player/blob/main/src/samotech_iptv/infrastructure/providers/xtream_request_builder.py "SamoTech Xtream request builder"
[7]: https://github.com/SamoTech/samotech-iptv-player/blob/main/providers/mag/protocol_profile.py "SamoTech MAG protocol profiles"
[8]: https://github.com/SamoTech/samotech-iptv-player/blob/main/providers/mag/session.py "SamoTech MAG session lifecycle"
[9]: https://wiki.videolan.org/VLC_command-line_help/ "VideoLAN VLC command-line help"
[10]: https://images.videolan.org/vlc/features.html "VideoLAN VLC features"
[11]: https://images.videolan.org/vlc/libvlc.html "VideoLAN libVLC overview"
[12]: https://github.com/SamoTech/samotech-iptv-player/blob/main/src/samotech_iptv/packaged_runtime.py "SamoTech bundled VLC runtime configuration"
[13]: https://github.com/kiddac/XStreamity "KiddaC XStreamity repository"
[14]: https://raw.githubusercontent.com/kiddac/XStreamity/master/XStreamity/usr/lib/enigma2/python/Plugins/Extensions/XStreamity/liveplayer.py "KiddaC XStreamity live Enigma2 player source"
[15]: https://github.com/kiddac/EStalker "KiddaC EStalker repository"
[16]: https://raw.githubusercontent.com/kiddac/EStalker/master/EStalker/usr/lib/enigma2/python/Plugins/Extensions/EStalker/liveplayer.py "KiddaC EStalker live Enigma2 player source"
[17]: https://raw.githubusercontent.com/kiddac/EStalker/master/EStalker/usr/lib/enigma2/python/Plugins/Extensions/EStalker/vodplayer.py "KiddaC EStalker VOD/series Enigma2 player source"
[18]: https://python-vlc.readthedocs.io/en/latest/ "python-vlc documentation"
