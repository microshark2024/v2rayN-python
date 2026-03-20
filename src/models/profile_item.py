"""
ProfileItem model - represents a single proxy server profile.
Mirrors ServiceLib/Models/ProfileItem.cs.
"""

from __future__ import annotations
import json
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Any


@dataclass
class ProtocolExtraItem:
    """Extra protocol-specific parameters."""
    flow: Optional[str] = None
    encryption: Optional[str] = None
    extra: Optional[str] = None


@dataclass
class ProfileItem:
    """
    Represents a single proxy server profile.
    Mirrors ServiceLib/Models/ProfileItem.cs.
    """

    # Primary key
    indexId: str = ""

    # Classification
    configType: int = 1           # EConfigType value
    coreType: Optional[int] = None  # ECoreType value
    configVersion: int = 2
    subid: str = ""
    isSub: bool = True

    # Display
    remarks: str = ""
    sortNumber: int = 0

    # Connection
    address: str = ""
    port: int = 0
    password: str = ""
    username: str = ""
    id: str = ""
    alterId: int = 0
    security: str = ""
    method: str = ""

    # Transport
    network: str = "tcp"
    headerType: str = ""
    requestHost: str = ""
    path: str = ""
    streamSecurity: str = ""     # none / tls / reality
    allowInsecure: str = ""
    sni: str = ""
    alpn: str = ""

    # Advanced
    fingerprint: str = ""
    publicKey: str = ""
    shortId: str = ""
    spiderX: str = ""
    echConfigList: str = ""
    finalmask: str = ""

    # Proxy chaining
    preSocksPort: Optional[int] = None
    muxEnabled: Optional[bool] = None
    protoExtra: str = ""

    # UI settings
    displayLog: bool = True
    coreBasicLoglevel: str = ""

    # Speed / test results
    delay: int = -1
    speed: float = 0.0
    speedError: str = ""
    testError: str = ""

    # Timestamps
    addTime: int = 0
    lastModifyTime: int = 0

    def get_network(self) -> str:
        """Get network type, falling back to 'tcp'."""
        if not self.network:
            return "tcp"
        return self.network

    def get_alpn_list(self) -> Optional[List[str]]:
        """Parse ALPN string into list."""
        if not self.alpn:
            return None
        return [a.strip() for a in self.alpn.split(",") if a.strip()]

    def is_custom(self) -> bool:
        """Return True if this is a custom JSON config."""
        return self.configType == 99  # EConfigType.Custom

    def is_valid(self) -> bool:
        """Basic validation."""
        if not self.address:
            return False
        if self.port <= 0 or self.port > 65535:
            return False
        if self.is_custom():
            return True
        return True

    def get_summary(self) -> str:
        """Return human-readable summary."""
        name = self.remarks or self.address
        return f"{name}:{self.port}"

    def get_protocol_extra(self) -> ProtocolExtraItem:
        """Deserialize protoExtra JSON."""
        if self.protoExtra:
            try:
                d = json.loads(self.protoExtra)
                return ProtocolExtraItem(**{k: v for k, v in d.items()
                                            if k in ProtocolExtraItem.__dataclass_fields__})
            except (json.JSONDecodeError, TypeError):
                pass
        return ProtocolExtraItem()

    def set_protocol_extra(self, extra: ProtocolExtraItem) -> None:
        """Serialize ProtocolExtraItem to protoExtra."""
        d = {k: v for k, v in asdict(extra).items() if v is not None}
        self.protoExtra = json.dumps(d) if d else ""

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_dict(cls, data: dict) -> "ProfileItem":
        """Create from dictionary."""
        valid_keys = set(cls.__dataclass_fields__.keys())
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


@dataclass
class ProfileItemModel(ProfileItem):
    """Extended ProfileItem with display-only fields."""
    groupName: str = ""
    configTypeName: str = ""
    coreTypeName: str = ""


@dataclass
class ServerSpeedItem:
    """Speed test result for a server."""
    indexId: str = ""
    delay: int = -1
    speed: float = 0.0
    speedError: str = ""


@dataclass
class ServerTestItem:
    """Item for speed test execution."""
    profileItem: Optional[ProfileItem] = None
    delay: int = -1
    speed: float = 0.0
    speedError: str = ""
    testError: str = ""
    port: int = 0
    success: bool = False
    coreType: Optional[int] = None
