"""Infrastructure layer — concrete adapters for ports.

This package contains all I/O-dependent implementations:
- Provider adapters (MAG, Xtream, M3U)
- Database repositories (SQLite via aiosqlite)
- Network client
- Security / keyring
- Configuration loaders

Phase A: structure only.  No concrete implementations yet.
Provider migration from ``providers/`` happens in Phase B.

Allowed dependencies:
  infrastructure  →  application (ports/DTOs)
  infrastructure  →  domain
  infrastructure  →  core
  infrastructure  →  third-party libraries (aiohttp, aiosqlite, keyring, …)

Forbidden:
  infrastructure  →  presentation
"""
