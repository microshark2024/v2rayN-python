"""
Global constants for v2rayN Python implementation.
Mirrors ServiceLib/Common/Global.cs.
"""

import os
import platform


class Global:
    """Global application constants."""

    # Application info
    APP_NAME = "ohoo"
    APP_VERSION = "0.0.1"
    DOMAIN = "https://github.com/2dust/v2rayN"

    # Config file names
    CONFIG_FILE_NAME = "guiNConfig.json"
    GUI_CONFIG_FILE_NAME = "guiNConfig.json"
    CORE_CONFIG_FILE_NAME = "coreNConfig.json"
    SPEEDTEST_CONFIG_FILE_NAME = "speedtestNConfig.json"

    # Directory names
    BIN_DIR = "bin"
    LOGS_DIR = "logs"
    ROUTING_DIR = "routing"
    GUICONFIGS_DIR = "guiConfigs"

    # Backup
    BACKUP_DIR = "backup"

    # File names
    CORE_LOG_FILE = "coreNLog.txt"
    GUI_LOG_FILE = "guiNLog.txt"

    # Default ports
    DEFAULT_SOCKS_PORT = 10808
    DEFAULT_HTTP_PORT = 10809
    DEFAULT_API_PORT = 10810

    # API settings
    MIHOMO_API_PORT = 9090
    STATS_API_PORT = 10085

    # Network types
    NETWORK_TCP = "tcp"
    NETWORK_KCP = "kcp"
    NETWORK_WS = "ws"
    NETWORK_H2 = "h2"
    NETWORK_GRPC = "grpc"
    NETWORK_QUIC = "quic"
    NETWORK_HTTPUPGRADE = "httpupgrade"
    NETWORK_XHTTP = "xhttp"
    NETWORK_MEEK = "meek"
    NETWORK_WEBRTC = "webrtc"

    NETWORKS = [
        NETWORK_TCP, NETWORK_KCP, NETWORK_WS, NETWORK_H2,
        NETWORK_GRPC, NETWORK_QUIC, NETWORK_HTTPUPGRADE,
        NETWORK_XHTTP, NETWORK_MEEK, NETWORK_WEBRTC
    ]

    # Security types
    SECURITY_NONE = "none"
    SECURITY_TLS = "tls"
    SECURITY_REALITY = "reality"

    SECURITIES = [SECURITY_NONE, SECURITY_TLS, SECURITY_REALITY]

    # Header types
    HEADER_TYPES = ["none", "srtp", "utp", "wechat-video", "dtls", "wireguard"]

    # ALPN options
    ALPN_OPTIONS = ["", "h2", "http/1.1", "h2,http/1.1"]

    # Fingerprint options
    FINGERPRINTS = [
        "", "chrome", "firefox", "safari", "ios", "android",
        "edge", "360", "qq", "random", "randomized"
    ]

    # Default user agents
    DEFAULT_USER_AGENTS = [
        "",
        "v2rayN",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "ClashMetaForAndroid/2.10.1",
    ]

    # Speed test URLs
    DEFAULT_SPEEDTEST_URLS = [
        "https://dl.google.com/dl/android/studio/install/3.4.1.0/android-studio-ide-183.5522156-windows.exe"
    ]

    # Ping URLs
    DEFAULT_PING_URLS = [
        "https://www.google.com/generate_204",
        "https://www.gstatic.com/generate_204",
    ]

    # DNS
    DEFAULT_DNS_REMOTE = "https://1.1.1.1/dns-query"
    DEFAULT_DNS_LOCAL = "223.5.5.5"

    # GUI defaults
    DEFAULT_THEME = "Follow"
    DEFAULT_FONT_SIZE = 14

    # Core names mapping
    CORE_NAMES = {
        "v2fly": "v2ray",
        "Xray": "xray",
        "v2fly_v5": "v2ray",
        "mihomo": "mihomo",
        "hysteria": "hysteria",
        "naiveproxy": "naive",
        "tuic": "tuic",
        "sing_box": "sing-box",
        "juicity": "juicity",
        "hysteria2": "hysteria",
        "brook": "brook",
        "overtls": "overtls",
        "shadowquic": "shadowquic",
        "mieru": "mieru",
    }

    # Core executable names by platform
    @staticmethod
    def get_core_exe(core_name: str) -> str:
        """Get core executable name based on platform."""
        if platform.system() == "Windows":
            return f"{core_name}.exe"
        return core_name

    # Config types that support GUI editing
    GUI_EDITABLE_CONFIG_TYPES = [1, 2, 3, 7, 8, 9, 10, 11, 12, 13]

    # Subscription conversion URL
    SUB_CONVERT_URL = "https://sub.xeton.dev/sub?target=mixed&url={0}&insert=false"

    # GitHub release API
    GITHUB_API = "https://api.github.com/repos/{owner}/{repo}/releases/latest"

    # Base URI schemes
    URI_SCHEMES = {
        "vmess": "vmess://",
        "vless": "vless://",
        "ss": "ss://",
        "trojan": "trojan://",
        "hysteria2": "hysteria2://",
        "hy2": "hy2://",
        "tuic": "tuic://",
        "wireguard": "wireguard://",
        "hysteria": "hysteria://",
        "anytls": "anytls://",
    }

    # Max log lines to display
    MAX_LOG_LINES = 500

    # Auto-update interval options (hours)
    AUTO_UPDATE_INTERVALS = [0, 1, 2, 4, 6, 8, 12, 24]
