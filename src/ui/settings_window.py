"""
Settings window - application options.
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QTabWidget, QWidget,
    QLineEdit, QSpinBox, QCheckBox, QPushButton, QComboBox, QLabel,
    QDialogButtonBox, QGroupBox, QFileDialog,
)
from PyQt6.QtCore import Qt

from ..models.config import Config
from ..common.global_constants import Global


class SettingsWindow(QDialog):
    """
    Application settings dialog.
    Mirrors OptionSettingWindow in the original C# code.
    """

    def __init__(self, parent=None, config: Config = None):
        super().__init__(parent)
        self._config = config or Config()
        self.setWindowTitle("Options")
        self.setMinimumWidth(550)
        self.setModal(True)
        self._init_ui()
        self._load_config()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        tabs = QTabWidget()
        layout.addWidget(tabs)

        # ── Core Settings ────────────────────────────────────────────
        core_tab = QWidget()
        cform = QFormLayout(core_tab)

        self._log_level_combo = QComboBox()
        self._log_level_combo.addItems(["debug", "info", "warning", "error", "none"])
        cform.addRow("Log Level:", self._log_level_combo)

        self._mux_check = QCheckBox("Enable Mux")
        cform.addRow("", self._mux_check)

        tabs.addTab(core_tab, "Core")

        # ── Inbound ──────────────────────────────────────────────────
        inbound_tab = QWidget()
        iform = QFormLayout(inbound_tab)

        self._socks_port_spin = QSpinBox()
        self._socks_port_spin.setRange(1, 65535)
        iform.addRow("SOCKS Port:", self._socks_port_spin)

        self._http_port_spin = QSpinBox()
        self._http_port_spin.setRange(1, 65535)
        iform.addRow("HTTP Port:", self._http_port_spin)

        self._udp_check = QCheckBox("UDP Enabled")
        iform.addRow("", self._udp_check)

        self._sniffing_check = QCheckBox("Sniffing Enabled")
        iform.addRow("", self._sniffing_check)

        tabs.addTab(inbound_tab, "Inbound")

        # ── Routing ──────────────────────────────────────────────────
        routing_tab = QWidget()
        rform = QFormLayout(routing_tab)

        self._domain_strategy_combo = QComboBox()
        self._domain_strategy_combo.addItems([
            "AsIs", "IPIfNonMatch", "IPOnDemand"
        ])
        rform.addRow("Domain Strategy:", self._domain_strategy_combo)

        self._domain_matcher_combo = QComboBox()
        self._domain_matcher_combo.addItems(["hybrid", "linear"])
        rform.addRow("Domain Matcher:", self._domain_matcher_combo)

        tabs.addTab(routing_tab, "Routing")

        # ── UI ───────────────────────────────────────────────────────
        ui_tab = QWidget()
        uform = QFormLayout(ui_tab)

        self._font_size_spin = QSpinBox()
        self._font_size_spin.setRange(8, 32)
        uform.addRow("Font Size:", self._font_size_spin)

        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["Follow System", "Light", "Dark"])
        uform.addRow("Theme:", self._theme_combo)

        self._lang_combo = QComboBox()
        self._lang_combo.addItems(["en", "zh-Hans", "zh-Hant", "ru", "fa"])
        uform.addRow("Language:", self._lang_combo)

        self._auto_run_check = QCheckBox("Auto-run on startup")
        uform.addRow("", self._auto_run_check)

        tabs.addTab(ui_tab, "UI")

        # ── System Proxy ─────────────────────────────────────────────
        proxy_tab = QWidget()
        pform = QFormLayout(proxy_tab)

        self._proxy_exc_edit = QLineEdit()
        pform.addRow("Exceptions:", self._proxy_exc_edit)

        self._pac_url_edit = QLineEdit()
        pform.addRow("PAC URL:", self._pac_url_edit)

        tabs.addTab(proxy_tab, "System Proxy")

        # ── Speed Test ───────────────────────────────────────────────
        speed_tab = QWidget()
        sform = QFormLayout(speed_tab)

        self._speedtest_url_edit = QLineEdit()
        sform.addRow("Speedtest URL:", self._speedtest_url_edit)

        self._ping_url_edit = QLineEdit()
        sform.addRow("Ping URL:", self._ping_url_edit)

        tabs.addTab(speed_tab, "Speed Test")

        # ── TUN Mode ─────────────────────────────────────────────────
        tun_tab = QWidget()
        tform = QFormLayout(tun_tab)

        self._tun_check = QCheckBox("Enable TUN Mode")
        tform.addRow("", self._tun_check)

        self._tun_stack_combo = QComboBox()
        self._tun_stack_combo.addItems(["gvisor", "system", "mixed"])
        tform.addRow("Stack:", self._tun_stack_combo)

        self._tun_mtu_spin = QSpinBox()
        self._tun_mtu_spin.setRange(576, 65535)
        tform.addRow("MTU:", self._tun_mtu_spin)

        tabs.addTab(tun_tab, "TUN")

        # ── Buttons ──────────────────────────────────────────────────
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self._on_save)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _load_config(self) -> None:
        cfg = self._config

        # Core
        log_idx = self._log_level_combo.findText(cfg.coreBasicItem.loglevel)
        self._log_level_combo.setCurrentIndex(max(0, log_idx))
        self._mux_check.setChecked(cfg.coreBasicItem.muxEnabled)

        # Inbound
        socks_port = 10808
        http_port = 10809
        udp_enabled = True
        sniffing = True
        if cfg.inbound:
            for ib in cfg.inbound:
                proto = ib.get("protocol", "") if isinstance(ib, dict) else getattr(ib, "protocol", "")
                port_val = ib.get("localPort", 0) if isinstance(ib, dict) else getattr(ib, "localPort", 0)
                udp_val = ib.get("udpEnabled", True) if isinstance(ib, dict) else getattr(ib, "udpEnabled", True)
                sniff_val = ib.get("sniffingEnabled", True) if isinstance(ib, dict) else getattr(ib, "sniffingEnabled", True)
                if proto == "socks":
                    socks_port = port_val
                    udp_enabled = udp_val
                    sniffing = sniff_val
                elif proto == "http":
                    http_port = port_val

        self._socks_port_spin.setValue(socks_port)
        self._http_port_spin.setValue(http_port)
        self._udp_check.setChecked(udp_enabled)
        self._sniffing_check.setChecked(sniffing)

        # Routing
        ds_idx = self._domain_strategy_combo.findText(cfg.routingBasicItem.domainStrategy)
        self._domain_strategy_combo.setCurrentIndex(max(0, ds_idx))
        dm_idx = self._domain_matcher_combo.findText(cfg.routingBasicItem.domainMatcher)
        self._domain_matcher_combo.setCurrentIndex(max(0, dm_idx))

        # UI
        self._font_size_spin.setValue(int(cfg.uiItem.currentFontSize))
        lang_idx = self._lang_combo.findText(cfg.uiItem.currentLanguage)
        self._lang_combo.setCurrentIndex(max(0, lang_idx))
        self._auto_run_check.setChecked(cfg.guiItem.autoRun != 0)

        # System Proxy
        self._proxy_exc_edit.setText(cfg.systemProxyItem.proxyExceptions)
        self._pac_url_edit.setText(cfg.systemProxyItem.pacUrl)

        # Speed Test
        self._speedtest_url_edit.setText(cfg.speedTestItem.speedTestUrl)
        self._ping_url_edit.setText(cfg.speedTestItem.speedPingTestUrl)

        # TUN
        self._tun_check.setChecked(cfg.tunModeItem.enableTun)
        stack_idx = self._tun_stack_combo.findText(cfg.tunModeItem.stack)
        self._tun_stack_combo.setCurrentIndex(max(0, stack_idx))
        self._tun_mtu_spin.setValue(cfg.tunModeItem.mtu)

    def _on_save(self) -> None:
        cfg = self._config

        # Core
        cfg.coreBasicItem.loglevel = self._log_level_combo.currentText()
        cfg.coreBasicItem.muxEnabled = self._mux_check.isChecked()

        # Inbound
        socks_port = self._socks_port_spin.value()
        http_port = self._http_port_spin.value()
        cfg.inbound = [
            {
                "protocol": "socks",
                "localPort": socks_port,
                "udpEnabled": self._udp_check.isChecked(),
                "sniffingEnabled": self._sniffing_check.isChecked(),
                "routeOnly": False,
            },
            {
                "protocol": "http",
                "localPort": http_port,
                "udpEnabled": False,
                "sniffingEnabled": self._sniffing_check.isChecked(),
                "routeOnly": False,
            },
        ]

        # Routing
        cfg.routingBasicItem.domainStrategy = self._domain_strategy_combo.currentText()
        cfg.routingBasicItem.domainMatcher = self._domain_matcher_combo.currentText()

        # UI
        cfg.uiItem.currentFontSize = float(self._font_size_spin.value())
        cfg.uiItem.currentLanguage = self._lang_combo.currentText()
        cfg.guiItem.autoRun = 1 if self._auto_run_check.isChecked() else 0

        # System Proxy
        cfg.systemProxyItem.proxyExceptions = self._proxy_exc_edit.text().strip()
        cfg.systemProxyItem.pacUrl = self._pac_url_edit.text().strip()

        # Speed Test
        cfg.speedTestItem.speedTestUrl = self._speedtest_url_edit.text().strip()
        cfg.speedTestItem.speedPingTestUrl = self._ping_url_edit.text().strip()

        # TUN
        cfg.tunModeItem.enableTun = self._tun_check.isChecked()
        cfg.tunModeItem.stack = self._tun_stack_combo.currentText()
        cfg.tunModeItem.mtu = self._tun_mtu_spin.value()

        self.accept()

    @property
    def config(self) -> Config:
        return self._config
