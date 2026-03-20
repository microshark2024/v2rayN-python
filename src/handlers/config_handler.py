"""
Configuration handler - load/save application config.
Mirrors ServiceLib/Handler/ConfigHandler.cs.
"""

from __future__ import annotations
import json
import os
import logging
from typing import Optional

from ..models.config import Config, InItem
from ..common.global_constants import Global
from ..common.utils import Utils

logger = logging.getLogger(__name__)


class ConfigHandler:
    """
    Handles loading and saving of the main application config file.
    """

    @staticmethod
    def get_config_path(config_dir: str) -> str:
        return os.path.join(config_dir, Global.CONFIG_FILE_NAME)

    @staticmethod
    def load_config(config_dir: str) -> Config:
        """
        Load configuration from disk, or create a default one.
        Mirrors ConfigHandler.LoadConfig() in C#.
        """
        path = ConfigHandler.get_config_path(config_dir)
        config = Config()

        if os.path.isfile(path):
            try:
                text = Utils.read_file(path)
                if text:
                    data = json.loads(text)
                    config = Config.from_dict(data)
                    logger.info(f"Loaded config from {path}")
            except Exception as e:
                logger.error(f"Failed to load config: {e}")

        # Ensure defaults are applied
        ConfigHandler._apply_defaults(config)
        return config

    @staticmethod
    def save_config(config: Config, config_dir: str) -> bool:
        """
        Save configuration to disk.
        Mirrors ConfigHandler.SaveConfig() in C#.
        """
        path = ConfigHandler.get_config_path(config_dir)
        try:
            os.makedirs(config_dir, exist_ok=True)
            text = json.dumps(config.to_dict(), ensure_ascii=False, indent=2)
            return Utils.write_file(path, text)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False

    @staticmethod
    def _apply_defaults(config: Config) -> None:
        """
        Apply default values for any missing/unset sections.
        Mirrors the default initialization logic in ConfigHandler.LoadConfig().
        """
        # Default inbound (SOCKS on 10808)
        if not config.inbound:
            config.inbound = [
                {
                    "protocol": "socks",
                    "localPort": 10808,
                    "udpEnabled": True,
                    "sniffingEnabled": True,
                    "routeOnly": False,
                },
                {
                    "protocol": "http",
                    "localPort": 10809,
                    "udpEnabled": False,
                    "sniffingEnabled": True,
                    "routeOnly": False,
                },
            ]

        # Default language
        if not config.uiItem.currentLanguage:
            import locale
            try:
                lang = locale.getlocale()[0] or ""
            except Exception:
                lang = ""
            if lang.startswith("zh"):
                config.uiItem.currentLanguage = "zh-Hans"
            else:
                config.uiItem.currentLanguage = "en"

        # Default speed test URL
        if not config.speedTestItem.speedTestUrl:
            config.speedTestItem.speedTestUrl = (
                "https://dl.google.com/dl/android/studio/install/3.4.1.0/"
                "android-studio-ide-183.5522156-windows.exe"
            )

        # Default ping URL
        if not config.speedTestItem.speedPingTestUrl:
            config.speedTestItem.speedPingTestUrl = "https://www.google.com/generate_204"

    @staticmethod
    def get_socks_port(config: Config) -> int:
        """Get the SOCKS inbound port from config."""
        for item in config.inbound:
            if isinstance(item, dict) and item.get("protocol") == "socks":
                return item.get("localPort", 10808)
            if hasattr(item, "protocol") and item.protocol == "socks":
                return item.localPort
        return 10808

    @staticmethod
    def get_http_port(config: Config) -> int:
        """Get the HTTP inbound port from config."""
        for item in config.inbound:
            if isinstance(item, dict) and item.get("protocol") == "http":
                return item.get("localPort", 10809)
            if hasattr(item, "protocol") and item.protocol == "http":
                return item.localPort
        return 10809
