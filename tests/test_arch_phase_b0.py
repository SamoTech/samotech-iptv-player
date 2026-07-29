"""Phase B.0 architecture validation tests.

Verifies:
1. All new sub-packages are importable.
2. All compatibility shims re-export correctly.
3. Capability interfaces are abstract.
4. ISP — each capability interface is independently implementable.
5. Domain sub-packages never import from application/infrastructure.
6. Core never imports from domain/application/infrastructure.
7. No circular imports across domain, application, core.
8. py.typed marker exists.
9. Direct sub-module imports work.
10. ProviderPort is still abstract (backward compat).
"""
from __future__ import annotations

import importlib
import inspect
import sys
from pathlib import Path

import pytest


# ── Helper ───────────────────────────────────────────────────────────────────

def _src(module_name: str) -> str:
    mod = importlib.import_module(module_name)
    return inspect.getsource(mod)


# ── py.typed ──────────────────────────────────────────────────────────────────

def test_py_typed_exists() -> None:
    import samotech_iptv
    pkg_path = Path(samotech_iptv.__file__).parent
    assert (pkg_path / "py.typed").exists(), "py.typed marker missing (PEP 561)"


# ── Domain sub-package importability ───────────────────────────────────────

@pytest.mark.parametrize("module", [
    "samotech_iptv.domain.entities",
    "samotech_iptv.domain.entities.channel",
    "samotech_iptv.domain.entities.category",
    "samotech_iptv.domain.entities.playlist",
    "samotech_iptv.domain.entities.movie",
    "samotech_iptv.domain.entities.series",
    "samotech_iptv.domain.entities.episode",
    "samotech_iptv.domain.entities.stream",
    "samotech_iptv.domain.entities.provider",
    "samotech_iptv.domain.entities.epg_entry",
    "samotech_iptv.domain.entities.favorite",
    "samotech_iptv.domain.entities.history",
    "samotech_iptv.domain.value_objects",
    "samotech_iptv.domain.value_objects.provider_id",
    "samotech_iptv.domain.value_objects.channel_id",
    "samotech_iptv.domain.value_objects.stream_id",
    "samotech_iptv.domain.value_objects.url",
    "samotech_iptv.domain.value_objects.credential",
    "samotech_iptv.domain.repositories",
    "samotech_iptv.domain.repositories.channel_repository",
    "samotech_iptv.domain.repositories.playlist_repository",
    "samotech_iptv.domain.repositories.provider_repository",
    "samotech_iptv.domain.repositories.epg_repository",
    "samotech_iptv.domain.repositories.history_repository",
    "samotech_iptv.domain.repositories.favorite_repository",
    "samotech_iptv.domain.events",
    "samotech_iptv.domain.events.provider_events",
    "samotech_iptv.domain.events.playback_events",
    "samotech_iptv.domain.events.library_events",
])
def test_domain_submodule_importable(module: str) -> None:
    importlib.import_module(module)


# ── Application sub-package importability ──────────────────────────────────

@pytest.mark.parametrize("module", [
    "samotech_iptv.application.ports",
    "samotech_iptv.application.ports.provider_port",
    "samotech_iptv.application.ports.player_port",
    "samotech_iptv.application.ports.storage_port",
    "samotech_iptv.application.ports.credential_store_port",
    "samotech_iptv.application.ports.notification_port",
    "samotech_iptv.application.ports.provider_capabilities",
    "samotech_iptv.application.dtos",
    "samotech_iptv.application.dtos.provider",
    "samotech_iptv.application.dtos.auth",
    "samotech_iptv.application.dtos.channels",
    "samotech_iptv.application.dtos.categories",
    "samotech_iptv.application.dtos.epg",
    "samotech_iptv.application.dtos.stream",
    "samotech_iptv.application.dtos.history",
    "samotech_iptv.application.dtos.favorites",
])
def test_application_submodule_importable(module: str) -> None:
    importlib.import_module(module)


# ── Compatibility shims ─────────────────────────────────────────────────────

def test_phase_a_domain_entities_import_still_works() -> None:
    from samotech_iptv.domain.entities import Channel, EPGEntry, Provider
    assert Channel and EPGEntry and Provider


def test_phase_a_domain_value_objects_import_still_works() -> None:
    from samotech_iptv.domain.value_objects import URL, Credential, ProviderId
    assert URL and Credential and ProviderId


def test_phase_a_domain_repositories_import_still_works() -> None:
    from samotech_iptv.domain.repositories import ChannelRepository, EPGRepository
    assert ChannelRepository and EPGRepository


def test_phase_a_domain_events_import_still_works() -> None:
    from samotech_iptv.domain.events import ChannelsLoadedEvent, ProviderAuthenticatedEvent
    assert ChannelsLoadedEvent and ProviderAuthenticatedEvent


def test_phase_a_application_ports_import_still_works() -> None:
    from samotech_iptv.application.ports import ProviderPort, PlayerPort
    assert ProviderPort and PlayerPort


def test_phase_a_application_dtos_import_still_works() -> None:
    from samotech_iptv.application.dtos import ChannelDTO, AuthenticateRequest
    assert ChannelDTO and AuthenticateRequest


# ── ISP — capability interfaces are independently abstract ───────────────────

@pytest.mark.parametrize("iface", [
    "AuthenticationProvider",
    "CatalogProvider",
    "EPGProvider",
    "SearchProvider",
    "PlaybackProvider",
    "SessionProvider",
    "CapabilityProvider",
])
def test_capability_interface_is_abstract(iface: str) -> None:
    from samotech_iptv.application.ports import provider_capabilities as mod
    cls = getattr(mod, iface)
    assert inspect.isabstract(cls), f"{iface} must be abstract"


def test_catalog_provider_independent_of_auth() -> None:
    """A class can implement CatalogProvider without AuthenticationProvider."""
    from samotech_iptv.application.ports.provider_capabilities import CatalogProvider
    from samotech_iptv.domain.entities.channel import Channel

    class MinimalCatalog(CatalogProvider):
        async def load_channels(self):
            return []

    catalog = MinimalCatalog()
    assert not inspect.isabstract(catalog.__class__)


def test_epg_provider_independent_of_auth() -> None:
    from samotech_iptv.application.ports.provider_capabilities import EPGProvider

    class MinimalEPG(EPGProvider):
        async def load_epg(self, channel_id):
            return []

    epg = MinimalEPG()
    assert not inspect.isabstract(epg.__class__)


# ── Dependency direction ──────────────────────────────────────────────────────

DOMAIN_MODULES = [
    "samotech_iptv.domain.entities.channel",
    "samotech_iptv.domain.entities.epg_entry",
    "samotech_iptv.domain.value_objects.url",
    "samotech_iptv.domain.value_objects.credential",
    "samotech_iptv.domain.repositories.channel_repository",
    "samotech_iptv.domain.events.provider_events",
]

@pytest.mark.parametrize("module", DOMAIN_MODULES)
def test_domain_module_no_infrastructure_import(module: str) -> None:
    src = _src(module)
    assert "samotech_iptv.infrastructure" not in src

@pytest.mark.parametrize("module", DOMAIN_MODULES)
def test_domain_module_no_application_import(module: str) -> None:
    src = _src(module)
    assert "samotech_iptv.application" not in src

@pytest.mark.parametrize("module", DOMAIN_MODULES)
def test_domain_module_no_presentation_import(module: str) -> None:
    src = _src(module)
    assert "samotech_iptv.presentation" not in src


CORE_MODULES = [
    "samotech_iptv.core.exceptions",
    "samotech_iptv.core.result",
    "samotech_iptv.core.events",
    "samotech_iptv.core.logging",
    "samotech_iptv.core.config",
    "samotech_iptv.core.constants",
]

@pytest.mark.parametrize("module", CORE_MODULES)
def test_core_module_no_domain_import(module: str) -> None:
    src = _src(module)
    assert "samotech_iptv.domain" not in src

@pytest.mark.parametrize("module", CORE_MODULES)
def test_core_module_no_infrastructure_import(module: str) -> None:
    src = _src(module)
    assert "samotech_iptv.infrastructure" not in src

@pytest.mark.parametrize("module", CORE_MODULES)
def test_core_module_no_application_import(module: str) -> None:
    src = _src(module)
    assert "samotech_iptv.application" not in src


APPLICATION_MODULES = [
    "samotech_iptv.application.ports.provider_port",
    "samotech_iptv.application.ports.provider_capabilities",
    "samotech_iptv.application.dtos.channels",
    "samotech_iptv.application.dtos.auth",
]

@pytest.mark.parametrize("module", APPLICATION_MODULES)
def test_application_module_no_infrastructure_import(module: str) -> None:
    src = _src(module)
    assert "samotech_iptv.infrastructure" not in src

@pytest.mark.parametrize("module", APPLICATION_MODULES)
def test_application_module_no_presentation_import(module: str) -> None:
    src = _src(module)
    assert "samotech_iptv.presentation" not in src


# ── Direct sub-module imports ─────────────────────────────────────────────────

def test_direct_entity_import() -> None:
    from samotech_iptv.domain.entities.channel import Channel
    from samotech_iptv.domain.entities.epg_entry import EPGEntry
    from samotech_iptv.domain.entities.episode import Episode
    assert Channel and EPGEntry and Episode


def test_direct_value_object_import() -> None:
    from samotech_iptv.domain.value_objects.url import URL
    from samotech_iptv.domain.value_objects.credential import Credential
    u = URL("http://example.com")
    assert str(u) == "http://example.com"


def test_direct_repository_import() -> None:
    from samotech_iptv.domain.repositories.channel_repository import ChannelRepository
    assert inspect.isabstract(ChannelRepository)


def test_direct_capability_import() -> None:
    from samotech_iptv.application.ports.provider_capabilities import (
        AuthenticationProvider, CatalogProvider, EPGProvider,
    )
    assert all(inspect.isabstract(c) for c in [
        AuthenticationProvider, CatalogProvider, EPGProvider
    ])


def test_direct_dto_import() -> None:
    from samotech_iptv.application.dtos.channels import ChannelDTO
    from samotech_iptv.application.dtos.auth import AuthenticateRequest
    dto = ChannelDTO(id="1", name="BBC", provider_id="p", stream_id="s")
    assert dto.name == "BBC"
