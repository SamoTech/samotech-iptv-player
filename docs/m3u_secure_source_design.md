# Secure M3U source design

Manual M3U registration supports local playlist paths, credential-free HTTP(S) URLs, and tokenized or credential-bearing URLs.

A local path or credential-free remote source is non-secret configuration and may be stored as provider metadata. A source with URL user-info, a query string, or a fragment is treated as sensitive because these components frequently contain access material. The complete sensitive source must be stored through the existing secure credential boundary; provider metadata retains only a sanitised, credential-free HTTP(S) source for identification and diagnostics.

At runtime, the M3U adapter must prefer a provider-scoped secure source value when present and otherwise use metadata. The full source must never be included in logs, status text, errors, or provider metadata.
