# v2rayN - Python Edition

A complete Python rewrite of [v2rayN](https://github.com/2dust/v2rayN) — a cross-platform proxy client GUI application.

## Features

- ✅ **Multi-protocol support**: VMess, VLESS, Shadowsocks, Trojan, Hysteria2, TUIC, WireGuard, Socks, ANYTLS
- ✅ **Core support**: v2ray, Xray, sing-box, mihomo (Clash), hysteria2, and more
- ✅ **Subscription management**: Import from URL, auto-update, keyword filtering
- ✅ **System proxy control**: Windows (registry), Linux (gsettings), macOS (networksetup)
- ✅ **Core config generation**: Automatic v2ray/xray/sing-box JSON config generation
- ✅ **Speed testing**: TCP latency ping and download speed test
- ✅ **Cross-platform GUI**: PyQt6 (Windows / Linux / macOS)
- ✅ **System tray**: Minimize to tray, quick proxy toggle
- ✅ **Import/Export**: Clipboard and file-based URI import/export
- ✅ **QR Code display**: Display proxy URI as QR code
- ✅ **SQLite storage**: Persistent server, subscription, routing, and DNS settings
- ✅ **Configuration management**: JSON-based config with full v2rayN compatibility

## Project Structure

```
v2rayN-python/
├── main.py                         # Entry point
├── requirements.txt                # Python dependencies
├── src/
│   ├── common/
│   │   ├── global_constants.py     # Global constants (ports, protocols, etc.)
│   │   └── utils.py                # Common utility functions
│   ├── enums/
│   │   └── enums.py                # All enumerations (ECoreType, EConfigType, etc.)
│   ├── models/
│   │   ├── config.py               # Main Config model + sub-config items
│   │   ├── profile_item.py         # ProfileItem (proxy server profile)
│   │   └── sub_item.py             # SubItem (subscription), RoutingItem, DNSItem
│   ├── handlers/
│   │   ├── config_handler.py       # Load/save configuration
│   │   ├── database_handler.py     # SQLite database operations
│   │   ├── subscription_handler.py # Fetch and parse subscriptions
│   │   ├── fmt/
│   │   │   ├── base_fmt.py         # Base URI parser
│   │   │   ├── vmess_fmt.py        # VMess URI parser/generator
│   │   │   ├── vless_fmt.py        # VLESS URI parser/generator
│   │   │   ├── shadowsocks_fmt.py  # Shadowsocks URI parser/generator
│   │   │   ├── trojan_fmt.py       # Trojan URI parser/generator
│   │   │   ├── hysteria2_fmt.py    # Hysteria2 URI parser/generator
│   │   │   ├── tuic_fmt.py         # TUIC URI parser/generator
│   │   │   ├── wireguard_fmt.py    # WireGuard URI parser/generator
│   │   │   └── v2ray_fmt.py        # Universal URI dispatcher
│   │   └── sys_proxy/
│   │       └── sys_proxy_handler.py # System proxy (Windows/Linux/macOS)
│   ├── services/
│   │   ├── process_service.py      # Manages a proxy core subprocess
│   │   ├── speedtest_service.py    # Latency and download speed testing
│   │   └── core_config_service.py  # Generate v2ray/xray/sing-box config files
│   ├── manager/
│   │   ├── app_manager.py          # Application-wide singleton manager
│   │   └── core_manager.py         # Start/stop proxy core processes
│   └── ui/
│       ├── main_window.py          # Main application window
│       ├── add_server_window.py    # Add/Edit server dialog
│       ├── settings_window.py      # Settings/Options dialog
│       └── subscription_window.py  # Subscription management dialog
└── tests/
    ├── test_utils.py               # Utils tests (30 tests)
    ├── test_models.py              # Model tests (23 tests)
    ├── test_config_handler.py      # Config handler tests (10 tests)
    ├── test_database_handler.py    # Database tests (16 tests)
    └── test_fmt_handlers.py        # Protocol format tests (27 tests)
```

## Requirements

- Python 3.10+
- PyQt6 (GUI)
- requests (HTTP/subscription downloads)
- qrcode + Pillow (QR code display)
- pyyaml (YAML config parsing)

## Installation

```bash
cd v2rayN-python
pip install -r requirements.txt
```

## Running

```bash
python main.py
```

## Running Tests

```bash
cd v2rayN-python
pip install pytest
python -m pytest tests/ -v
```

## Building a Windows EXE

### Prerequisites

```bash
pip install -r requirements.txt
pip install -r requirements-build.txt   # installs PyInstaller
```

### Build

```bash
pyinstaller v2rayN.spec
```

The packaged application is produced in `dist/v2rayN/`.  Copy your core
binaries into `dist/v2rayN/bin/` before distributing.

### Automated CI build

A GitHub Actions workflow (`.github/workflows/build.yml`) automatically builds
the Windows EXE whenever a version tag (e.g. `v1.0.0`) is pushed, and uploads
it as a release asset.  You can also trigger a one-off build via
**Actions → Build Windows EXE → Run workflow**.

## Core Binaries

Place core executable files in the `bin/` directory next to `main.py` (or next
to `v2rayN.exe` when using the packaged release):

| Core     | Executable name     | Protocols                          |
|----------|--------------------|------------------------------------|
| Xray     | `xray` / `xray.exe` | VMess, VLESS, Trojan, Shadowsocks  |
| v2ray    | `v2ray` / `v2ray.exe` | VMess, VLESS, Trojan, Shadowsocks |
| sing-box | `sing-box` / `sing-box.exe` | Hysteria2, TUIC, WireGuard, + |
| mihomo   | `mihomo` / `mihomo.exe` | Clash-based protocols           |
| hysteria | `hysteria` / `hysteria.exe` | Hysteria / Hysteria2          |

## Architecture

This Python edition mirrors the architecture of the original C# codebase:

| Python module | C# equivalent |
|---|---|
| `AppManager` | `AppManager.cs` |
| `CoreManager` | `CoreManager.cs` |
| `ConfigHandler` | `ConfigHandler.cs` |
| `DatabaseHandler` | SQLite via `sqlite-net-pcl` |
| `SubscriptionHandler` | `SubscriptionHandler.cs` |
| `ProcessService` | `ProcessService.cs` |
| `CoreConfigService` | `CoreConfigV2rayService.cs` + `CoreConfigSingboxService.cs` |
| `SysProxyHandler` | `SysProxyHandler.cs` + platform impls |
| `V2rayFmt` + format classes | `V2rayFmt.cs` + protocol fmts |
| `MainWindow` | `MainWindow.xaml.cs` |

## License

GPLv3 — same as the original v2rayN project.
