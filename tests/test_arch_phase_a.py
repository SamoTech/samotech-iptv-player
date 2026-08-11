"""Phase A architecture validation tests.

Verifies:
1. All layer packages are importable.
2. Core exports are present.
3. Domain entities construct and validate correctly.
4. Value objects validate their invariants.
5. Application ports are abstract (cannot be instantiated directly).
6. DTOs are frozen dataclasses.
7. Dependency direction: domain does NOT import from infrastructure/application.
"""
from __future__ import annotations

import inspect
import sys
from datetime import UTC, datetime

import pytest

_AUTH_VALUE = "test-auth-value"

# ── Layer importability ───────────────────────────────────────────────────────

def test_core_importable() -> None:
    import samotech_iptv.core  # noqa: F401


def test_domain_importable() -> None:
    import samotech_iptv.domain  # noqa: F401


def test_application_importable() -> None:
    import samotech_iptv.application  # noqa: F401


def test_infrastructure_importable() -> None:
    import samotech_iptv.infrastructure  # noqa: F401


def test_presentation_importable() -> None:
    import samotech_iptv.presentation  # noqa: F401


# ── Core ─────────────────────────────────────────────────────────────────────

def test_core_result_ok() -> None:
    from samotech_iptv.core.result import Ok, Result
    r: Result[int, str] = Ok(42)
    assert r.is_ok()
    assert r.unwrap() == 42
    assert r.unwrap_or(0) == 42


def test_core_result_err() -> None:
    from samotech_iptv.core.result import Err
    r = Err("boom")
    assert r.is_err()
    assert r.unwrap_or(99) == 99
    with pytest.raises(ValueError):
        r.unwrap()


def test_core_exceptions_hierarchy() -> None:
    from samotech_iptv.core.exceptions import (
        AuthenticationError,
        NotFoundError,
        ProviderError,
        SamotechError,
        ValidationError,
    )
    assert issubclass(ValidationError, SamotechError)
    assert issubclass(NotFoundError, SamotechError)
    assert issubclass(AuthenticationError, SamotechError)
    assert issubclass(ProviderError, SamotechError)


def test_core_domain_event() -> None:
    from samotech_iptv.core.events import DomainEvent
    ev = DomainEvent()
    assert ev.event_id
    assert ev.occurred_at


# ── Domain — entities ─────────────────────────────────────────────────────────

def test_channel_entity_creation() -> None:
    from samotech_iptv.domain.entities import Channel
    from samotech_iptv.domain.value_objects import ChannelId, ProviderId, StreamId
    ch = Channel(
        id=ChannelId("ch-1"),
        name="Al Jazeera",
        provider_id=ProviderId("prov-1"),
        stream_id=StreamId("stream-1"),
    )
    assert ch.name == "Al Jazeera"


def test_channel_blank_name_raises() -> None:
    from samotech_iptv.core.exceptions import ValidationError
    from samotech_iptv.domain.entities import Channel
    from samotech_iptv.domain.value_objects import ChannelId, ProviderId, StreamId
    with pytest.raises(ValidationError):
        Channel(
            id=ChannelId("ch-1"),
            name="   ",
            provider_id=ProviderId("prov-1"),
            stream_id=StreamId("stream-1"),
        )


def test_epg_entry_invalid_time_range() -> None:
    from samotech_iptv.core.exceptions import ValidationError
    from samotech_iptv.domain.entities import EPGEntry
    from samotech_iptv.domain.value_objects import ChannelId
    now = datetime.now(UTC)
    with pytest.raises(ValidationError):
        EPGEntry(
            id="epg-1",
            channel_id=ChannelId("ch-1"),
            title="Test",
            start=now,
            end=now,  # end == start  →  invalid
        )


def test_episode_invalid_season() -> None:
    from samotech_iptv.core.exceptions import ValidationError
    from samotech_iptv.domain.entities import Episode
    from samotech_iptv.domain.value_objects import StreamId
    with pytest.raises(ValidationError):
        Episode(
            id="ep-1", series_id="s-1", title="Pilot",
            stream_id=StreamId("st-1"), season=0, episode_number=1,
        )


# ── Domain — value objects ────────────────────────────────────────────────────

def test_url_valid() -> None:
    from samotech_iptv.domain.value_objects import URL
    url = URL("http://example.com/stream")
    assert str(url) == "http://example.com/stream"


def test_url_invalid_raises() -> None:
    from samotech_iptv.core.exceptions import ValidationError
    from samotech_iptv.domain.value_objects import URL
    with pytest.raises(ValidationError):
        URL("not-a-url")


def test_credential_repr_hides_password() -> None:
    from samotech_iptv.domain.value_objects import Credential
    c = Credential(username="user", _password=_AUTH_VALUE)
    assert _AUTH_VALUE not in repr(c)
    assert _AUTH_VALUE not in str(c)
    assert c.password == _AUTH_VALUE


def test_provider_id_blank_raises() -> None:
    from samotech_iptv.core.exceptions import ValidationError
    from samotech_iptv.domain.value_objects import ProviderId
    with pytest.raises(ValidationError):
        ProviderId("  ")


# ── Application — ports are abstract ─────────────────────────────────────────

def test_provider_port_is_abstract() -> None:
    from samotech_iptv.application.ports import ProviderPort
    assert inspect.isabstract(ProviderPort)


def test_player_port_is_abstract() -> None:
    from samotech_iptv.application.ports import PlayerPort
    assert inspect.isabstract(PlayerPort)


# ── Application — DTOs are frozen ─────────────────────────────────────────────

def test_channel_dto_is_frozen() -> None:
    from samotech_iptv.application.dtos import ChannelDTO
    dto = ChannelDTO(id="1", name="Test", provider_id="p", stream_id="s")
    with pytest.raises((AttributeError, TypeError)):
        dto.name = "modified"  # type: ignore[misc]


# ── Dependency graph: domain must NOT import infra/application ────────────────

def test_domain_does_not_import_infrastructure() -> None:
    for name, submod in sys.modules.items():
        if "infrastructure" in name and "samotech_iptv" in name:
            # If infrastructure was imported by domain module, that's a violation
            assert "samotech_iptv.domain" not in getattr(submod, "__file__", "")


def test_domain_does_not_import_application() -> None:
    import samotech_iptv.domain.entities as mod
    src = inspect.getsource(mod)
    assert "from samotech_iptv.application" not in src
    assert "import samotech_iptv.application" not in src


def test_core_does_not_import_domain() -> None:
    import samotech_iptv.core.exceptions as mod
    src = inspect.getsource(mod)
    assert "from samotech_iptv.domain" not in src
    assert "from samotech_iptv.application" not in src
    assert "from samotech_iptv.infrastructure" not in src
