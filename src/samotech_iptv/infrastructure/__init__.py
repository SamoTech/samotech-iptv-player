"""Infrastructure layer — external-world adapters.

Implements the application-layer port interfaces using real technology.

Packages:
  network/       — async HTTP client (aiohttp)
  security/      — OS-keyring credential store
  configuration/ — env-var + override config provider
  providers/     — provider registry and factory (adapters in B.2+)
  database/      — SQLite repositories (Phase B.3)
  player/        — MPV / WinRT player adapters (Phase C)

Allowed dependencies:
  infrastructure  →  application.ports
  infrastructure  →  domain
  infrastructure  →  core
  infrastructure  →  stdlib
  infrastructure  →  third-party (aiohttp, keyring, …)

Forbidden:
  infrastructure  ←  presentation
  infrastructure  ←  application.use_cases  (only ports)
"""
