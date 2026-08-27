"""Unit tests for the single configuration composition boundary."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from samotech_iptv.core import config as core_config
from samotech_iptv.core.config import default_data_dir
from samotech_iptv.core.exceptions import ConfigurationError
from samotech_iptv.infrastructure.configuration.configuration_provider import (
    ConfigurationProvider,
)


class TestConfigurationProvider:
    def test_defaults_compose_a_complete_app_config(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            config = ConfigurationProvider().app_config()
        assert config.debug is False
        assert config.log_level == "INFO"
        assert config.data_dir == default_data_dir()
        assert config.network.connect_timeout == pytest.approx(10.0)
        assert config.player.buffer_size_mb == 16

    @pytest.mark.parametrize(
        ("platform", "environment", "expected_suffix"),
        [
            ("win32", {"LOCALAPPDATA": "C:/Users/test/AppData/Local"}, "SamoTech/IPTV Player"),
            ("darwin", {}, "Library/Application Support/SamoTech/IPTV Player"),
            ("linux", {"XDG_DATA_HOME": "/home/test/xdg-data"}, "SamoTech/IPTV Player"),
        ],
    )
    def test_default_data_dir_uses_platform_convention(
        self,
        platform: str,
        environment: dict[str, str],
        expected_suffix: str,
    ) -> None:
        with (
            patch.object(core_config.sys, "platform", platform),
            patch.dict(os.environ, environment, clear=True),
        ):
            resolved = default_data_dir()
        assert resolved.replace("\\", "/").endswith(expected_suffix)

    def test_explicit_override_wins_over_environment(self) -> None:
        with patch.dict(os.environ, {"IPTV_LOG_LEVEL": "WARNING"}, clear=True):
            config = ConfigurationProvider(overrides={"log_level": "critical"}).app_config()
        assert config.log_level == "CRITICAL"

    def test_ip_tv_environment_wins_over_default(self) -> None:
        with patch.dict(
            os.environ,
            {
                "IPTV_DEBUG": "true",
                "IPTV_LOG_LEVEL": "warning",
                "IPTV_DATA_DIR": "/var/lib/samotech",
                "IPTV_CONNECT_TIMEOUT": "20.0",
                "IPTV_READ_TIMEOUT": "60.0",
                "IPTV_MAX_RETRIES": "5",
                "IPTV_TLS_VERIFY": "false",
                "IPTV_BUFFER_MB": "32",
                "IPTV_HW_DECODE": "0",
            },
            clear=True,
        ):
            config = ConfigurationProvider().app_config()

        assert config.debug is True
        assert config.log_level == "WARNING"
        assert config.data_dir == "/var/lib/samotech"
        assert config.network.connect_timeout == pytest.approx(20.0)
        assert config.network.read_timeout == pytest.approx(60.0)
        assert config.network.max_retries == 5
        assert config.network.tls_verify is False
        assert config.player.buffer_size_mb == 32
        assert config.player.hardware_decode is False

    def test_legacy_environment_prefix_is_not_a_configuration_source(self) -> None:
        with patch.dict(os.environ, {"SAMOTECH_LOG_LEVEL": "CRITICAL"}, clear=True):
            config = ConfigurationProvider().app_config()
        assert config.log_level == "INFO"

    @pytest.mark.parametrize(
        ("overrides", "message"),
        [
            ({"debug": "sometimes"}, "debug must be a boolean value"),
            ({"connect_timeout": "never"}, "connect_timeout must be a number"),
            ({"max_retries": 0}, "max_retries must be at least one"),
            ({"buffer_mb": 0}, "buffer_mb must be greater than zero"),
        ],
    )
    def test_invalid_values_raise_configuration_error(
        self, overrides: dict[str, object], message: str
    ) -> None:
        with pytest.raises(ConfigurationError, match=message):
            ConfigurationProvider(overrides=overrides).app_config()

    def test_generic_get_uses_standard_precedence(self) -> None:
        with patch.dict(os.environ, {"IPTV_REGION": "env"}, clear=True):
            provider = ConfigurationProvider(overrides={"region": "override"})
            assert provider.get("region", "default") == "override"
        assert ConfigurationProvider().get("missing", "default") == "default"
