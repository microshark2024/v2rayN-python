"""
V2ray-format dispatcher.
Mirrors ServiceLib/Handler/Fmt/V2rayFmt.cs - parses any supported URI scheme.
"""

from __future__ import annotations
import re
from typing import Optional, List

from .base_fmt import BaseFmt
from .vmess_fmt import VmessFmt
from .vless_fmt import VlessFmt
from .shadowsocks_fmt import ShadowsocksFmt
from .trojan_fmt import TrojanFmt
from .hysteria2_fmt import Hysteria2Fmt
from .tuic_fmt import TuicFmt
from .wireguard_fmt import WireguardFmt
from ...models.profile_item import ProfileItem
from ...common.utils import Utils


class V2rayFmt(BaseFmt):
    """
    Dispatcher that handles all supported proxy URI formats.
    Mirrors ServiceLib/Handler/Fmt/V2rayFmt.cs.
    """

    @staticmethod
    def resolve_config(uri: str) -> Optional[ProfileItem]:
        """Parse any supported proxy URI into a ProfileItem."""
        uri = uri.strip()
        if not uri:
            return None

        if uri.startswith("vmess://"):
            return VmessFmt.resolve_config(uri)
        if uri.startswith("vless://"):
            return VlessFmt.resolve_config(uri)
        if uri.startswith("ss://"):
            return ShadowsocksFmt.resolve_config(uri)
        if uri.startswith("trojan://"):
            return TrojanFmt.resolve_config(uri)
        if uri.startswith("hysteria2://") or uri.startswith("hy2://"):
            return Hysteria2Fmt.resolve_config(uri)
        if uri.startswith("tuic://"):
            return TuicFmt.resolve_config(uri)
        if uri.startswith("wireguard://"):
            return WireguardFmt.resolve_config(uri)

        return None

    @staticmethod
    def resolve_profile(item: ProfileItem) -> str:
        """Generate URI string from ProfileItem based on its configType."""
        ct = item.configType
        if ct == 1:
            return VmessFmt.resolve_profile(item)
        if ct == 7:
            return VlessFmt.resolve_profile(item)
        if ct == 2:
            return ShadowsocksFmt.resolve_profile(item)
        if ct == 8:
            return TrojanFmt.resolve_profile(item)
        if ct == 9:
            return Hysteria2Fmt.resolve_profile(item)
        if ct == 10:
            return TuicFmt.resolve_profile(item)
        if ct == 11:
            return WireguardFmt.resolve_profile(item)
        return ""

    @staticmethod
    def parse_subscription_content(content: str) -> List[ProfileItem]:
        """
        Parse a subscription response body (may be base64 or plain text).
        Returns a list of ProfileItem instances.
        """
        items = []
        if not content:
            return items

        # Try base64 decode first
        decoded = Utils.base64_decode(content.strip())
        lines_source = decoded if decoded else content

        for line in re.split(r"\r?\n", lines_source):
            line = line.strip()
            if not line:
                continue
            profile = V2rayFmt.resolve_config(line)
            if profile:
                items.append(profile)
        return items
