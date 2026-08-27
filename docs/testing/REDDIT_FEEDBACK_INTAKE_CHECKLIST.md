# Reddit Feedback Intake Checklist

This checklist is for developers reviewing public-testing feedback about SamoTech IPTV Player v0.1.6. It converts a post into a safe, reproducible engineering report without requesting private source data.

> **Never request or accept credentials, private playlist URLs, stream URLs, provider tokens, cookies, authorization headers, MAC addresses, device identifiers, or raw logs that contain them.** Ask testers to use the application's copied safe diagnostic report instead.

## 1. Minimum Reproduction Record

| Information to record | Safe example | Do not request |
|---|---|---|
| Release identity | `v0.1.6`, downloaded portable EXE | Installer path containing personal folders |
| Platform | Windows edition/build, CPU architecture, display count | Account name or device serial number |
| Source category | M3U file, M3U URL, Xtream, MAG/Stalker, or Smart Import | URL, server host, portal address, username, password, or MAC |
| Content category | Live TV, movie, episode, EPG, favorites, history, settings | Channel ID, stream ID, private title if sensitive |
| User action | “Selected a loaded live channel and pressed Play” | Captured network request or raw log |
| Expected versus observed behavior | “Expected retry after a denied start; observed error state” | Speculative codec/provider conclusion |
| Reproducibility | Always, intermittent, once; approximate local time | Full private account activity history |

## 2. Safe Diagnostic Evidence

Ask the tester to select **Info** in the player controls and paste the copied diagnostic report. This report is designed to include only allow-listed state, timing, recovery, platform, provider-type, and content-type values. Values not measured are represented as `NOT_AVAILABLE`.

If the diagnostic report is unavailable, request the exact visible application status text and whether the optional `SamoTech-Debug.bat` launcher was used. Debug output must be reviewed only after the tester confirms it contains no source URL, credential, token, cookie, authorization header, MAC, or device identifier.

## 3. Triage Labels

| Label | Use when | Initial action |
|---|---|---|
| `needs-reproduction` | Safe steps or version/platform evidence is incomplete | Ask only for missing safe fields from this checklist |
| `setup-ux` | Source entry, empty state, label, selection, or navigation issue | Validate through deterministic dialog or PlayerShell tests |
| `playback-state` | Loading, buffering, error, retry, stop, fullscreen, audio, subtitle, or control-state issue | Compare typed lifecycle state and safe diagnostic values |
| `provider-compatibility` | A legitimate source behaves differently from a generic playback contract | Do not infer support; request safe evidence and isolate provider boundary |
| `windows-windowing` | Focus, taskbar, multi-monitor, fullscreen restoration, Alt+Tab, or shortcut issue | Reproduce on Windows; do not claim Linux Qt equivalence |
| `privacy-security` | Possible secret disclosure, credential handling, diagnostic/log leakage, or unsafe copy | Stop public disclosure, redact evidence, and run the relevant security regression |
| `out-of-scope` | Requested backend, proxy, transport, client platform, or proprietary portal flow lacks a contract | Record the exact missing contract and avoid speculative implementation |

## 4. Engineering Decision Rules

A report may justify a code change only when it is reproducible with safe evidence, a deterministic regression can be added, and the change preserves the existing PySide6/libVLC/provider-boundary design. Feedback is not proof of universal codec support, HLS/media decoding, commercial provider compatibility, or MAG behavior.

If a P0/P1 public-testing defect is confirmed, complete the existing test, security, static, Windows packaging, checksum, and release process before considering another public release. Otherwise, record the issue and include it in the next evidence-driven milestone.

## 5. Known Boundaries to State Up Front

The v0.1.6 public-testing release has verified Windows packaging and safe lifecycle controls, but it does not certify every provider, codec, container, device, portal flow, multi-monitor configuration, or client platform. The Linux development environment also cannot validate decoded IPTV media because it has no local libVLC runtime.
