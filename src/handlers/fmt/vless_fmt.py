"""
VLESS format handler.
Mirrors ServiceLib/Handler/Fmt/VLESSFmt.cs.
"""

from __future__ import annotations
from typing import Optional
from urllib.parse import urlparse, parse_qs, unquote

from .base_fmt import BaseFmt
from ...models.profile_item import ProfileItem
from ...common.utils import Utils


class VlessFmt(BaseFmt):
    """VLESS protocol URI parser/generator."""

    SCHEME = "vless://"

    @staticmethod
    def resolve_config(uri: str) -> Optional[ProfileItem]:
        """
        Parse vless:// URI.
        Format: vless://uuid@host:port?params#remarks
        """
        if not uri.startswith(VlessFmt.SCHEME):
            return None

        uri_body, remarks = BaseFmt._parse_fragment(uri)
        # Strip scheme
        rest = uri_body[len(VlessFmt.SCHEME):]
        uri_body_with_params, params = BaseFmt._parse_query(rest)

        # uuid@host:port
        at_idx = uri_body_with_params.rfind("@")
        if at_idx < 0:
            return None

        uuid = uri_body_with_params[:at_idx]
        hostport = uri_body_with_params[at_idx + 1:]

        # Handle IPv6
        if hostport.startswith("["):
            bracket = hostport.index("]")
            host = hostport[1:bracket]
            port_str = hostport[bracket + 2:]  # skip ]:
        elif ":" in hostport:
            parts = hostport.rsplit(":", 1)
            host = parts[0]
            port_str = parts[1]
        else:
            host = hostport
            port_str = "0"

        profile = ProfileItem()
        profile.indexId = Utils.generate_id()
        profile.configType = 7  # EConfigType.VLESS
        profile.id = uuid
        profile.address = host
        profile.port = int(port_str) if port_str.isdigit() else 0
        profile.remarks = remarks

        # Transport
        profile.network = params.get("type", "tcp")
        profile.headerType = params.get("headerType", "none")
        profile.requestHost = params.get("host", "")
        profile.path = params.get("path", "")
        profile.path = params.get("serviceName", profile.path)  # gRPC

        # Security
        security = params.get("security", "none")
        profile.streamSecurity = security if security in ("tls", "reality") else "none"
        profile.sni = params.get("sni", "")
        profile.alpn = params.get("alpn", "")
        profile.fingerprint = params.get("fp", "")
        profile.allowInsecure = params.get("allowInsecure", "")

        # Reality
        profile.publicKey = params.get("pbk", "")
        profile.shortId = params.get("sid", "")
        profile.spiderX = params.get("spx", "")

        # Flow
        flow = params.get("flow", "")
        if flow:
            extra = profile.get_protocol_extra()
            extra.flow = flow
            profile.set_protocol_extra(extra)

        # Encryption
        profile.security = params.get("encryption", "none")

        VlessFmt._set_base_profile_defaults(profile)
        return profile

    @staticmethod
    def resolve_profile(item: ProfileItem) -> str:
        """Generate vless:// URI from ProfileItem."""
        params = {}
        params["type"] = item.network or "tcp"
        if item.headerType:
            params["headerType"] = item.headerType
        if item.requestHost:
            params["host"] = item.requestHost
        if item.path:
            params["path"] = item.path
        if item.streamSecurity and item.streamSecurity != "none":
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
            params["spx"] = item.spiderX or ""

        extra = item.get_protocol_extra()
        if extra.flow:
            params["flow"] = extra.flow
        if item.security and item.security != "none":
            params["encryption"] = item.security

        query = "&".join(f"{k}={Utils.url_encode(v)}" for k, v in params.items() if v)
        base = f"{VlessFmt.SCHEME}{item.id}@{item.address}:{item.port}"
        if query:
            base += f"?{query}"
        if item.remarks:
            base += f"#{Utils.url_encode(item.remarks)}"
        return base
