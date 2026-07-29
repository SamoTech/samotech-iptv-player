# Infrastructure / Network

## Phase A Status

Empty scaffold.

## Phase B Plan

- `HttpClientFactory` — creates `aiohttp.ClientSession` with configured
  timeouts, TLS settings, and retry middleware.
- `RetryMiddleware` — exponential backoff (already in MAG provider, to be
  extracted here for reuse).
