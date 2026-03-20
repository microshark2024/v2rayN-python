"""
v2rayN - Python Edition
Entry point.

Usage:
    python main.py
"""

import sys
import os
import logging

# Ensure src/ is on the path
sys.path.insert(0, os.path.dirname(__file__))

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt

from src.manager.app_manager import AppManager


def main() -> None:
    # High DPI support
    app = QApplication(sys.argv)
    app.setApplicationName("v2rayN")
    app.setApplicationVersion("7.19.4")
    app.setOrganizationName("v2rayN")

    # Initialize application manager
    mgr = AppManager.instance()
    if not mgr.init():
        QMessageBox.critical(None, "Error", "Failed to initialize application.")
        sys.exit(1)

    # Import and create main window
    from src.ui.main_window import MainWindow
    win = MainWindow(mgr)
    win.show()

    exit_code = app.exec()

    # Ensure clean shutdown
    mgr.shutdown()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
