"""
Add/Edit server dialog window.
"""

from __future__ import annotations
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QComboBox, QSpinBox, QCheckBox, QPushButton, QDialogButtonBox,
    QTabWidget, QWidget, QLabel, QGroupBox, QMessageBox,
)
from PyQt6.QtCore import Qt

from ..models.profile_item import ProfileItem
from ..common.global_constants import Global
from ..common.utils import Utils


# Map EConfigType int to display name
CONFIG_TYPE_NAMES = {
    1: "VMess",
    2: "Shadowsocks",
    3: "Socks",
    7: "VLESS",
    8: "Trojan",
    9: "Hysteria2",
    10: "TUIC",
    11: "WireGuard",
    12: "Hysteria",
    13: "ANYTLS",
}

SECURITY_OPTIONS = ["auto", "none", "aes-128-gcm", "aes-256-gcm", "chacha20-poly1305"]
NETWORK_OPTIONS = Global.NETWORKS
STREAM_SECURITY_OPTIONS = Global.SECURITIES


class AddServerWindow(QDialog):
    """
    Dialog for adding or editing a proxy server profile.
    Mirrors the AddServerWindow variants in the original C# code.
    """

    def __init__(self, parent=None, profile: Optional[ProfileItem] = None):
        super().__init__(parent)
        self._profile = profile or ProfileItem()
        self._is_new = profile is None

        self.setWindowTitle("Add Server" if self._is_new else "Edit Server")
        self.setMinimumWidth(600)
        self.setModal(True)

        self._init_ui()
        self._load_profile(self._profile)

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Config type selector
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Protocol:"))
        self._type_combo = QComboBox()
        for type_id, name in CONFIG_TYPE_NAMES.items():
            self._type_combo.addItem(name, type_id)
        self._type_combo.currentIndexChanged.connect(self._on_type_changed)
        type_layout.addWidget(self._type_combo)
        type_layout.addStretch()
        layout.addLayout(type_layout)

        # Tab widget for different sections
        self._tabs = QTabWidget()
        layout.addWidget(self._tabs)

        # ── Basic tab ────────────────────────────────────────────────
        basic_tab = QWidget()
        form = QFormLayout(basic_tab)

        self._remarks_edit = QLineEdit()
        form.addRow("Remarks:", self._remarks_edit)

        self._address_edit = QLineEdit()
        form.addRow("Address:", self._address_edit)

        self._port_spin = QSpinBox()
        self._port_spin.setRange(1, 65535)
        self._port_spin.setValue(443)
        form.addRow("Port:", self._port_spin)

        self._id_edit = QLineEdit()
        form.addRow("ID / UUID:", self._id_edit)

        self._password_edit = QLineEdit()
        self._password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Password:", self._password_edit)

        self._security_combo = QComboBox()
        self._security_combo.addItems(SECURITY_OPTIONS)
        form.addRow("Security / Method:", self._security_combo)

        self._tabs.addTab(basic_tab, "Basic")

        # ── Transport tab ────────────────────────────────────────────
        transport_tab = QWidget()
        tform = QFormLayout(transport_tab)

        self._network_combo = QComboBox()
        self._network_combo.addItems(NETWORK_OPTIONS)
        tform.addRow("Network:", self._network_combo)

        self._stream_sec_combo = QComboBox()
        self._stream_sec_combo.addItems(STREAM_SECURITY_OPTIONS)
        tform.addRow("TLS:", self._stream_sec_combo)

        self._sni_edit = QLineEdit()
        tform.addRow("SNI:", self._sni_edit)

        self._alpn_edit = QLineEdit()
        tform.addRow("ALPN:", self._alpn_edit)

        self._fingerprint_combo = QComboBox()
        self._fingerprint_combo.addItems(Global.FINGERPRINTS)
        tform.addRow("Fingerprint:", self._fingerprint_combo)

        self._allow_insecure_check = QCheckBox("Allow Insecure")
        tform.addRow("", self._allow_insecure_check)

        self._host_edit = QLineEdit()
        tform.addRow("Host:", self._host_edit)

        self._path_edit = QLineEdit()
        tform.addRow("Path:", self._path_edit)

        self._tabs.addTab(transport_tab, "Transport")

        # ── Reality tab ──────────────────────────────────────────────
        reality_tab = QWidget()
        rform = QFormLayout(reality_tab)

        self._public_key_edit = QLineEdit()
        rform.addRow("Public Key:", self._public_key_edit)

        self._short_id_edit = QLineEdit()
        rform.addRow("Short ID:", self._short_id_edit)

        self._spider_x_edit = QLineEdit()
        rform.addRow("Spider X:", self._spider_x_edit)

        self._tabs.addTab(reality_tab, "Reality")

        # ── Buttons ──────────────────────────────────────────────────
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.button(QDialogButtonBox.StandardButton.Ok).setText("Save")
        btn_box.accepted.connect(self._on_save)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _load_profile(self, profile: ProfileItem) -> None:
        """Populate form from profile data."""
        # Type combo
        idx = self._type_combo.findData(profile.configType)
        if idx >= 0:
            self._type_combo.setCurrentIndex(idx)

        self._remarks_edit.setText(profile.remarks or "")
        self._address_edit.setText(profile.address or "")
        self._port_spin.setValue(profile.port or 443)
        self._id_edit.setText(profile.id or "")
        self._password_edit.setText(profile.password or "")

        sec_idx = self._security_combo.findText(profile.security or "")
        self._security_combo.setCurrentIndex(max(0, sec_idx))

        net_idx = self._network_combo.findText(profile.network or "tcp")
        self._network_combo.setCurrentIndex(max(0, net_idx))

        ss_idx = self._stream_sec_combo.findText(profile.streamSecurity or "none")
        self._stream_sec_combo.setCurrentIndex(max(0, ss_idx))

        self._sni_edit.setText(profile.sni or "")
        self._alpn_edit.setText(profile.alpn or "")

        fp_idx = self._fingerprint_combo.findText(profile.fingerprint or "")
        self._fingerprint_combo.setCurrentIndex(max(0, fp_idx))

        self._allow_insecure_check.setChecked(
            profile.allowInsecure in ("1", "true", "True")
        )
        self._host_edit.setText(profile.requestHost or "")
        self._path_edit.setText(profile.path or "")
        self._public_key_edit.setText(profile.publicKey or "")
        self._short_id_edit.setText(profile.shortId or "")
        self._spider_x_edit.setText(profile.spiderX or "")

    def _on_type_changed(self, idx: int) -> None:
        """Update form labels/visibility based on protocol type."""
        type_id = self._type_combo.currentData()
        # Could update label text and visibility per protocol type here

    def _on_save(self) -> None:
        """Validate and save profile data."""
        addr = self._address_edit.text().strip()
        port = self._port_spin.value()

        if not addr:
            QMessageBox.warning(self, "Validation Error", "Address cannot be empty.")
            return
        if not Utils.is_valid_port(port):
            QMessageBox.warning(self, "Validation Error", "Invalid port number.")
            return

        # Write form values back to profile
        p = self._profile
        p.configType = self._type_combo.currentData()
        p.remarks = self._remarks_edit.text().strip()
        p.address = addr
        p.port = port
        p.id = self._id_edit.text().strip()
        p.password = self._password_edit.text()
        p.security = self._security_combo.currentText()
        p.network = self._network_combo.currentText()
        p.streamSecurity = self._stream_sec_combo.currentText()
        p.sni = self._sni_edit.text().strip()
        p.alpn = self._alpn_edit.text().strip()
        p.fingerprint = self._fingerprint_combo.currentText()
        p.allowInsecure = "1" if self._allow_insecure_check.isChecked() else "0"
        p.requestHost = self._host_edit.text().strip()
        p.path = self._path_edit.text().strip()
        p.publicKey = self._public_key_edit.text().strip()
        p.shortId = self._short_id_edit.text().strip()
        p.spiderX = self._spider_x_edit.text().strip()

        if not p.indexId:
            p.indexId = Utils.generate_id()
        if not p.remarks:
            p.remarks = f"{p.address}:{p.port}"

        self.accept()

    @property
    def profile(self) -> ProfileItem:
        return self._profile
