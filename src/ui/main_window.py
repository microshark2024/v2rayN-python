"""
Main application window.
Mirrors MainWindow / MainWindowViewModel from the original C# code.
"""

from __future__ import annotations
import os
import threading
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QToolBar, QPushButton, QLabel, QStatusBar,
    QMenu, QMenuBar, QSystemTrayIcon, QApplication, QSplitter,
    QTextEdit, QHeaderView, QMessageBox, QDialog, QComboBox,
    QAbstractItemView, QSizePolicy, QInputDialog, QFileDialog,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QAction, QIcon, QFont, QColor, QClipboard

from ..manager.app_manager import AppManager
from ..models.profile_item import ProfileItem
from ..models.sub_item import SubItem
from ..handlers.fmt.v2ray_fmt import V2rayFmt
from ..common.utils import Utils
from ..common.global_constants import Global


# ── Worker threads ────────────────────────────────────────────────────────────

class UpdateSubWorker(QThread):
    """Background thread for subscription updates."""
    progress = pyqtSignal(bool, str)
    finished = pyqtSignal()

    def __init__(self, mgr: AppManager, sub_id: str = "", use_proxy: bool = False):
        super().__init__()
        self._mgr = mgr
        self._sub_id = sub_id
        self._use_proxy = use_proxy

    def run(self):
        if not self._mgr.sub_handler:
            self.progress.emit(False, "Subscription handler not initialized")
            self.finished.emit()
            return
        self._mgr.sub_handler.update_subscription(
            self._sub_id,
            self._use_proxy,
            lambda ok, msg: self.progress.emit(ok, msg),
        )
        self.finished.emit()


class PingWorker(QThread):
    """Background thread for ping tests."""
    result = pyqtSignal(str, int)   # (index_id, delay_ms)
    finished = pyqtSignal()

    def __init__(self, mgr: AppManager, profile_ids: list[str]):
        super().__init__()
        self._mgr = mgr
        self._ids = profile_ids

    def run(self):
        for pid in self._ids:
            delay = self._mgr.ping_profile(pid)
            self.result.emit(pid, delay)
        self.finished.emit()


# ── Main window ───────────────────────────────────────────────────────────────

CONFIG_TYPE_NAMES = {
    1: "VMess", 2: "SS", 3: "Socks", 7: "VLESS", 8: "Trojan",
    9: "HY2", 10: "TUIC", 11: "WG", 12: "HY", 13: "ANY", 99: "Custom",
}


class MainWindow(QMainWindow):
    """
    Main application window.
    Mirrors MainWindow in the original C# code.
    """

    log_message = pyqtSignal(str)

    def __init__(self, app_manager: AppManager):
        super().__init__()
        self._mgr = app_manager
        self._tray: Optional[QSystemTrayIcon] = None
        self._current_sub_id: str = ""
        self._log_max_lines = Global.MAX_LOG_LINES

        self.setWindowTitle(f"{Global.APP_NAME} {Global.APP_VERSION}")
        self.setMinimumSize(1000, 600)

        self._init_menu()
        self._init_toolbar()
        self._init_central()
        self._init_statusbar()
        self._init_tray()

        self.log_message.connect(self._append_log)

        # Register log callback
        self._mgr.set_log_callback(
            lambda msg: self.log_message.emit(msg)
        )

        # Load server list
        self._refresh_profiles()
        self._refresh_sub_combo()

        # Restore window geometry
        cfg = self._mgr.config
        self.resize(cfg.uiItem.mainWidth, cfg.uiItem.mainHeight)

    # ── Menu bar ──────────────────────────────────────────────────────

    def _init_menu(self) -> None:
        menubar = self.menuBar()

        # ── File ──────────────────────────────────────────────────
        file_menu = menubar.addMenu("File")

        act_import_clipboard = QAction("Import from Clipboard", self)
        act_import_clipboard.setShortcut("Ctrl+V")
        act_import_clipboard.triggered.connect(self._on_import_clipboard)
        file_menu.addAction(act_import_clipboard)

        act_import_file = QAction("Import from File…", self)
        act_import_file.triggered.connect(self._on_import_file)
        file_menu.addAction(act_import_file)

        file_menu.addSeparator()

        act_export = QAction("Export Selected", self)
        act_export.triggered.connect(self._on_export_selected)
        file_menu.addAction(act_export)

        act_export_all = QAction("Export All", self)
        act_export_all.triggered.connect(self._on_export_all)
        file_menu.addAction(act_export_all)

        file_menu.addSeparator()

        act_quit = QAction("Quit", self)
        act_quit.setShortcut("Ctrl+Q")
        act_quit.triggered.connect(self._on_quit)
        file_menu.addAction(act_quit)

        # ── Proxy ──────────────────────────────────────────────────
        proxy_menu = menubar.addMenu("Proxy")

        act_start = QAction("Start Core", self)
        act_start.setShortcut("Ctrl+S")
        act_start.triggered.connect(self._on_start_core)
        proxy_menu.addAction(act_start)

        act_stop = QAction("Stop Core", self)
        act_stop.triggered.connect(self._on_stop_core)
        proxy_menu.addAction(act_stop)

        proxy_menu.addSeparator()

        act_sys_proxy_on = QAction("Enable System Proxy", self)
        act_sys_proxy_on.triggered.connect(lambda: self._on_toggle_sys_proxy(True))
        proxy_menu.addAction(act_sys_proxy_on)

        act_sys_proxy_off = QAction("Disable System Proxy", self)
        act_sys_proxy_off.triggered.connect(lambda: self._on_toggle_sys_proxy(False))
        proxy_menu.addAction(act_sys_proxy_off)

        # ── Subscription ───────────────────────────────────────────
        sub_menu = menubar.addMenu("Subscription")

        act_update_all = QAction("Update All Subscriptions", self)
        act_update_all.triggered.connect(lambda: self._on_update_sub(""))
        sub_menu.addAction(act_update_all)

        act_update_sel = QAction("Update Selected Subscription", self)
        act_update_sel.triggered.connect(self._on_update_selected_sub)
        sub_menu.addAction(act_update_sel)

        sub_menu.addSeparator()

        act_sub_settings = QAction("Subscription Settings…", self)
        act_sub_settings.triggered.connect(self._on_sub_settings)
        sub_menu.addAction(act_sub_settings)

        # ── Server ─────────────────────────────────────────────────
        server_menu = menubar.addMenu("Server")

        act_add = QAction("Add Server", self)
        act_add.setShortcut("Ins")
        act_add.triggered.connect(self._on_add_server)
        server_menu.addAction(act_add)

        act_edit = QAction("Edit Server", self)
        act_edit.setShortcut("Enter")
        act_edit.triggered.connect(self._on_edit_server)
        server_menu.addAction(act_edit)

        act_delete = QAction("Delete Server(s)", self)
        act_delete.setShortcut("Del")
        act_delete.triggered.connect(self._on_delete_servers)
        server_menu.addAction(act_delete)

        server_menu.addSeparator()

        act_ping_all = QAction("Ping All", self)
        act_ping_all.triggered.connect(self._on_ping_all)
        server_menu.addAction(act_ping_all)

        act_ping_sel = QAction("Ping Selected", self)
        act_ping_sel.triggered.connect(self._on_ping_selected)
        server_menu.addAction(act_ping_sel)

        server_menu.addSeparator()

        act_copy_uri = QAction("Copy URI", self)
        act_copy_uri.triggered.connect(self._on_copy_uri)
        server_menu.addAction(act_copy_uri)

        act_qr = QAction("Show QR Code", self)
        act_qr.triggered.connect(self._on_show_qr)
        server_menu.addAction(act_qr)

        # ── Settings ───────────────────────────────────────────────
        settings_menu = menubar.addMenu("Settings")

        act_options = QAction("Options…", self)
        act_options.triggered.connect(self._on_settings)
        settings_menu.addAction(act_options)

        # ── Help ───────────────────────────────────────────────────
        help_menu = menubar.addMenu("Help")

        act_about = QAction("About", self)
        act_about.triggered.connect(self._on_about)
        help_menu.addAction(act_about)

    # ── Toolbar ───────────────────────────────────────────────────────

    def _init_toolbar(self) -> None:
        toolbar = self.addToolBar("Main")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(16, 16))

        self._start_btn = QPushButton("▶ Start")
        self._start_btn.setFixedWidth(80)
        self._start_btn.clicked.connect(self._on_start_core)
        toolbar.addWidget(self._start_btn)

        self._stop_btn = QPushButton("⏹ Stop")
        self._stop_btn.setFixedWidth(80)
        self._stop_btn.clicked.connect(self._on_stop_core)
        toolbar.addWidget(self._stop_btn)

        toolbar.addSeparator()

        self._proxy_btn = QPushButton("Proxy: OFF")
        self._proxy_btn.setCheckable(True)
        self._proxy_btn.setFixedWidth(100)
        self._proxy_btn.clicked.connect(self._on_toggle_proxy_btn)
        toolbar.addWidget(self._proxy_btn)

        toolbar.addSeparator()

        # Subscription filter combo
        toolbar.addWidget(QLabel(" Sub: "))
        self._sub_combo = QComboBox()
        self._sub_combo.setMinimumWidth(160)
        self._sub_combo.currentIndexChanged.connect(self._on_sub_filter_changed)
        toolbar.addWidget(self._sub_combo)

        toolbar.addSeparator()

        self._update_sub_btn = QPushButton("⟳ Update Sub")
        self._update_sub_btn.clicked.connect(lambda: self._on_update_sub(""))
        toolbar.addWidget(self._update_sub_btn)

    # ── Central widget ────────────────────────────────────────────────

    def _init_central(self) -> None:
        splitter = QSplitter(Qt.Orientation.Vertical)
        self.setCentralWidget(splitter)

        # ── Server list table ────────────────────────────────────
        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels(
            ["#", "Remarks", "Address", "Port", "Protocol", "Latency", "Speed"]
        )
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_context_menu)
        self._table.doubleClicked.connect(self._on_table_double_click)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
        splitter.addWidget(self._table)

        # ── Log panel ─────────────────────────────────────────────
        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setFont(QFont("Monospace", 10))
        self._log_text.setMaximumHeight(150)
        splitter.addWidget(self._log_text)
        splitter.setSizes([450, 150])

    # ── Status bar ────────────────────────────────────────────────────

    def _init_statusbar(self) -> None:
        self._status_bar = self.statusBar()
        self._core_status_label = QLabel("Core: Stopped")
        self._proxy_status_label = QLabel("Proxy: OFF")
        self._port_label = QLabel()
        self._status_bar.addPermanentWidget(self._port_label)
        self._status_bar.addPermanentWidget(self._proxy_status_label)
        self._status_bar.addPermanentWidget(self._core_status_label)

    # ── System tray ───────────────────────────────────────────────────

    def _init_tray(self) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        self._tray = QSystemTrayIcon(self)

        # Build tray menu
        tray_menu = QMenu()
        act_show = QAction("Show", self)
        act_show.triggered.connect(self.show)
        tray_menu.addAction(act_show)

        tray_menu.addSeparator()

        act_start = QAction("Start Core", self)
        act_start.triggered.connect(self._on_start_core)
        tray_menu.addAction(act_start)

        act_stop = QAction("Stop Core", self)
        act_stop.triggered.connect(self._on_stop_core)
        tray_menu.addAction(act_stop)

        tray_menu.addSeparator()

        act_proxy_on = QAction("Enable Proxy", self)
        act_proxy_on.triggered.connect(lambda: self._on_toggle_sys_proxy(True))
        tray_menu.addAction(act_proxy_on)

        act_proxy_off = QAction("Disable Proxy", self)
        act_proxy_off.triggered.connect(lambda: self._on_toggle_sys_proxy(False))
        tray_menu.addAction(act_proxy_off)

        tray_menu.addSeparator()

        act_quit = QAction("Quit", self)
        act_quit.triggered.connect(self._on_quit)
        tray_menu.addAction(act_quit)

        self._tray.setContextMenu(tray_menu)
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()

    # ── Table management ──────────────────────────────────────────────

    def _refresh_profiles(self) -> None:
        """Reload server list from database."""
        self._table.setRowCount(0)
        profiles = self._mgr.get_profiles(self._current_sub_id or None)
        active_id = self._mgr.active_profile_id

        for row, p in enumerate(profiles):
            self._table.insertRow(row)
            self._table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            remarks_item = QTableWidgetItem(p.remarks or "")
            if p.indexId == active_id:
                font = remarks_item.font()
                font.setBold(True)
                remarks_item.setFont(font)
            self._table.setItem(row, 1, remarks_item)
            self._table.setItem(row, 2, QTableWidgetItem(p.address or ""))
            self._table.setItem(row, 3, QTableWidgetItem(str(p.port)))
            self._table.setItem(row, 4, QTableWidgetItem(CONFIG_TYPE_NAMES.get(p.configType, "?")))
            delay_str = f"{p.delay}ms" if p.delay >= 0 else "-"
            self._table.setItem(row, 5, QTableWidgetItem(delay_str))
            speed_str = Utils.format_speed(p.speed) if p.speed > 0 else "-"
            self._table.setItem(row, 6, QTableWidgetItem(speed_str))
            self._table.item(row, 0).setData(Qt.ItemDataRole.UserRole, p)

        port = self._mgr.config.inbound[0].get("localPort", 10808) if self._mgr.config.inbound else 10808
        self._port_label.setText(f"SOCKS: {port}")

    def _refresh_sub_combo(self) -> None:
        """Reload subscription filter combo box."""
        self._sub_combo.blockSignals(True)
        self._sub_combo.clear()
        self._sub_combo.addItem("All", "")
        if self._mgr.db:
            subs = self._mgr.db.get_all_subs()
            for s in subs:
                self._sub_combo.addItem(s.remarks or s.url or s.id, s.id)
        self._sub_combo.blockSignals(False)

    def _get_selected_profiles(self) -> list[ProfileItem]:
        rows = set(idx.row() for idx in self._table.selectedIndexes())
        result = []
        for row in sorted(rows):
            item = self._table.item(row, 0)
            if item:
                p = item.data(Qt.ItemDataRole.UserRole)
                if p:
                    result.append(p)
        return result

    def _get_first_selected(self) -> Optional[ProfileItem]:
        profiles = self._get_selected_profiles()
        return profiles[0] if profiles else None

    # ── Actions ───────────────────────────────────────────────────────

    def _on_start_core(self) -> None:
        p = self._get_first_selected()
        if p:
            self._mgr.active_profile_id = p.indexId
            self._mgr.save_config()

        if not self._mgr.active_profile_id:
            QMessageBox.information(self, "Info", "Please select a server first.")
            return

        ok = self._mgr.start_core()
        if ok:
            self._core_status_label.setText("Core: Running")
            self._status_bar.showMessage("Core started.", 3000)
            self._refresh_profiles()
        else:
            self._core_status_label.setText("Core: Error")
            QMessageBox.warning(self, "Error", "Failed to start core. Check logs.")

    def _on_stop_core(self) -> None:
        self._mgr.stop_core()
        self._core_status_label.setText("Core: Stopped")
        self._status_bar.showMessage("Core stopped.", 3000)

    def _on_toggle_proxy_btn(self, checked: bool) -> None:
        self._on_toggle_sys_proxy(checked)

    def _on_toggle_sys_proxy(self, enable: bool) -> None:
        ok = self._mgr.set_system_proxy(enable)
        if ok:
            label = "Proxy: ON" if enable else "Proxy: OFF"
            self._proxy_status_label.setText(label)
            self._proxy_btn.setText(label)
            self._proxy_btn.setChecked(enable)
            self._status_bar.showMessage(
                f"System proxy {'enabled' if enable else 'disabled'}.", 3000
            )
        else:
            QMessageBox.warning(
                self, "Error",
                f"Failed to {'enable' if enable else 'disable'} system proxy."
            )

    def _on_add_server(self) -> None:
        from .add_server_window import AddServerWindow
        dlg = AddServerWindow(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._mgr.add_profile(dlg.profile)
            self._refresh_profiles()

    def _on_edit_server(self) -> None:
        p = self._get_first_selected()
        if not p:
            QMessageBox.information(self, "Info", "Please select a server to edit.")
            return
        from .add_server_window import AddServerWindow
        dlg = AddServerWindow(self, p)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._mgr.db.upsert_profile(dlg.profile)
            self._refresh_profiles()

    def _on_delete_servers(self) -> None:
        profiles = self._get_selected_profiles()
        if not profiles:
            return
        reply = QMessageBox.question(
            self, "Confirm",
            f"Delete {len(profiles)} server(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            for p in profiles:
                self._mgr.delete_profile(p.indexId)
            self._refresh_profiles()

    def _on_table_double_click(self) -> None:
        """Double-click: set active and start core."""
        p = self._get_first_selected()
        if p:
            self._mgr.set_active_and_restart(p.indexId)
            self._core_status_label.setText("Core: Running")
            self._refresh_profiles()

    def _on_selection_changed(self) -> None:
        pass

    def _on_context_menu(self, pos) -> None:
        menu = QMenu(self)
        menu.addAction("Set as Active && Start", self._on_table_double_click)
        menu.addAction("Edit", self._on_edit_server)
        menu.addAction("Delete", self._on_delete_servers)
        menu.addSeparator()
        menu.addAction("Copy URI", self._on_copy_uri)
        menu.addAction("Show QR Code", self._on_show_qr)
        menu.addSeparator()
        menu.addAction("Ping", self._on_ping_selected)
        menu.exec(self._table.viewport().mapToGlobal(pos))

    # ── Subscription actions ──────────────────────────────────────────

    def _on_sub_filter_changed(self, idx: int) -> None:
        self._current_sub_id = self._sub_combo.currentData() or ""
        self._refresh_profiles()

    def _on_update_sub(self, sub_id: str) -> None:
        self._status_bar.showMessage("Updating subscriptions...")
        self._update_sub_btn.setEnabled(False)

        worker = UpdateSubWorker(self._mgr, sub_id=sub_id)
        worker.progress.connect(self._on_sub_progress)
        worker.finished.connect(self._on_sub_update_done)
        worker.start()
        # Keep reference alive
        self._sub_worker = worker

    def _on_update_selected_sub(self) -> None:
        sub_id = self._sub_combo.currentData() or ""
        self._on_update_sub(sub_id)

    def _on_sub_progress(self, ok: bool, msg: str) -> None:
        self._status_bar.showMessage(msg, 5000)

    def _on_sub_update_done(self) -> None:
        self._update_sub_btn.setEnabled(True)
        self._refresh_profiles()
        self._refresh_sub_combo()
        self._status_bar.showMessage("Subscription update complete.", 3000)

    def _on_sub_settings(self) -> None:
        from .subscription_window import SubscriptionWindow
        dlg = SubscriptionWindow(self, self._mgr.db)
        dlg.exec()
        self._refresh_sub_combo()
        self._refresh_profiles()

    # ── Import / Export ───────────────────────────────────────────────

    def _on_import_clipboard(self) -> None:
        text = QApplication.clipboard().text()
        if not text:
            QMessageBox.information(self, "Import", "Clipboard is empty.")
            return
        if not self._mgr.sub_handler:
            return
        count = self._mgr.sub_handler.import_from_clipboard(text)
        self._refresh_profiles()
        self._status_bar.showMessage(f"Imported {count} profile(s).", 3000)

    def _on_import_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open subscription file", "",
            "Text Files (*.txt);;All Files (*)"
        )
        if path and self._mgr.sub_handler:
            count = self._mgr.sub_handler.import_from_file(path)
            self._refresh_profiles()
            self._status_bar.showMessage(f"Imported {count} profile(s).", 3000)

    def _on_export_selected(self) -> None:
        profiles = self._get_selected_profiles()
        if not profiles:
            return
        lines = [V2rayFmt.resolve_profile(p) for p in profiles if V2rayFmt.resolve_profile(p)]
        text = "\n".join(lines)
        QApplication.clipboard().setText(text)
        self._status_bar.showMessage(f"Copied {len(lines)} URI(s) to clipboard.", 3000)

    def _on_export_all(self) -> None:
        if not self._mgr.sub_handler:
            return
        text = self._mgr.sub_handler.export_profiles()
        QApplication.clipboard().setText(text)
        count = len([l for l in text.splitlines() if l.strip()])
        self._status_bar.showMessage(f"Copied {count} URI(s) to clipboard.", 3000)

    def _on_copy_uri(self) -> None:
        p = self._get_first_selected()
        if not p:
            return
        uri = V2rayFmt.resolve_profile(p)
        if uri:
            QApplication.clipboard().setText(uri)
            self._status_bar.showMessage("URI copied to clipboard.", 2000)

    def _on_show_qr(self) -> None:
        p = self._get_first_selected()
        if not p:
            return
        uri = V2rayFmt.resolve_profile(p)
        if not uri:
            QMessageBox.information(self, "QR Code", "Cannot generate URI for this server.")
            return
        try:
            import qrcode
            from PyQt6.QtGui import QPixmap, QImage
            from PyQt6.QtWidgets import QLabel, QDialog, QVBoxLayout
            img = qrcode.make(uri)
            img_bytes = img.tobytes()
            qimg = QImage(img_bytes, img.size[0], img.size[1], QImage.Format.Format_Grayscale8)
            pixmap = QPixmap.fromImage(qimg)

            dlg = QDialog(self)
            dlg.setWindowTitle(f"QR Code - {p.remarks}")
            layout_dlg = QVBoxLayout(dlg)
            lbl = QLabel()
            lbl.setPixmap(pixmap.scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio))
            layout_dlg.addWidget(lbl)
            dlg.exec()
        except ImportError:
            QMessageBox.information(
                self, "QR Code",
                f"URI: {uri}\n\n(Install 'qrcode' package for QR display)"
            )

    # ── Speed test ────────────────────────────────────────────────────

    def _on_ping_all(self) -> None:
        profiles = self._mgr.get_profiles(self._current_sub_id or None)
        ids = [p.indexId for p in profiles]
        self._run_ping(ids)

    def _on_ping_selected(self) -> None:
        profiles = self._get_selected_profiles()
        ids = [p.indexId for p in profiles]
        if ids:
            self._run_ping(ids)

    def _run_ping(self, ids: list[str]) -> None:
        self._status_bar.showMessage("Pinging...")
        worker = PingWorker(self._mgr, ids)
        worker.result.connect(self._on_ping_result)
        worker.finished.connect(lambda: self._status_bar.showMessage("Ping done.", 3000))
        worker.start()
        self._ping_worker = worker

    def _on_ping_result(self, index_id: str, delay: int) -> None:
        """Update delay for a profile in the table."""
        p = self._mgr.db.get_profile(index_id)
        if p:
            p.delay = delay
            self._mgr.db.upsert_profile(p)
        for row in range(self._table.rowCount()):
            item = self._table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole):
                if item.data(Qt.ItemDataRole.UserRole).indexId == index_id:
                    delay_str = f"{delay}ms" if delay >= 0 else "Timeout"
                    delay_item = QTableWidgetItem(delay_str)
                    if delay >= 0:
                        delay_item.setForeground(
                            QColor("green") if delay < 500 else QColor("orange")
                        )
                    else:
                        delay_item.setForeground(QColor("red"))
                    self._table.setItem(row, 5, delay_item)
                    break

    # ── Settings ──────────────────────────────────────────────────────

    def _on_settings(self) -> None:
        from .settings_window import SettingsWindow
        dlg = SettingsWindow(self, self._mgr.config)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._mgr.save_config()
            self._status_bar.showMessage("Settings saved.", 3000)

    # ── Log ───────────────────────────────────────────────────────────

    def _append_log(self, message: str) -> None:
        self._log_text.append(message)
        # Limit log to max lines
        doc = self._log_text.document()
        if doc.blockCount() > self._log_max_lines:
            cursor = self._log_text.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.select(cursor.SelectionType.BlockUnderCursor)
            cursor.removeSelectedText()
        self._log_text.ensureCursorVisible()

    # ── Tray ──────────────────────────────────────────────────────────

    def _on_tray_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.raise_()
                self.activateWindow()

    # ── Misc ──────────────────────────────────────────────────────────

    def _on_about(self) -> None:
        QMessageBox.about(
            self,
            f"About v2rayN",
            f"<b>v2rayN {Global.APP_VERSION}</b><br><br>"
            f"A cross-platform proxy client.<br><br>"
            f"Python edition<br>"
            f"Original project: <a href='{Global.DOMAIN}'>{Global.DOMAIN}</a>",
        )

    def _on_quit(self) -> None:
        reply = QMessageBox.question(
            self, "Quit", "Are you sure you want to quit?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._do_quit()

    def _do_quit(self) -> None:
        cfg = self._mgr.config
        cfg.uiItem.mainWidth = self.width()
        cfg.uiItem.mainHeight = self.height()
        self._mgr.shutdown()
        if self._tray:
            self._tray.hide()
        QApplication.instance().quit()

    def closeEvent(self, event) -> None:
        """Minimize to tray instead of closing."""
        if self._tray and self._tray.isVisible():
            self.hide()
            event.ignore()
        else:
            event.accept()
