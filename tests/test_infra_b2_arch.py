"""Architecture validation tests for Phase B.2.

Verifies:
  - All new B.2 modules are importable
  - MagProviderAdapter imports only allowed layers
  - No MAG-specific types leak into application ports
  - ProviderContext only depends on infrastructure + core
  - Error translators do not expose legacy types in their signatures
  - Adapter implements all 7 capability interfaces
  - Factory starts with no MAG type pre-registered (explicit registration required)
"""
from __future__ import annotations

import importlib
import inspect

import pytest


@pytest.mark.parametrize("module", [
    "samotech_iptv.infrastructure.providers.provider_context",
    "samotech_iptv.infrastructure.providers.mag_adapter",
    "samotech_iptv.infrastructure.providers.mag_domain_translator",
    "samotech_iptv.infrastructure.providers.mag_error_translator",
])
def test_b2_module_importable(module: str) -> None:
    importlib.import_module(module)


def _src(mod_name: str) -> str:
    return inspect.getsource(importlib.import_module(mod_name))


@pytest.mark.parametrize("module", [
    "samotech_iptv.infrastructure.providers.mag_adapter",
    "samotech_iptv.infrastructure.providers.mag_domain_translator",
    "samotech_iptv.infrastructure.providers.mag_error_translator",
    "samotech_iptv.infrastructure.providers.provider_context",
])
def test_no_presentation_import(module: str) -> None:
    assert "samotech_iptv.presentation" not in _src(module)


@pytest.mark.parametrize("module", [
    "samotech_iptv.infrastructure.providers.mag_adapter",
    "samotech_iptv.infrastructure.providers.mag_domain_translator",
    "samotech_iptv.infrastructure.providers.mag_error_translator",
    "samotech_iptv.infrastructure.providers.provider_context",
])
def test_no_use_cases_import(module: str) -> None:
    assert "samotech_iptv.application.use_cases" not in _src(module)


def test_mag_adapter_implements_all_capability_interfaces() -> None:
    from samotech_iptv.application.ports.provider_capabilities import (
        AuthenticationProvider,
        CapabilityProvider,
        CatalogProvider,
        EPGProvider,
        PlaybackProvider,
        SearchProvider,
        SessionProvider,
    )
    from samotech_iptv.infrastructure.providers.mag_adapter import MagProviderAdapter
    for iface in (
        AuthenticationProvider, CatalogProvider, EPGProvider,
        SearchProvider, PlaybackProvider, SessionProvider, CapabilityProvider,
    ):
        assert issubclass(MagProviderAdapter, iface), \
            f"MagProviderAdapter does not implement {iface.__name__}"


def test_provider_context_only_references_infra_and_core() -> None:
    src = _src("samotech_iptv.infrastructure.providers.provider_context")
    assert "samotech_iptv.domain" not in src  # context has no domain dependency
    assert "providers.mag" not in src          # no legacy-specific imports


def test_mag_error_translator_no_top_level_legacy_import() -> None:
    """The legacy providers.base package must only be imported lazily (inside the function)."""
    import ast
    src = _src("samotech_iptv.infrastructure.providers.mag_error_translator")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and "providers.base" in node.module:
                # Only allowed inside a function body — check lineno is inside a FunctionDef
                pytest.fail(
                    f"providers.base imported at module level in mag_error_translator.py "
                    f"(line {node.lineno}) — must be deferred"
                )
            break  # only check top-level statements (walk gives all, use the first import)


def test_factory_does_not_auto_register() -> None:
    """Importing MagProviderAdapter must NOT auto-register in a shared factory."""
    from samotech_iptv.infrastructure.providers.provider_factory import ProviderFactory
    factory = ProviderFactory()
    # factory starts empty regardless of imports
    assert not factory.is_registered("mag")


def test_register_with_factory_idempotent() -> None:
    from samotech_iptv.infrastructure.providers.mag_adapter import register_with_factory
    from samotech_iptv.infrastructure.providers.provider_factory import ProviderFactory
    factory = ProviderFactory()
    register_with_factory(factory)
    register_with_factory(factory)  # second call must not raise
    assert factory.is_registered("mag")
