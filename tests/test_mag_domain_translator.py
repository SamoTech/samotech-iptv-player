from __future__ import annotations

from samotech_iptv.domain.value_objects.provider_id import ProviderId
from samotech_iptv.infrastructure.providers.mag_domain_translator import MagDomainTranslator

_PROVIDER_ID = ProviderId("mag-test")
_STREAM_COMMAND = "http://stream.example.test/live/channel-1.ts"


def _raw_channel(logo: str) -> dict[str, object]:
    return {
        "id": "1913027",
        "name": "Example Channel",
        "tv_genre_id": "7",
        "cmds": [{"url": _STREAM_COMMAND}],
        "logo": logo,
    }


def test_valid_logo_url_is_preserved() -> None:
    channel = MagDomainTranslator.channel(
        _raw_channel("https://cdn.example.test/logos/channel.png"), _PROVIDER_ID
    )

    assert str(channel.logo_url) == "https://cdn.example.test/logos/channel.png"
    assert str(channel.id) == "1913027"
    assert channel.name == "Example Channel"


def test_leading_hyphen_logo_url_is_normalized_without_dropping_channel() -> None:
    raw = _raw_channel("-http://cdn.example.test/logos/channel.png")
    channel = MagDomainTranslator.channel(raw, _PROVIDER_ID)

    assert str(channel.logo_url) == "http://cdn.example.test/logos/channel.png"
    assert str(channel.id) == "1913027"
    assert channel.name == "Example Channel"
    assert raw["cmds"] == [{"url": _STREAM_COMMAND}]


def test_unnormalizable_logo_becomes_none_and_command_is_unchanged() -> None:
    raw = _raw_channel("not-a-url")
    channel = MagDomainTranslator.channel(raw, _PROVIDER_ID)

    assert channel.logo_url is None
    assert str(channel.id) == "1913027"
    assert channel.name == "Example Channel"
    assert channel.category_id == "7"
    assert raw["cmds"] == [{"url": _STREAM_COMMAND}]


def test_missing_logo_is_allowed_for_channel_records() -> None:
    raw = _raw_channel("")
    raw.pop("logo")
    channel = MagDomainTranslator.channel(raw, _PROVIDER_ID)

    assert channel.logo_url is None
    assert raw["cmds"] == [{"url": _STREAM_COMMAND}]
