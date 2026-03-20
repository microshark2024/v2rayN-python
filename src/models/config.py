"""
Data models for v2rayN Python implementation.
Mirrors ServiceLib/Models/*.cs.
"""

from __future__ import annotations
import json
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Any


# ── Helper ────────────────────────────────────────────────────────────────────

def _asdict_no_none(obj) -> dict:
    """Convert dataclass to dict, omitting None values."""
    return {k: v for k, v in asdict(obj).items() if v is not None}


# ── Sub-configuration items ───────────────────────────────────────────────────

@dataclass
class CoreBasicItem:
    loglevel: str = "warning"
    muxEnabled: bool = False
    muxConcurrency: int = 8
    muxXudpConcurrency: int = 16
    muxXudpProxyUDP443: str = ""


@dataclass
class TunModeItem:
    enableTun: bool = False
    strictRoute: bool = True
    stack: str = "gvisor"
    mtu: int = 9000
    enableExInbound: bool = False
    enableIPv6Address: bool = True
    metricIPv6: int = 200


@dataclass
class KcpItem:
    mtu: int = 1350
    tti: int = 50
    uplinkCapacity: int = 12
    downlinkCapacity: int = 100
    congestion: bool = False
    readBufferSize: int = 2
    writeBufferSize: int = 2


@dataclass
class GrpcItem:
    idle_timeout: int = 60
    health_check_timeout: int = 20
    permit_without_stream: bool = False
    initial_windows_size: int = 0


@dataclass
class RoutingBasicItem:
    domainStrategy: str = "IPIfNonMatch"
    domainMatcher: str = "hybrid"


@dataclass
class GUIItem:
    autoRun: int = 0
    enableStatistics: bool = True
    keepOlderDedupl: bool = False
    autoUpdateSubInterval: int = 0
    checkPreRelease: bool = False
    mainGirdColumns1: str = ""
    mainGirdColumns2: str = ""
    msgTimeout: int = 3000


@dataclass
class UIItem:
    mainWidth: int = 1366
    mainHeight: int = 768
    colorModeDark: bool = True
    followSystemTheme: bool = True
    currentFontSize: float = 14.0
    currentLanguage: str = ""
    currentProxyExceptions: str = "localhost;127.*;10.*;172.16.*;192.168.*;*.local"
    enableAutoAdjustMainLvColWidth: bool = True
    currentTheme: str = ""


@dataclass
class MsgUIItem:
    mainMsgWidth: int = 800
    mainMsgHeight: int = 600


@dataclass
class ConstItem:
    defIEProxyExceptions: str = "localhost"


@dataclass
class SpeedTestItem:
    speedTestUrl: str = ""
    speedPingTestUrl: str = "https://www.google.com/generate_204"
    speedPingTestUrl2: str = ""
    downloadSpeed: float = 0.0


@dataclass
class Mux4RayItem:
    enabled: bool = False
    protocol: str = "h2mux"
    maxConnections: int = 4
    minStreams: int = 4
    maxStreams: int = 0
    padding: bool = False
    onlyhttp: bool = False
    onlyQuic: bool = False
    concurrency: int = -1


@dataclass
class Mux4SboxItem:
    enabled: bool = False
    protocol: str = "h2mux"
    maxConnections: int = 4
    minStreams: int = 4
    maxStreams: int = 0
    padding: bool = False
    onlyhttp: bool = False
    brutal_mbps: int = 0


@dataclass
class HysteriaItem:
    up_mbps: int = 100
    down_mbps: int = 100
    obfs: str = ""
    obfsParam: str = ""
    auth: str = ""
    alpn: str = ""
    server_name: str = ""
    insecure: bool = False
    hop_interval: int = 0


@dataclass
class ClashUIItem:
    enableMixinContent: bool = False


@dataclass
class SystemProxyItem:
    proxyExceptions: str = "localhost;127.*;10.*;172.16.*;192.168.*;*.local"
    systemProxyAdvancedProtocol: str = ""
    pacUrl: str = ""
    port: int = 0


@dataclass
class WebDavItem:
    url: str = ""
    userName: str = ""
    password: str = ""
    DirPath: str = ""
    enabled: bool = False


@dataclass
class CheckUpdateItem:
    checkPreReleaseUpdate: bool = False


@dataclass
class Fragment4RayItem:
    enabled: bool = False
    length: str = ""
    interval: str = ""
    packets: str = ""


@dataclass
class InItem:
    protocol: str = "socks"
    localPort: int = 10808
    udpEnabled: bool = True
    sniffingEnabled: bool = True
    routeOnly: bool = False


@dataclass
class KeyEventItem:
    keyCode: int = 0
    modifierKeys: int = 0
    action: int = 0


@dataclass
class CoreTypeItem:
    configType: int = 0
    coreType: Optional[int] = None


@dataclass
class SimpleDNSItem:
    enabled: bool = False
    localDns: str = "223.5.5.5"
    remoteDns: str = "https://1.1.1.1/dns-query"
    domainStrategy4Freedom: str = ""
    useSystemHosts: bool = False


# ── Main Config ───────────────────────────────────────────────────────────────

@dataclass
class Config:
    """
    Main application configuration.
    Mirrors ServiceLib/Models/Config.cs.
    """

    indexId: str = ""
    subIndexId: str = ""

    coreBasicItem: CoreBasicItem = field(default_factory=CoreBasicItem)
    tunModeItem: TunModeItem = field(default_factory=TunModeItem)
    kcpItem: KcpItem = field(default_factory=KcpItem)
    grpcItem: GrpcItem = field(default_factory=GrpcItem)
    routingBasicItem: RoutingBasicItem = field(default_factory=RoutingBasicItem)
    guiItem: GUIItem = field(default_factory=GUIItem)
    msgUIItem: MsgUIItem = field(default_factory=MsgUIItem)
    uiItem: UIItem = field(default_factory=UIItem)
    constItem: ConstItem = field(default_factory=ConstItem)
    speedTestItem: SpeedTestItem = field(default_factory=SpeedTestItem)
    mux4RayItem: Mux4RayItem = field(default_factory=Mux4RayItem)
    mux4SboxItem: Mux4SboxItem = field(default_factory=Mux4SboxItem)
    hysteriaItem: HysteriaItem = field(default_factory=HysteriaItem)
    clashUIItem: ClashUIItem = field(default_factory=ClashUIItem)
    systemProxyItem: SystemProxyItem = field(default_factory=SystemProxyItem)
    webDavItem: WebDavItem = field(default_factory=WebDavItem)
    checkUpdateItem: CheckUpdateItem = field(default_factory=CheckUpdateItem)
    fragment4RayItem: Optional[Fragment4RayItem] = None
    simpleDNSItem: SimpleDNSItem = field(default_factory=SimpleDNSItem)

    inbound: List[dict] = field(default_factory=list)
    globalHotkeys: List[dict] = field(default_factory=list)
    coreTypeItem: List[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return json.loads(json.dumps(asdict(self), default=str))

    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        """Create Config from dictionary."""
        c = cls()

        def _apply(obj, d: dict):
            for k, v in d.items():
                if hasattr(obj, k):
                    attr = getattr(obj, k)
                    if isinstance(attr, list):
                        setattr(obj, k, v)
                    elif hasattr(attr, "__dataclass_fields__") and isinstance(v, dict):
                        _apply(attr, v)
                    else:
                        setattr(obj, k, v)

        _apply(c, data)
        return c
