"""
WireGuard format handler.
Mirrors ServiceLib/Handler/Fmt/WireguardFmt.cs.
"""

from __future__ import annotations
from typing import Optional

from .base_fmt import BaseFmt
from ...models.profile_item import ProfileItem
from ...common.utils import Utils


class WireguardFmt(BaseFmt):
    """WireGuard protocol URI parser/generator."""

    SCHEME = "wireguard://"

    @staticmethod
    def resolve_config(uri: str) -> Optional[ProfileItem]:
        """
        Parse wireguard:// URI.
        Format: wireguard://privatekey@host:port?params#remarks
        """
        if not uri.startswith(WireguardFmt.SCHEME):
            return None

        uri_body, remarks = BaseFmt._parse_fragment(uri)
        rest = uri_body[len(WireguardFmt.SCHEME):]
        rest, params = BaseFmt._parse_query(rest)

        at_idx = rest.rfind("@")
        if at_idx >= 0:
            private_key = Utils.url_decode(rest[:at_idx])
            hostport = rest[at_idx + 1:]
        else:
            private_key = ""
            hostport = rest

        if ":" in hostport:
            parts = hostport.rsplit(":", 1)
            host = parts[0].strip("[]")
            port = int(parts[1]) if parts[1].isdigit() else 51820
        else:
            host = hostport
            port = 51820

        profile = ProfileItem()
        profile.indexId = Utils.generate_id()
        profile.configType = 11  # EConfigType.WireGuard
        profile.id = private_key          # private key stored in id field
        profile.address = host
        profile.port = port
        profile.remarks = remarks

        profile.publicKey = params.get("publickey", "")
        profile.path = params.get("address", "")       # local IP
        profile.requestHost = params.get("dns", "")
        profile.sni = params.get("presharedkey", "")
        profile.security = params.get("mtu", "1420")

        WireguardFmt._set_base_profile_defaults(profile)
        return profile

    @staticmethod
    def resolve_profile(item: ProfileItem) -> str:
        """Generate wireguard:// URI from ProfileItem."""
        params = {}
        if item.publicKey:
            params["publickey"] = item.publicKey
        if item.path:
            params["address"] = item.path
        if item.requestHost:
            params["dns"] = item.requestHost
        if item.sni:
            params["presharedkey"] = item.sni
        if item.security:
            params["mtu"] = item.security

        query = "&".join(f"{k}={Utils.url_encode(v)}" for k, v in params.items() if v)
        base = f"{WireguardFmt.SCHEME}{Utils.url_encode(item.id)}@{item.address}:{item.port}"
        if query:
            base += f"?{query}"
        if item.remarks:
            base += f"#{Utils.url_encode(item.remarks)}"
        return base
