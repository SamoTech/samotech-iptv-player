# Player 3 Authorized Provider Acceptance Procedure

## Scope and evidence boundary

This procedure separates synthetic validation, Linux-native validation, Windows-native validation, authorized Xtream validation, and authorized MAG validation. A result in one category must not be promoted into another category. The procedure records safe aggregate evidence only and never records usernames, passwords, MAC identities, portal URLs, tokens, cookies, authorization headers, resolved stream URLs, or raw provider payloads.

## Preconditions

Use an authorized test account and source entered interactively through the application or a locally approved secret mechanism. Do not add credentials to source, tests, CI, shell history, reports, or commits. Confirm that the native VLC installation and Qt environment are compatible before provider actions.

## Evidence record

Record only the following fields:

| Field | Allowed value |
| --- | --- |
| `AUTH` | `PASS` or `FAIL` |
| `LIVE_COUNT` | non-secret integer |
| `VOD_COUNT` | non-secret integer |
| `SERIES_COUNT` | non-secret integer |
| `EPISODE_COUNT` | non-secret integer or `UNKNOWN` |
| `EPG` | `PASS`, `FAIL`, or `NOT_SUPPORTED` |
| `PLAYBACK` | `PASS`, `FAIL`, or `NOT_SUPPORTED` |
| `RESUME` | `PASS`, `FAIL`, or `NOT_SUPPORTED` |
| `CATCHUP` | `PASS`, `FAIL`, or `NOT_SUPPORTED` |
| `RECOVERY` | `PASS`, `FAIL`, or `NOT_SUPPORTED` |
| `NOTES` | generic failure category only |

## Authorized Xtream sequence

Authenticate, load live categories and streams, load VOD categories and streams, load series categories and series, open one movie detail, open one series season and episode list, load one short EPG sample, resolve one live stream, resolve one movie, resolve one episode, and exercise stop/replay and rapid replacement. For non-live playback, verify resume only on a matching incomplete Movie or Episode record. Record aggregate counts and safe result categories only.

If an action is unsupported by the server, record `NOT_SUPPORTED`; do not retry indefinitely or infer that the action exists from a generic API response. A malformed individual record must be counted as rejected rather than causing a false full-catalogue success claim.

## Authorized MAG sequence

MAG acceptance remains conditional on a concrete authorized portal/session profile. Authenticate through the existing MAG adapter, load live categories and channels, load channel EPG, resolve and play one live channel, exercise session refresh and controlled invalid-session behavior, and record only aggregate outcomes. VOD, Series, Episodes, catch-up, and non-live playback remain `NOT_SUPPORTED` unless a future authorized trace proves an application-compatible provider contract and resolver path.

## Completion rule

A real-provider acceptance claim is valid only when the exact category is backed by observed evidence on the stated platform. Linux synthetic or local-native results do not establish Windows or populated-provider acceptance. Any unexecuted sequence remains `NOT EXECUTED` in the final audit.
