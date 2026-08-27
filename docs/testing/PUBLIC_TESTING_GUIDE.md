# Public Testing Guide — SamoTech IPTV Player

## Purpose and Scope

This guide supports the public-testing release. The application has passed architecture, application, security, deterministic-test, and Windows portable-packaging validation. It does **not** certify every commercial provider, playlist, portal, codec, network, or device environment, and it makes no universal compatibility claim. Test only sources you are authorized to use.

## Install and Launch

Download the Windows x64 portable EXE and the accompanying `SHA256SUMS.txt` file from the release. Verify the checksum before running the EXE. No separate Python or VLC installation is required for the validated portable path.

Normal launch uses `SamoTech-IPTV-Player-Windows-x64-v<version>.exe`. The optional `SamoTech-Debug.bat` launcher is for local troubleshooting: it keeps a Command Prompt open and preserves sanitized lifecycle output. It does not transmit data and it does not replace normal application launch.

## Add a Legitimate Source

| Source type | Supported public-testing setup | Notes |
|---|---|---|
| M3U / M3U8 | Select **Providers → Add IPTV Provider → Manual Add → Manual M3U Add**, then choose a local `.m3u`/`.m3u8` file or paste a playlist URL | Playlist groups, logos, `tvg-id`, `tvg-name`, and an available EPG URL remain source-data dependent |
| Xtream | Select **Manual Xtream Add**, then enter server URL, username, and password | The local application derives its internal provider identifier; do not include credentials in a bug report |
| MAG / Stalker | Select **Manual MAG / Stalker Add** only when you have an authorized portal/device-identity flow | Capability is limited to the existing implemented behavior; no unverified VOD, series, or catch-up claim is made |

Smart Import can locally detect source information and preview a masked summary. It does not claim a real network connection until the provider is added through its normal connection workflow.

## Play and Control Media

Choose a provider, load its catalogue, select a channel/movie/episode, and start playback. Use the on-screen controls for play/pause, stop, volume, mute, supported audio/subtitle tracks, aspect ratio, and fullscreen. Press **F** or select **Fullscreen** to enter/exit fullscreen. Live inputs intentionally do not present meaningless seek controls; VOD and series use the available position/duration controls when the media reports them.

## Open Safe Diagnostics

Select **Info** in player controls to open Playback Diagnostics. The report records only allow-listed values such as provider type, content type, safe playback state, transport hint, timing, recovery count, and error classification. Fields such as container, codec, resolution, FPS, and first-frame status are shown as `NOT_AVAILABLE` when libVLC has not safely exposed a measurement.

Use **Copy Diagnostic Report** and paste the resulting text into a GitHub issue. The copied report excludes passwords, usernames, private URLs, credential-bearing URLs, access tokens, cookies, authorization headers, and MAG device identities.

## Report a Problem

Create a GitHub bug report using the repository template. Include Windows version, SamoTech version, provider type, content type, whether the catalogue loaded, whether the stream opened, whether a first frame appeared, whether audio worked, buffering behavior, channel/episode switching behavior, and the safe copied diagnostic report.

> **Never post passwords, usernames, tokens, MAC addresses, cookies, authorization headers, private playlist URLs, or raw provider logs.**

## Screenshots

No screenshots are included in this guide because no image captured from the final tagged Windows artifact exists at documentation time. This avoids presenting a mock or stale interface as release evidence. Users may attach redacted screenshots to reports after ensuring that no private source data is visible.
