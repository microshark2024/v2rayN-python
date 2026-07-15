# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for v2rayN Python Edition.

Build locally with:
    pip install -r requirements-build.txt
    pyinstaller v2rayN.spec

The output directory is:  dist/v2rayN/
Place core binaries (xray.exe, sing-box.exe, …) in  dist/v2rayN/bin/
"""

block_cipher = None

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[
        # Bundle the bin/ directory (xray.exe, geoip.dat, geosite.dat, …).
        # Populate bin/ with all desired core binaries BEFORE running
        # PyInstaller; the directory must exist at build time.
        # After extraction, users can add or replace binaries in bin/.
        ("bin", "bin"),
    ],
    hiddenimports=[
        # All src sub-packages (PyInstaller may miss them because they are
        # imported via relative imports or loaded dynamically).
        "src.common.global_constants",
        "src.common.utils",
        "src.enums.enums",
        "src.handlers.config_handler",
        "src.handlers.database_handler",
        "src.handlers.subscription_handler",
        "src.handlers.fmt.base_fmt",
        "src.handlers.fmt.vmess_fmt",
        "src.handlers.fmt.vless_fmt",
        "src.handlers.fmt.shadowsocks_fmt",
        "src.handlers.fmt.trojan_fmt",
        "src.handlers.fmt.hysteria2_fmt",
        "src.handlers.fmt.tuic_fmt",
        "src.handlers.fmt.wireguard_fmt",
        "src.handlers.fmt.v2ray_fmt",
        "src.handlers.sys_proxy.sys_proxy_handler",
        "src.manager.app_manager",
        "src.manager.core_manager",
        "src.models.config",
        "src.models.profile_item",
        "src.models.sub_item",
        "src.services.core_config_service",
        "src.services.process_service",
        "src.services.speedtest_service",
        "src.ui.main_window",
        "src.ui.add_server_window",
        "src.ui.settings_window",
        "src.ui.subscription_window",
        # Third-party packages that may be missed by static analysis
        "PyQt6",
        "PyQt6.QtWidgets",
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "qrcode",
        "PIL",
        "yaml",
        "requests",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="v2rayN",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,   # No console window — GUI-only application
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="v2rayN",
)
