"""
Application manager - singleton that coordinates all app components.
Mirrors ServiceLib/Manager/AppManager.cs.
"""

from __future__ import annotations
import os
import logging
import threading
from typing import Optional, List, Callable

from ..models.config import Config
from ..models.profile_item import ProfileItem
from ..models.sub_item import SubItem, RoutingItem, DNSItem
from ..handlers.config_handler import ConfigHandler
from ..handlers.database_handler import DatabaseHandler
from ..handlers.subscription_handler import SubscriptionHandler
from ..handlers.sys_proxy.sys_proxy_handler import SysProxyHandler
from ..services.speedtest_service import SpeedtestService
from ..manager.core_manager import CoreManager
from ..common.global_constants import Global
from ..common.utils import Utils

logger = logging.getLogger(__name__)


class AppManager:
    """
    Application-wide singleton manager.
    Mirrors ServiceLib/Manager/AppManager.cs.

    Usage:
        mgr = AppManager.instance()
        mgr.init()
    """

    _instance: Optional["AppManager"] = None
    _lock = threading.Lock()

    def __init__(self):
        self._config: Optional[Config] = None
        self._db: Optional[DatabaseHandler] = None
        self._core_manager: Optional[CoreManager] = None
        self._sub_handler: Optional[SubscriptionHandler] = None
        self._speedtest_service: Optional[SpeedtestService] = None

        self._config_dir: str = Utils.get_config_dir()
        self._bin_dir: str = os.path.join(Utils.get_app_dir(), Global.BIN_DIR)

        self._log_callback: Optional[Callable[[str], None]] = None
        self._proxy_enabled: bool = False
        self._active_profile_id: str = ""

    # ── Singleton ─────────────────────────────────────────────────────

    @classmethod
    def instance(cls) -> "AppManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    # ── Initialization ────────────────────────────────────────────────

    def init(self) -> bool:
        """
        Initialize all app components.
        Mirrors AppManager.InitApp().
        """
        self._setup_logging()

        # Load config
        self._config = ConfigHandler.load_config(self._config_dir)
        logger.info(f"Config loaded from {self._config_dir}")

        # Init database
        db_path = os.path.join(self._config_dir, DatabaseHandler.DB_FILE)
        self._db = DatabaseHandler(db_path)
        logger.info(f"Database initialized: {db_path}")

        # Init sub-components
        self._sub_handler = SubscriptionHandler(self._db, self._config)
        self._core_manager = CoreManager(self._config, self._config_dir, self._bin_dir)
        self._speedtest_service = SpeedtestService(
            ping_url=self._config.speedTestItem.speedPingTestUrl,
            speedtest_url=self._config.speedTestItem.speedTestUrl,
        )

        logger.info("AppManager initialized successfully.")
        return True

    def _setup_logging(self) -> None:
        """Configure Python logging."""
        log_file = os.path.join(Utils.get_logs_dir(), Global.GUI_LOG_FILE)
        handlers: list[logging.Handler] = [
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding="utf-8"),
        ]
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            handlers=handlers,
        )

    # ── App exit ──────────────────────────────────────────────────────

    def shutdown(self) -> None:
        """
        Clean shutdown - stop core, clear proxy, save config.
        Mirrors AppManager.AppExitAsync().
        """
        logger.info("Shutting down v2rayN...")
        self.stop_core()
        self.set_system_proxy(False)
        self.save_config()
        logger.info("Shutdown complete.")

    # ── Config ────────────────────────────────────────────────────────

    @property
    def config(self) -> Config:
        if self._config is None:
            raise RuntimeError("AppManager not initialized. Call init() first.")
        return self._config

    def save_config(self) -> None:
        ConfigHandler.save_config(self.config, self._config_dir)

    # ── Active profile ────────────────────────────────────────────────

    @property
    def active_profile_id(self) -> str:
        return self._active_profile_id or self.config.indexId

    @active_profile_id.setter
    def active_profile_id(self, value: str) -> None:
        self._active_profile_id = value
        self.config.indexId = value

    def get_active_profile(self) -> Optional[ProfileItem]:
        if self._db and self.active_profile_id:
            return self._db.get_profile(self.active_profile_id)
        return None

    # ── Core management ───────────────────────────────────────────────

    def set_log_callback(self, callback: Callable[[str], None]) -> None:
        self._log_callback = callback
        if self._core_manager:
            self._core_manager.set_log_callback(callback)

    def start_core(self, profile_id: Optional[str] = None) -> bool:
        """Start proxy core for the given or active profile."""
        if not self._core_manager:
            logger.error("CoreManager not initialized.")
            return False

        pid = profile_id or self.active_profile_id
        if not pid:
            logger.error("No active profile selected.")
            return False

        profile = self._db.get_profile(pid) if self._db else None
        if not profile:
            logger.error(f"Profile not found: {pid}")
            return False

        return self._core_manager.load_core(profile)

    def stop_core(self) -> None:
        if self._core_manager:
            self._core_manager.core_stop()

    @property
    def core_running(self) -> bool:
        return self._core_manager is not None and self._core_manager.is_running

    # ── System proxy ──────────────────────────────────────────────────

    def set_system_proxy(self, enable: bool) -> bool:
        """Enable or disable system proxy."""
        if enable:
            port = ConfigHandler.get_socks_port(self.config)
            exceptions = self.config.systemProxyItem.proxyExceptions
            ok = SysProxyHandler.set_proxy("127.0.0.1", port, exceptions)
        else:
            ok = SysProxyHandler.clear_proxy()

        self._proxy_enabled = enable and ok
        return ok

    @property
    def proxy_enabled(self) -> bool:
        return self._proxy_enabled

    # ── Profile management ────────────────────────────────────────────

    @property
    def db(self) -> DatabaseHandler:
        if self._db is None:
            raise RuntimeError("AppManager not initialized.")
        return self._db

    def get_profiles(self, subid: Optional[str] = None) -> List[ProfileItem]:
        return self._db.get_all_profiles(subid) if self._db else []

    def add_profile(self, profile: ProfileItem) -> None:
        if not profile.indexId:
            profile.indexId = Utils.generate_id()
        profile.addTime = Utils.timestamp()
        if self._db:
            self._db.upsert_profile(profile)

    def delete_profile(self, index_id: str) -> None:
        if self._db:
            self._db.delete_profile(index_id)
        if index_id == self.active_profile_id:
            self.stop_core()
            self.active_profile_id = ""

    def set_active_and_restart(self, index_id: str) -> bool:
        """Set active profile and restart core."""
        self.active_profile_id = index_id
        self.save_config()
        return self.start_core(index_id)

    # ── Subscription management ───────────────────────────────────────

    def update_subscription(
        self,
        sub_id: str = "",
        use_proxy: bool = False,
        callback: Optional[Callable[[bool, str], None]] = None,
    ) -> None:
        """Update subscriptions in a background thread."""
        if not self._sub_handler:
            return

        def _run():
            self._sub_handler.update_subscription(sub_id, use_proxy, callback)

        threading.Thread(target=_run, daemon=True).start()

    # ── Speed test ────────────────────────────────────────────────────

    def ping_profile(self, profile_id: str) -> int:
        """Return TCP latency (ms) for a profile. -1 = failed."""
        profile = self._db.get_profile(profile_id) if self._db else None
        if not profile or not self._speedtest_service:
            return -1
        return self._speedtest_service.ping_server(profile.address, profile.port)

    # ── Getters ───────────────────────────────────────────────────────

    @property
    def sub_handler(self) -> Optional[SubscriptionHandler]:
        return self._sub_handler

    @property
    def core_manager(self) -> Optional[CoreManager]:
        return self._core_manager

    @property
    def speedtest(self) -> Optional[SpeedtestService]:
        return self._speedtest_service
