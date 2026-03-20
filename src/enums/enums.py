"""
Enumerations for v2rayN Python implementation.
Mirrors the enums from the original C# ServiceLib/Enums/*.cs files.
"""

from enum import IntEnum, Enum


class ECoreType(IntEnum):
    """Supported proxy core types."""
    v2fly = 1
    Xray = 2
    v2fly_v5 = 4
    mihomo = 13
    hysteria = 21
    naiveproxy = 22
    tuic = 23
    sing_box = 24
    juicity = 25
    hysteria2 = 26
    brook = 27
    overtls = 28
    shadowquic = 29
    mieru = 30


class EConfigType(IntEnum):
    """Supported proxy configuration types."""
    VMess = 1
    Shadowsocks = 2
    Socks = 3
    VLESS = 7
    Trojan = 8
    Hysteria2 = 9
    TUIC = 10
    WireGuard = 11
    Hysteria = 12
    ANYTLS = 13
    Custom = 99


class ERuleMode(IntEnum):
    """Routing rule modes."""
    Global = 0
    Bypass = 1
    Rule = 2


class ESysProxyType(IntEnum):
    """System proxy setting types."""
    ForcedClear = 0
    ForcedChange = 1
    Unchanged = 2
    Pac = 3


class EInboundProtocol(IntEnum):
    """Inbound protocol types."""
    socks = 0
    http = 1
    socks2 = 2
    http2 = 3
    socks3 = 4
    http3 = 5


class EProxySetting(IntEnum):
    """Proxy setting types for system proxy."""
    NoModify = 0
    SetProxy = 1
    ClearProxy = 2
    Pac = 3


class ETheme(IntEnum):
    """UI theme options."""
    Dark = 0
    Light = 1
    Follow = 2


class EAutoRun(IntEnum):
    """Auto-run on startup options."""
    Off = 0
    On = 1
    OnAsAdmin = 2


class EGlobalHotkey(IntEnum):
    """Global hotkey actions."""
    ShowForm = 0
    SystemProxyClear = 1
    SystemProxySet = 2
    SystemProxyUnchanged = 3
    SystemProxyPac = 4


class ELogLevel(Enum):
    """Log level options."""
    debug = "debug"
    info = "info"
    warning = "warning"
    error = "error"
    none = "none"


class EPresetType(IntEnum):
    """Preset configuration types."""
    Default = 0
    Custom = 1


class EKcpHeaderType(IntEnum):
    """KCP header types."""
    none = 0
    srtp = 1
    utp = 2
    wechat_video = 3
    dtls = 4
    wireguard = 5


class EMsgCommand(IntEnum):
    """Message commands for inter-component communication."""
    None_ = 0
    AppStart = 1
    AppExit = 2
    RefreshProfiles = 3
    RefreshSubItems = 4
    RefreshRoutings = 5
    RefreshDNS = 6
    TestSpeedAll = 7
    TestSpeedSelected = 8
    Ping = 9
    UpdateConfig = 10
    ReloadCore = 11
    SwitchSystemProxy = 12
    ToggleRunState = 13


class ESpeedActionType(IntEnum):
    """Speed test action types."""
    Ping = 0
    RealPing = 1
    Speedtest = 2


class ENodeSort(IntEnum):
    """Node sorting options."""
    Default = 0
    DelayAsc = 1
    DelayDesc = 2
    SpeedAsc = 3
    SpeedDesc = 4
    Alphanumeric = 5
