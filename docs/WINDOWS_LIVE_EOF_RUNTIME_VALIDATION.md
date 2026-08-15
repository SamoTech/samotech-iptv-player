# Windows Live EOF Runtime Validation

## Purpose and boundary

This procedure is the **manual authorized-runtime gate** for the bounded Live EOF recovery controller. It is not a real-provider CI test, does not establish the native root cause, and must not be marked complete from Linux, offscreen Qt, fake libVLC objects, or a Python import alone.

The controller is implemented and intentionally limited to current-session Live playback: it can rebuild media through the existing path after unexpected `END`, `STOPPED`, or a prolonged native `BUFFERING` state. It is bounded to five attempts in 45 seconds with 1/2/4/8/8-second backoff and only resets its budget after five seconds of sustained native `PLAYING`.

## Prerequisites

Use a 64-bit Windows desktop user session with matching 64-bit Python and VLC, the exact review worktree containing the recovery candidate, and an authorized Live IPTV source already configured through normal application controls. Keep provider settings, credentials, device identity, stream selection, VLC options, network caching, hardware-decoding settings, timeouts, qasync, and `PlayerShell` unchanged.

Before opening a provider, verify the local native runtime and deterministic controller tests:

```powershell
.\.venv\Scripts\Activate.ps1
python tests\vlc_native_lifecycle_probe.py
pytest -q tests\test_infra_vlc_player_adapter.py
```

The lifecycle probe must report `native_vlc_lifecycle=PASS`; it is provider-free and uses only a temporary local WAV source. The focused test suite proves deterministic event handling but does not substitute for the authorized runtime observation.

## Safe evidence rule

Record only aggregate playback and recovery state. Never copy, save, upload, or report provider URLs, stream URLs, MAC/device identities, usernames, passwords, tokens, cookies, authorization headers, provider payloads, or raw provider responses.

| Record | Permitted values |
|---|---|
| Playback start | `PASS` or `FAIL` |
| Failure reproduced | `YES` or `NO` |
| Native event | `BUFFERING`, `END`, `STOPPED`, or safe generic failure category |
| Recovery | Attempt number, `STARTED`, `PLAYING`, `STABLE`, `PLAY_FAILURE`, or `ABANDONED` |
| Channel switch safety | `PASS` or `FAIL` |
| Explicit stop safety | `PASS` or `FAIL` |

## Validation sequence

1. Start the supported desktop entry point with process-local safe diagnostics enabled:

   ```powershell
   $env:IPTV_DEBUG = '1'
   samotech-iptv
   ```

2. Select one already authorized **Live** channel through the normal application workflow. Confirm native `PLAYING`; do not copy the resolved URL.
3. Leave playback running without pause, seek, provider changes, or artificial traffic interference.
4. If no failure occurs during the chosen observation window, record `failure reproduced=NO` and stop. Do **not** call the issue fixed.
5. If native `BUFFERING`, `END`, or `STOPPED` occurs, record its safe event label and time relative to the local observation. Confirm that `PLAYBACK_RECOVERY` records one bounded attempt and that a new media generation is created; do not record a URL.
6. If recovery returns to native `PLAYING`, observe for at least five seconds. Record whether a `STABLE` result resets the recovery budget only after that window.
7. During a pending recovery delay, select another authorized Live channel. Confirm that the earlier channel never becomes audible or visible again and that the current selection is the only active stream.
8. Start one Live channel and stop it explicitly. Confirm that no recovery attempt begins after the expected stop callback.
9. Close the application normally. Do not alter the VLC installation, plugin cache, provider configuration, or recovery policy as part of this procedure.

## Result classification

| Result | Classification |
|---|---|
| Failure reproduced and bounded recovery returns to `PLAYING` | **A — application-level bounded recovery mitigated the observed interruption.** The upstream/native root cause remains unconfirmed. |
| Failure reproduced and all five bounded attempts fail or the 45-second window expires | **B — recovery operated as designed, but the upstream/native interruption persisted beyond its safety budget.** This is not by itself a controller defect. |
| Failure does not reproduce | **C — runtime validation did not reproduce the failure.** Do not claim a fix. |
| Recovery restarts the wrong channel, ignores an explicit action, duplicates loops, blocks the UI, or exceeds its configured policy | **D — recovery-controller defect.** Stop and preserve only the safe lifecycle sequence before changing architecture. |
| Native VLC lifecycle probe cannot load or initialize | **E — native VLC runtime unavailable.** Resolve Windows/VLC installation compatibility before evaluating IPTV playback. |

## Completion rule

This runtime gate is complete only when a real authorized Windows desktop session records the applicable safe results. The current Linux/offscreen and fake-backed results remain deterministic validation evidence only and do not establish a root-cause fix.
