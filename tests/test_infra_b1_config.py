"""Unit tests for ConfigurationProvider."""
from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from samotech_iptv.infrastructure.configuration.configuration_provider import (
    ConfigurationProvider,
)


class TestConfigurationProvider:
    def test_defaults_are_used_when_no_env_or_overrides(self) -> None:
        provider = ConfigurationProvider()
        cfg = provider.app_config()
        assert cfg.debug is False
        assert cfg.log_level == "INFO"

    def test_override_wins_over_default(self) -> None:
        provider = ConfigurationProvider(overrides={"debug": True, "log_level": "DEBUG"})
        cfg = provider.app_config()
        assert cfg.debug is True
        assert cfg.log_level == "DEBUG"

    def test_env_var_wins_over_default(self) -> None:
        with patch.dict(os.environ, {"SAMOTECH_LOG_LEVEL": "WARNING"}):
            provider = ConfigurationProvider()
            cfg = provider.app_config()
            assert cfg.log_level == "WARNING"

    def test_override_wins_over_env_var(self) -> None:
        with patch.dict(os.environ, {"SAMOTECH_LOG_LEVEL": "WARNING"}):
            provider = ConfigurationProvider(overrides={"log_level": "CRITICAL"})
            cfg = provider.app_config()
            assert cfg.log_level == "CRITICAL"

    def test_network_config_defaults(self) -> None:
        provider = ConfigurationProvider()
        cfg = provider.network_config()
        assert cfg.connect_timeout == pytest.approx(10.0)
        assert cfg.read_timeout == pytest.approx(30.0)
        assert cfg.max_retries == 3

    def test_network_config_from_env(self) -> None:
        with patch.dict(os.environ, {
            "SAMOTECH_CONNECT_TIMEOUT": "20.0",
            "SAMOTECH_MAX_RETRIES": "5",
        }):
            provider = ConfigurationProvider()
            cfg = provider.network_config()
            assert cfg.connect_timeout == pytest.approx(20.0)
            assert cfg.max_retries == 5

    def test_get_generic_key(self) -> None:
        provider = ConfigurationProvider(overrides={"my_key": "my_value"})
        assert provider.get("my_key") == "my_value"

    def test_get_returns_default_when_missing(self) -> None:
        provider = ConfigurationProvider()
        assert provider.get("nonexistent_key", "fallback") == "fallback"

    def test_bool_coercion_from_string(self) -> None:
        with patch.dict(os.environ, {"SAMOTECH_DEBUG": "true"}):
            provider = ConfigurationProvider()
            cfg = provider.app_config()
            assert cfg.debug is True

    def test_bool_coercion_1(self) -> None:
        with patch.dict(os.environ, {"SAMOTECH_DEBUG": "1"}):
            provider = ConfigurationProvider()
            cfg = provider.app_config()
            assert cfg.debug is True

    def test_bool_false_coercion(self) -> None:
        with patch.dict(os.environ, {"SAMOTECH_DEBUG": "false"}):
            provider = ConfigurationProvider()
            cfg = provider.app_config()
            assert cfg.debug is False
