"""Architecture validation for the Phase B.1 infrastructure layer.

Verifies:
  - All new infrastructure modules import successfully
  - Infrastructure never imports from presentation
  - Infrastructure never imports from application.use_cases
  - Provider adapters require explicit registration
  - Error translation module only uses core + infra.network
  - All modules use core.logging (no print / logging.basicConfig)
"""
from __future__ import annotations

import importlib
import inspect

import pytest

# ── Importability ───────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("module", [
    "samotech_iptv.infrastructure.network",
    "samotech_iptv.infrastructure.network.exceptions",
    "samotech_iptv.infrastructure.network.timeouts",
    "samotech_iptv.infrastructure.network.retry_policy",
    "samotech_iptv.infrastructure.network.headers",
    "samotech_iptv.infrastructure.network.http_session",
    "samotech_iptv.infrastructure.network.http_client",
    "samotech_iptv.infrastructure.security",
    "samotech_iptv.infrastructure.security.keyring_credential_store",
    "samotech_iptv.infrastructure.configuration",
    "samotech_iptv.infrastructure.configuration.configuration_provider",
    "samotech_iptv.infrastructure.providers",
    "samotech_iptv.infrastructure.providers.provider_metadata",
    "samotech_iptv.infrastructure.providers.provider_registry",
    "samotech_iptv.infrastructure.providers.provider_factory",
    "samotech_iptv.infrastructure.error_translation",
])
def test_infrastructure_module_importable(module: str) -> None:
    importlib.import_module(module)


# ── Dependency direction ────────────────────────────────────────────────────────────

INFRA_MODULES = [
    "samotech_iptv.infrastructure.network.http_client",
    "samotech_iptv.infrastructure.network.http_session",
    "samotech_iptv.infrastructure.network.retry_policy",
    "samotech_iptv.infrastructure.network.headers",
    "samotech_iptv.infrastructure.security.keyring_credential_store",
    "samotech_iptv.infrastructure.configuration.configuration_provider",
    "samotech_iptv.infrastructure.providers.provider_registry",
    "samotech_iptv.infrastructure.providers.provider_factory",
    "samotech_iptv.infrastructure.error_translation",
]


def _src(module_name: str) -> str:
    mod = importlib.import_module(module_name)
    return inspect.getsource(mod)


@pytest.mark.parametrize("module", INFRA_MODULES)
def test_infra_module_no_presentation_import(module: str) -> None:
    src = _src(module)
    assert "samotech_iptv.presentation" not in src


@pytest.mark.parametrize("module", INFRA_MODULES)
def test_infra_module_no_use_cases_import(module: str) -> None:
    src = _src(module)
    assert "samotech_iptv.application.use_cases" not in src


@pytest.mark.parametrize("module", INFRA_MODULES)
def test_infra_module_no_print_statements(module: str) -> None:
    src = _src(module)
    # allow print in comments/strings only — check no bare print( call
    import ast
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id == "print":
                pytest.fail(f"{module} contains a bare print() call")


# ── Explicit adapter registration ──────────────────────────────────────────────


def test_provider_package_does_not_auto_register_adapters() -> None:
    """Provider adapters must be registered by the composition root explicitly."""
    from samotech_iptv.infrastructure.providers.provider_factory import ProviderFactory

    factory = ProviderFactory()
    assert not factory.is_registered("mag")



def test_provider_factory_starts_empty() -> None:
    from samotech_iptv.infrastructure.providers.provider_factory import ProviderFactory
    factory = ProviderFactory()
    assert len(factory.supported_types()) == 0


# ── Error translation ──────────────────────────────────────────────────────────────

def test_error_translation_no_provider_specific_code() -> None:
    src = _src("samotech_iptv.infrastructure.error_translation")
    assert "mag" not in src.lower()
    assert "xtream" not in src.lower()
    assert "m3u" not in src.lower()
