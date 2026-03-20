"""
Tests for configuration handler - load/save config.
"""

import sys
import os
import json
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from src.handlers.config_handler import ConfigHandler
from src.models.config import Config


class TestConfigHandler:
    """Tests for ConfigHandler."""

    def test_load_creates_default_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = ConfigHandler.load_config(tmpdir)
            assert cfg is not None
            assert isinstance(cfg, Config)

    def test_load_applies_default_inbound(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = ConfigHandler.load_config(tmpdir)
            assert len(cfg.inbound) >= 1

    def test_load_applies_default_language(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = ConfigHandler.load_config(tmpdir)
            assert cfg.uiItem.currentLanguage in ("en", "zh-Hans", "zh-Hant")

    def test_load_applies_default_speedtest_url(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = ConfigHandler.load_config(tmpdir)
            assert cfg.speedTestItem.speedTestUrl != ""
            assert cfg.speedTestItem.speedPingTestUrl != ""

    def test_save_and_reload(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = Config()
            cfg.indexId = "test-save-load"
            cfg.coreBasicItem.loglevel = "debug"
            cfg.uiItem.mainWidth = 1920

            ConfigHandler.save_config(cfg, tmpdir)

            # Verify file was created
            config_path = ConfigHandler.get_config_path(tmpdir)
            assert os.path.isfile(config_path)

            # Reload and verify
            cfg2 = ConfigHandler.load_config(tmpdir)
            assert cfg2.indexId == "test-save-load"
            assert cfg2.coreBasicItem.loglevel == "debug"
            assert cfg2.uiItem.mainWidth == 1920

    def test_load_from_existing_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data = {
                "indexId": "existing-config",
                "coreBasicItem": {"loglevel": "info"},
                "inbound": [{"protocol": "socks", "localPort": 11111}],
            }
            config_path = ConfigHandler.get_config_path(tmpdir)
            with open(config_path, "w") as f:
                json.dump(data, f)

            cfg = ConfigHandler.load_config(tmpdir)
            assert cfg.indexId == "existing-config"
            assert cfg.coreBasicItem.loglevel == "info"

    def test_save_creates_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = os.path.join(tmpdir, "nested", "config")
            cfg = Config()
            result = ConfigHandler.save_config(cfg, new_dir)
            assert result is True
            assert os.path.isfile(ConfigHandler.get_config_path(new_dir))

    def test_get_socks_port(self):
        cfg = Config()
        cfg.inbound = [
            {"protocol": "socks", "localPort": 12345},
            {"protocol": "http", "localPort": 12346},
        ]
        assert ConfigHandler.get_socks_port(cfg) == 12345
        assert ConfigHandler.get_http_port(cfg) == 12346

    def test_get_socks_port_default(self):
        cfg = Config()
        cfg.inbound = []
        assert ConfigHandler.get_socks_port(cfg) == 10808
        assert ConfigHandler.get_http_port(cfg) == 10809

    def test_load_invalid_json_returns_default(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = ConfigHandler.get_config_path(tmpdir)
            with open(config_path, "w") as f:
                f.write("not valid json {{{{")

            cfg = ConfigHandler.load_config(tmpdir)
            # Should return default config, not crash
            assert cfg is not None
            assert isinstance(cfg, Config)
