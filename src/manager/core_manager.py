"""
Core manager - start/stop proxy core processes.
Mirrors ServiceLib/Manager/CoreManager.cs.
"""

from __future__ import annotations
import os
import platform
import logging
import stat
from typing import Optional, Callable

from ..models.config import Config
from ..models.profile_item import ProfileItem
from ..services.process_service import ProcessService
from ..services.core_config_service import CoreConfigService
from ..common.global_constants import Global
from ..common.utils import Utils

logger = logging.getLogger(__name__)


class CoreManager:
    """
    Manages proxy core processes (v2ray, xray, sing-box, etc.).
    Mirrors ServiceLib/Manager/CoreManager.cs.
    """

    # Map ECoreType int values to core executable name hints
    CORE_EXE_MAP = {
        1: "v2ray",
        2: "xray",
        4: "v2ray",
        13: "mihomo",
        21: "hysteria",
        22: "naive",
        23: "tuic",
        24: "sing-box",
        25: "juicity",
        26: "hysteria",
        27: "brook",
        28: "overtls",
        29: "shadowquic",
        30: "mieru",
    }

    # Config types that are natively supported by v2ray/xray
    V2RAY_CONFIG_TYPES = {1, 2, 3, 7, 8}  # VMess, SS, Socks, VLESS, Trojan

    # Config types that need sing-box
    SINGBOX_CONFIG_TYPES = {9, 10, 11}  # Hysteria2, TUIC, WireGuard

    def __init__(self, config: Config, config_dir: str, bin_dir: str):
        self.config = config
        self.config_dir = config_dir
        self.bin_dir = bin_dir
        self._main_process: Optional[ProcessService] = None
        self._log_callback: Optional[Callable[[str], None]] = None
        self._core_config_service = CoreConfigService(config, config_dir)

    def set_log_callback(self, callback: Callable[[str], None]) -> None:
        self._log_callback = callback

    # ── Core lifecycle ────────────────────────────────────────────────

    def load_core(self, profile: ProfileItem) -> bool:
        """
        Start the appropriate proxy core for the given profile.
        Mirrors CoreManager.LoadCore().

        Returns True if core started successfully.
        """
        self.core_stop()

        core_type = self._detect_core_type(profile)
        exe = self._find_core_executable(core_type)
        if not exe:
            logger.error(f"Core executable not found for type {core_type}")
            return False

        config_path = os.path.join(self.config_dir, Global.CORE_CONFIG_FILE_NAME)

        # Generate core config file
        if core_type == 24:  # sing-box
            self._core_config_service.generate_singbox_config(
                profile,
                output_path=config_path,
            )
        else:
            socks_port = self._get_socks_port()
            http_port = self._get_http_port()
            self._core_config_service.generate_v2ray_config(
                profile,
                output_path=config_path,
                inbound_port=socks_port,
                http_port=http_port,
            )

        self._main_process = ProcessService(
            executable=exe,
            config_path=config_path,
            display_log=profile.displayLog,
            log_callback=self._log_callback,
        )
        started = self._main_process.start()
        if not started:
            logger.error("Failed to start core process")
            return False

        logger.info(f"Core started: {os.path.basename(exe)} for profile {profile.remarks}")
        return True

    def core_stop(self) -> None:
        """Stop the running proxy core."""
        if self._main_process:
            self._main_process.stop()
            self._main_process = None

    @property
    def is_running(self) -> bool:
        return self._main_process is not None and self._main_process.is_running

    # ── Core detection ────────────────────────────────────────────────

    def _detect_core_type(self, profile: ProfileItem) -> int:
        """Determine which ECoreType to use for a profile."""
        # Profile may have a preferred core type
        if profile.coreType:
            return profile.coreType

        ct = profile.configType
        if ct in self.SINGBOX_CONFIG_TYPES:
            return 24  # sing-box
        # Default: Xray (supports VMess, VLESS, SS, Trojan)
        return 2

    def _find_core_executable(self, core_type: int) -> Optional[str]:
        """
        Find the core executable file path.
        Searches in bin_dir.
        """
        base_name = self.CORE_EXE_MAP.get(core_type, "xray")
        candidates = [base_name]
        if platform.system() == "Windows":
            candidates = [f"{base_name}.exe"]

        for name in candidates:
            path = os.path.join(self.bin_dir, name)
            if os.path.isfile(path):
                self._ensure_executable(path)
                return path

            # Try subdirectory (e.g. bin/xray/xray)
            sub_path = os.path.join(self.bin_dir, base_name, name)
            if os.path.isfile(sub_path):
                self._ensure_executable(sub_path)
                return sub_path

        logger.warning(f"Core executable '{base_name}' not found in {self.bin_dir}")
        return None

    def _ensure_executable(self, path: str) -> None:
        """Make file executable on Unix-like systems."""
        if platform.system() != "Windows":
            try:
                st = os.stat(path)
                os.chmod(path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
            except Exception as e:
                logger.warning(f"Could not chmod {path}: {e}")

    # ── Port helpers ──────────────────────────────────────────────────

    def _get_socks_port(self) -> int:
        from ..handlers.config_handler import ConfigHandler
        return ConfigHandler.get_socks_port(self.config)

    def _get_http_port(self) -> int:
        from ..handlers.config_handler import ConfigHandler
        return ConfigHandler.get_http_port(self.config)

    # ── Available cores ───────────────────────────────────────────────

    def get_available_cores(self) -> list[str]:
        """Return names of all core executables found in bin_dir."""
        found = []
        if not os.path.isdir(self.bin_dir):
            return found
        for fname in os.listdir(self.bin_dir):
            path = os.path.join(self.bin_dir, fname)
            if os.path.isfile(path) and os.access(path, os.X_OK):
                found.append(fname)
            elif os.path.isdir(path):
                # Check subdirectory
                for sub in os.listdir(path):
                    sub_path = os.path.join(path, sub)
                    if os.path.isfile(sub_path) and os.access(sub_path, os.X_OK):
                        found.append(f"{fname}/{sub}")
        return found
