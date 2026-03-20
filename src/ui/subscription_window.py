"""
Subscription management window.
"""

from __future__ import annotations
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLineEdit, QCheckBox, QSpinBox,
    QDialogButtonBox, QMessageBox, QLabel, QWidget, QGroupBox, QHeaderView,
)
from PyQt6.QtCore import Qt

from ..models.sub_item import SubItem
from ..common.utils import Utils


class SubEditDialog(QDialog):
    """Add / edit a single subscription."""

    def __init__(self, parent=None, sub: Optional[SubItem] = None):
        super().__init__(parent)
        self._sub = sub or SubItem()
        self._is_new = sub is None
        self.setWindowTitle("Add Subscription" if self._is_new else "Edit Subscription")
        self.setMinimumWidth(500)
        self.setModal(True)
        self._init_ui()
        self._load(self._sub)

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._remarks_edit = QLineEdit()
        form.addRow("Remarks:", self._remarks_edit)

        self._url_edit = QLineEdit()
        self._url_edit.setPlaceholderText("https://...")
        form.addRow("URL:", self._url_edit)

        self._more_url_edit = QLineEdit()
        self._more_url_edit.setPlaceholderText("Additional URLs separated by |")
        form.addRow("More URLs:", self._more_url_edit)

        self._user_agent_edit = QLineEdit()
        form.addRow("User-Agent:", self._user_agent_edit)

        self._filter_edit = QLineEdit()
        self._filter_edit.setPlaceholderText("Keyword filters separated by |")
        form.addRow("Filter:", self._filter_edit)

        self._enabled_check = QCheckBox("Enabled")
        form.addRow("", self._enabled_check)

        self._auto_update_spin = QSpinBox()
        self._auto_update_spin.setRange(0, 72)
        self._auto_update_spin.setSuffix(" hours (0=disabled)")
        form.addRow("Auto Update:", self._auto_update_spin)

        self._memo_edit = QLineEdit()
        form.addRow("Memo:", self._memo_edit)

        layout.addLayout(form)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self._on_save)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _load(self, sub: SubItem) -> None:
        self._remarks_edit.setText(sub.remarks or "")
        self._url_edit.setText(sub.url or "")
        self._more_url_edit.setText(sub.moreUrl or "")
        self._user_agent_edit.setText(sub.userAgent or "")
        self._filter_edit.setText(sub.filter or "")
        self._enabled_check.setChecked(sub.enabled)
        self._auto_update_spin.setValue(sub.autoUpdateInterval or 0)
        self._memo_edit.setText(sub.memo or "")

    def _on_save(self) -> None:
        url = self._url_edit.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "URL cannot be empty.")
            return
        s = self._sub
        s.remarks = self._remarks_edit.text().strip()
        s.url = url
        s.moreUrl = self._more_url_edit.text().strip()
        s.userAgent = self._user_agent_edit.text().strip()
        s.filter = self._filter_edit.text().strip() or None
        s.enabled = self._enabled_check.isChecked()
        s.autoUpdateInterval = self._auto_update_spin.value()
        s.memo = self._memo_edit.text().strip() or None
        if not s.id:
            s.id = Utils.generate_id()
        self.accept()

    @property
    def sub(self) -> SubItem:
        return self._sub


class SubscriptionWindow(QDialog):
    """
    Subscription management window.
    Mirrors SubSettingWindow in the original C# code.
    """

    def __init__(self, parent=None, db_handler=None):
        super().__init__(parent)
        self._db = db_handler
        self.setWindowTitle("Subscription Settings")
        self.setMinimumSize(700, 400)
        self._init_ui()
        self._load_subs()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Toolbar
        toolbar = QHBoxLayout()
        self._add_btn = QPushButton("Add")
        self._edit_btn = QPushButton("Edit")
        self._delete_btn = QPushButton("Delete")
        self._add_btn.clicked.connect(self._on_add)
        self._edit_btn.clicked.connect(self._on_edit)
        self._delete_btn.clicked.connect(self._on_delete)
        toolbar.addWidget(self._add_btn)
        toolbar.addWidget(self._edit_btn)
        toolbar.addWidget(self._delete_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(
            ["Remarks", "URL", "Enabled", "Auto Update", "Last Updated"]
        )
        self._table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.doubleClicked.connect(self._on_edit)
        layout.addWidget(self._table)

        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btn_box.rejected.connect(self.accept)
        layout.addWidget(btn_box)

    def _load_subs(self) -> None:
        self._table.setRowCount(0)
        if not self._db:
            return
        subs = self._db.get_all_subs()
        for row, sub in enumerate(subs):
            self._table.insertRow(row)
            self._table.setItem(row, 0, QTableWidgetItem(sub.remarks or ""))
            self._table.setItem(row, 1, QTableWidgetItem(sub.url or ""))
            self._table.setItem(row, 2, QTableWidgetItem("Yes" if sub.enabled else "No"))
            interval = sub.autoUpdateInterval or 0
            self._table.setItem(row, 3, QTableWidgetItem(f"{interval}h" if interval else "Off"))
            import time
            update_time = sub.updateTime or 0
            ts_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(update_time)) if update_time else "-"
            self._table.setItem(row, 4, QTableWidgetItem(ts_str))
            self._table.item(row, 0).setData(Qt.ItemDataRole.UserRole, sub)

    def _get_selected_sub(self) -> Optional[SubItem]:
        row = self._table.currentRow()
        if row < 0:
            return None
        item = self._table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _on_add(self) -> None:
        dlg = SubEditDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted and self._db:
            self._db.upsert_sub(dlg.sub)
            self._load_subs()

    def _on_edit(self) -> None:
        sub = self._get_selected_sub()
        if not sub:
            QMessageBox.information(self, "Info", "Please select a subscription first.")
            return
        dlg = SubEditDialog(self, sub)
        if dlg.exec() == QDialog.DialogCode.Accepted and self._db:
            self._db.upsert_sub(dlg.sub)
            self._load_subs()

    def _on_delete(self) -> None:
        sub = self._get_selected_sub()
        if not sub:
            return
        reply = QMessageBox.question(
            self, "Confirm", f"Delete subscription '{sub.remarks or sub.url}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes and self._db:
            self._db.delete_sub(sub.id)
            self._load_subs()
