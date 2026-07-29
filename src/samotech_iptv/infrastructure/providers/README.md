# Infrastructure / Providers

## Phase A Status

Empty scaffold.  The legacy `providers/` package at the repository root
remains untouched.

## Phase B Plan

1. Implement `MagProviderAdapter(ProviderPort)` that wraps the existing
   `MAGProvider` from `providers/mag_provider.py`.
2. Register via the application-layer `ProviderRegistry`.
3. Keep `providers/` importable for the migration window.
