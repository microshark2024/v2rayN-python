"""
Trojan format handler.
Mirrors ServiceLib/Handler/Fmt/TrojanFmt.cs.
"""

from __future__ import annotations
from typing import Optional

from .base_fmt import BaseFmt
from ...models.profile_item import ProfileItem
from ...common.utils import Utils


class TrojanFmt(BaseFmt):
    """Trojan protocol URI parser/generator."""

    SCHEME = "trojan://"

    @staticmethod
    def resolve_config(uri: str) -> Optional[ProfileItem]:
        """
        Parse trojan:// URI.
        Format: trojan://password@host:port?params#remarks
        """
        if not uri.startswith(TrojanFmt.SCHEME):
            return None

        uri_body, remarks = BaseFmt._parse_fragment(uri)
        rest = uri_body[len(TrojanFmt.SCHEME):]
        rest, params = BaseFmt._parse_query(rest)

        at_idx = rest.rfind("@")
        if at_idx < 0:
            return None

        password = Utils.url_decode(rest[:at_idx])
        hostport = rest[at_idx + 1:]

        if ":" in hostport:
            parts = hostport.rsplit(":", 1)
            host = parts[0].strip("[]")
            port = int(parts[1]) if parts[1].isdigit() else 0
        else:
            host = hostport
            port = 443

        profile = ProfileItem()
        profile.indexId = Utils.generate_id()
        profile.configType = 8  # EConfigType.Trojan
        profile.password = password
        profile.address = host
        profile.port = port
        profile.remarks = remarks

        # Transport
        profile.network = params.get("type", "tcp")
        profile.requestHost = params.get("host", "")
        profile.path = params.get("path", "")
        profile.path = params.get("serviceName", profile.path)

        # Security
        security = params.get("security", "tls")
        profile.streamSecurity = security if security in ("tls", "reality") else "tls"
        profile.sni = params.get("sni", "")
        profile.alpn = params.get("alpn", "")
        profile.fingerprint = params.get("fp", "")
        profile.allowInsecure = params.get("allowInsecure", "")

        # Reality
        profile.publicKey = params.get("pbk", "")
        profile.shortId = params.get("sid", "")
        profile.spiderX = params.get("spx", "")

        TrojanFmt._set_base_profile_defaults(profile)
        return profile

    @staticmethod
    def resolve_profile(item: ProfileItem) -> str:
        """Generate trojan:// URI from ProfileItem."""
        params = {}
        if item.network and item.network != "tcp":
            params["type"] = item.network
        if item.requestHost:
            params["host"] = item.requestHost
        if item.path:
            params["path"] = item.path
        if item.streamSecurity and item.streamSecurity not in ("", "none"):
            params["security"] = item.streamSecurity
        if item.sni:
            params["sni"] = item.sni
        if item.alpn:
            params["alpn"] = item.alpn
        if item.fingerprint:
            params["fp"] = item.fingerprint
        if item.streamSecurity == "reality":
            params["pbk"] = item.publicKey or ""
            params["sid"] = item.shortId or ""

        query = "&".join(f"{k}={Utils.url_encode(v)}" for k, v in params.items() if v)
        base = f"{TrojanFmt.SCHEME}{Utils.url_encode(item.password)}@{item.address}:{item.port}"
        if query:
            base += f"?{query}"
        if item.remarks:
            base += f"#{Utils.url_encode(item.remarks)}"
        return base
