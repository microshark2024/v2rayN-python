"""
SubItem model - represents a subscription source.
Mirrors ServiceLib/Models/SubItem.cs.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class SubItem:
    """
    Represents a proxy subscription source.
    Mirrors ServiceLib/Models/SubItem.cs.
    """

    id: str = ""
    remarks: str = ""
    url: str = ""
    moreUrl: str = ""
    enabled: bool = True
    userAgent: str = ""
    sort: int = 0

    # Filtering and conversion
    filter: Optional[str] = None
    convertTarget: Optional[str] = None

    # Auto-update settings
    autoUpdateInterval: int = 0
    updateTime: int = 0

    # Chaining
    prevProfile: Optional[str] = None
    nextProfile: Optional[str] = None
    preSocksPort: Optional[int] = None

    memo: Optional[str] = None

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items()}

    @classmethod
    def from_dict(cls, data: dict) -> "SubItem":
        valid_keys = set(cls.__dataclass_fields__.keys())
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


@dataclass
class RoutingItem:
    """Routing rule item."""
    id: str = ""
    remarks: str = ""
    url: str = ""
    customIcon: str = ""
    enabled: bool = True
    sort: int = 0
    domainStrategy: str = ""
    domainMatcher: str = ""
    ruleNum: int = 0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "RoutingItem":
        valid_keys = set(cls.__dataclass_fields__.keys())
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


@dataclass
class DNSItem:
    """DNS configuration item."""
    id: str = ""
    remarks: str = ""
    enabled: bool = True
    sort: int = 0
    normalDNS: str = ""
    tunDNS: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ServerStatItem:
    """Server statistics item."""
    indexId: str = ""
    totalUp: int = 0
    totalDown: int = 0
    todayUp: int = 0
    todayDown: int = 0


@dataclass
class ProfileExItem:
    """Profile extension/extra item."""
    indexId: str = ""
    subid: str = ""
    protoExtra: str = ""
    displayLog: bool = True
    coreBasicLoglevel: str = ""
