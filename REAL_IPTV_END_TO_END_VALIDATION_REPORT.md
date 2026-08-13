# REAL IPTV END-TO-END VALIDATION REPORT

## Overall Status

**PASS WITH LIMITATIONS.** Real M3U and Xtream provider operations were executed through the application adapters. The supplied M3U source was downloaded successfully, parsed, translated, and used for stream resolution. The real Xtream account authenticated successfully, loaded 187 live categories and 14,204 live channels with zero rejected records, and resolved a stream. The real MAG portal was reachable at DNS, TCP, and HTTP layers, but its handshake returned HTTP 200 with an empty JavaScript response rather than a JSON session payload; authentication therefore failed at the provider protocol boundary. Real VLC playback and Windows UI acceptance could not be verified because the sandbox has the Python `vlc` module but no usable libVLC runtime or desktop UI.

## M3U

| Check | Result |
|---|---|
| Registration | **VERIFIED** through the M3U application adapter equivalent. |
| Load channels | **PASS**. The external source returned HTTP 200 and the complete 5,162,339-byte playlist was downloaded. |
| Channels displayed | **NOT VERIFIED** in the Windows UI; the headless application boundary produced the channel records. |
| Stream resolution | **PASS** through the M3U adapter using the first translated channel. The resolved URL itself was not printed or stored in the report. |
| Playback | **NOT TESTED** because the sandbox lacks a usable libVLC runtime. |
| Records | **21,786 received / 21,786 translated / 0 rejected**. |
| First failure | None in source retrieval, parsing, translation, or stream resolution. UI display and VLC playback remain unverified. |

The M3U source was first downloaded with a bounded 180-second request. The application M3U parser and translator then processed the downloaded real playlist and returned 21,786 channels. The parser emitted warnings for invalid optional logo URLs, but those records remained valid channels and were not rejected.

## XTREAM

| Check | Result |
|---|---|
| Authentication | **PASS**. The real account returned an active authenticated response. |
| Categories | **PASS**, with **187** live categories returned by the Xtream adapter. |
| Channels | **PASS**. |
| Records | **14,204 received / 14,204 translated / 0 rejected**. |
| Playback | **NOT VERIFIED** because the sandbox has no usable libVLC runtime. Stream resolution passed. |
| Rapid switching | **NOT TESTED** with real VLC/UI. |

The real Xtream channel baseline was preserved exactly. Translation warnings were limited to invalid optional logo URLs; the affected channel records were retained, and the rejection count remained zero. A real stream URL was resolved through the application adapter without exposing it in output.

## VLC

| Check | Result | Evidence or limitation |
|---|---|---|
| Known-good stream | **NOT VERIFIED** | Python `vlc` is importable, but creating a libVLC instance fails with `NameError: no function 'libvlc_new'`. No system `libvlc` library or `vlc` executable is available. |
| H264 problematic stream | **NOT VERIFIED** | Requires a functioning libVLC runtime and an observable decoder event stream. |
| Hardware fallback | **AUTOMATED ONLY** | The focused adapter tests verify bounded retry and software fallback behavior; real decoder recovery was not possible in this environment. |
| Dead stream | **AUTOMATED ONLY** | Bounded failure behavior is covered by adapter tests; real VLC dead-stream behavior was not executable. |
| Stop → Play | **AUTOMATED ONLY** | Covered by adapter lifecycle tests, not by a real media player. |
| Rapid switching | **AUTOMATED ONLY** | Locking and serialized operations are covered by focused tests; no real UI/player switching was possible. |
| UI responsiveness | **NOT VERIFIED** | No Windows/Qt desktop session is available in the sandbox. |

The real VLC acceptance criteria are therefore **not claimed as passed**. The implementation’s deterministic regression tests pass, but decoder messages such as `get_buffer() failed`, `decode_slice_header`, and `no frame` could not be observed without libVLC.

## MAG REAL PORTAL

| Check | Result |
|---|---|
| Portal | **REACHABLE**. DNS resolved, TCP port 80 connected, and the portal landing request returned HTTP 200. |
| Authentication | **FAIL** at the provider protocol boundary. |
| Session | **FAIL** because authentication did not receive a session token. |
| Categories | **NOT RUN** after authentication failure. The adapter’s unsupported-category path remains covered by automated tests. |
| Channels | **NOT RUN** after authentication failure. |
| Session reuse | **NOT RUN** against the real portal. |
| Session re-authentication | **SIMULATED/AUTOMATED ONLY** through the existing deterministic MAG regression tests; real portal expiry was not reached. |
| Stream resolution | **NOT RUN** after authentication failure. |
| Playback | **NOT TESTED** because both authentication and libVLC runtime availability blocked the workflow. |

The first real MAG failure is **PROVIDER_PROTOCOL_FAILURE**, not `NETWORK_FAILURE`: the root handshake endpoint returned HTTP 200 with an empty response body (`text/javascript`) instead of a JSON object containing a token. The portal-path variant returned HTTP 404. The application consequently entered `authentication_failed` and did not bypass its authentication guard. No speculative compatibility change was made.

## DIAGNOSTICS

| Check | Result |
|---|---|
| PowerShell debug | **NOT VERIFIED**; the sandbox is Linux and has no Windows PowerShell desktop process. |
| Stage diagnostics | **PASS for executed headless adapter workflows**. M3U, Xtream, and MAG stages were exercised through application boundaries. |
| Tracebacks | **PASS for security handling**. Error evidence was reduced to safe exception types/status metadata; raw credential-bearing traces were not included in the report. |
| Timing | **PASS for network probes**. HTTP status, byte counts, and elapsed times were captured without sensitive request data. |
| Secret redaction | **PASS for captured validation output**. The harness checks found no MAC/device identity, bearer token, cookie, Authorization header, or credential-bearing URL in emitted diagnostic records. Resolved stream URLs were not printed. |

## AUTOMATED TESTS

| Check | Result |
|---|---|
| pytest | **PASS**. Full repository suite: 584 tests. |
| Focused tests | **PASS**. VLC, MAG lifecycle, MAG integration, and category tests passed; the previously recorded focused set contains 33 tests. |
| Black | **PASS**. |
| Ruff | **PASS**. |
| mypy | **PASS for modified implementation files; repository baseline remains failing** with 38 errors across 18 unrelated files. |
| diff-check | **PASS**. |

## GIT

| Item | Result |
|---|---|
| Branch | `main` |
| Commit | Existing repository HEAD; no code changes were made during this validation task. |
| Pushed | **NO new push**; no validation-time code change required a commit. |
| HEAD | Matches `origin/main` at the validation snapshot. |
| origin/main | Matches HEAD at the validation snapshot. |
| Remote verified | **YES**, by comparing `git rev-parse HEAD` and `git rev-parse origin/main`. |
| Working tree | **NOT CLEAN** because the reliability implementation and reports from the preceding task remain uncommitted. These were pre-existing task artifacts, not speculative changes from this validation run. |

## ROOT CAUSES

The evidence-backed real-world failures are limited to two environment/provider boundaries. The real MAG portal returned a non-JSON empty HTTP 200 handshake response, so the existing legacy MAG client could not extract a token. This is classified as **PROVIDER_PROTOCOL_FAILURE**. Real VLC playback could not be exercised because the sandbox contains the Python binding but not the native libVLC runtime, which is an **ENVIRONMENT_LIMITATION**, not an application failure demonstrated by this run.

The M3U and Xtream provider workflows did not reproduce the targeted loading failures. The Xtream category result in the first combined harness was invalid because that harness passed the adapter directly to a resolver-oriented category use case; a follow-up direct adapter call returned all 187 categories successfully. No code was changed in response to that harness mistake.

## FIXES

No code changes were made during this validation task. The previously implemented VLC/MAG reliability changes were preserved. In particular, the MAG authentication guard was not weakened and no compatibility hack was added for the real portal’s empty handshake response.

## REMAINING WORK

### VERIFIED

The supplied real M3U source was reachable, completely downloaded, parsed, translated into 21,786 channels, and used for stream resolution. The real Xtream provider authenticated, returned 187 categories, translated 14,204 live channels with zero rejected records, and resolved a stream. Automated VLC/MAG/category reliability tests, formatting, linting, and diff checks passed. Portal DNS/TCP/HTTP reachability was verified. Diagnostic output checks found no credential leakage.

### PENDING

Windows UI acceptance for M3U channel display, real Xtream playback, real MAG channel loading and playback, real VLC decoder fallback, dead-stream behavior, rapid switching, stop-to-play transitions, and UI responsiveness require a Windows desktop environment with libVLC installed and the provider workflows configured in the application UI.

### FAILED

The real MAG authentication attempt failed at the protocol boundary because the portal returned an empty non-JSON handshake response. MAG categories, channels, session reuse, stream resolution, and playback could not proceed after that first failure.

### NOT TESTED

Real portal session expiration and re-authentication, PowerShell debug capture, actual Windows UI rendering, and physical decoder-error recovery were not tested. They must not be described as production-verified based on this sandbox run.
