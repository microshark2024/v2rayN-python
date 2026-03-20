"""
TUIC format handler.
Mirrors ServiceLib/Handler/Fmt/TuicFmt.cs.
"""

from __future__ import annotations
from typing import Optional

from .base_fmt import BaseFmt
from ...models.profile_item import ProfileItem
from ...common.utils import Utils


class TuicFmt(BaseFmt):
    """TUIC protocol URI parser/generator."""

    SCHEME = "tuic://"

    @staticmethod
    def resolve_config(uri: str) -> Optional[ProfileItem]:
        """
        Parse tuic:// URI.
        Format: tuic://uuid:password@host:port?params#remarks
        """
        if not uri.startswith(TuicFmt.SCHEME):
            return None

        uri_body, remarks = BaseFmt._parse_fragment(uri)
        rest = uri_body[len(TuicFmt.SCHEME):]
        rest, params = BaseFmt._parse_query(rest)

        at_idx = rest.rfind("@")
        if at_idx < 0:
            return None

        userinfo = rest[:at_idx]
        hostport = rest[at_idx + 1:]

        # uuid:password
        if ":" in userinfo:
            uuid, password = userinfo.split(":", 1)
        else:
            uuid, password = userinfo, ""

        if ":" in hostport:
            parts = hostport.rsplit(":", 1)
            host = parts[0].strip("[]")
            port = int(parts[1]) if parts[1].isdigit() else 443
        else:
            host = hostport
            port = 443

        profile = ProfileItem()
        profile.indexId = Utils.generate_id()
        profile.configType = 10  # EConfigType.TUIC
        profile.id = Utils.url_decode(uuid)
        profile.password = Utils.url_decode(password)
        profile.address = host
        profile.port = port
        profile.remarks = remarks

        profile.sni = params.get("sni", "")
        profile.alpn = params.get("alpn", "")
        profile.allowInsecure = params.get("allow_insecure", "")
        profile.security = params.get("congestion_control", "bbr")
        profile.headerType = params.get("udp_relay_mode", "native")

        TuicFmt._set_base_profile_defaults(profile)
        return profile

    @staticmethod
    def resolve_profile(item: ProfileItem) -> str:
        """Generate tuic:// URI from ProfileItem."""
        params = {}
        if item.sni:
            params["sni"] = item.sni
        if item.alpn:
            params["alpn"] = item.alpn
        if item.allowInsecure:
            params["allow_insecure"] = item.allowInsecure
        if item.security:
            params["congestion_control"] = item.security
        if item.headerType:
            params["udp_relay_mode"] = item.headerType

        query = "&".join(f"{k}={Utils.url_encode(v)}" for k, v in params.items() if v)
        userinfo = f"{Utils.url_encode(item.id)}:{Utils.url_encode(item.password)}"
        base = f"{TuicFmt.SCHEME}{userinfo}@{item.address}:{item.port}"
        if query:
            base += f"?{query}"
        if item.remarks:
            base += f"#{Utils.url_encode(item.remarks)}"
        return base
