"""
Hysteria2 format handler.
Mirrors ServiceLib/Handler/Fmt/Hysteria2Fmt.cs.
"""

from __future__ import annotations
from typing import Optional

from .base_fmt import BaseFmt
from ...models.profile_item import ProfileItem
from ...common.utils import Utils


class Hysteria2Fmt(BaseFmt):
    """Hysteria2 protocol URI parser/generator."""

    SCHEMES = ("hysteria2://", "hy2://")

    @staticmethod
    def resolve_config(uri: str) -> Optional[ProfileItem]:
        """
        Parse hysteria2:// or hy2:// URI.
        Format: hysteria2://password@host:port?params#remarks
        """
        scheme = None
        for s in Hysteria2Fmt.SCHEMES:
            if uri.startswith(s):
                scheme = s
                break
        if not scheme:
            return None

        uri_body, remarks = BaseFmt._parse_fragment(uri)
        rest = uri_body[len(scheme):]
        rest, params = BaseFmt._parse_query(rest)

        at_idx = rest.rfind("@")
        if at_idx >= 0:
            password = Utils.url_decode(rest[:at_idx])
            hostport = rest[at_idx + 1:]
        else:
            password = ""
            hostport = rest

        if ":" in hostport:
            parts = hostport.rsplit(":", 1)
            host = parts[0].strip("[]")
            port = int(parts[1]) if parts[1].isdigit() else 443
        else:
            host = hostport
            port = 443

        profile = ProfileItem()
        profile.indexId = Utils.generate_id()
        profile.configType = 9  # EConfigType.Hysteria2
        profile.password = password
        profile.address = host
        profile.port = port
        profile.remarks = remarks

        # TLS
        profile.sni = params.get("sni", "")
        profile.allowInsecure = params.get("insecure", "")
        profile.fingerprint = params.get("pinSHA256", "")

        # Obfs
        obfs = params.get("obfs", "")
        obfs_password = params.get("obfs-password", "")
        if obfs:
            extra = profile.get_protocol_extra()
            extra.extra = f"{obfs}:{obfs_password}"
            profile.set_protocol_extra(extra)

        Hysteria2Fmt._set_base_profile_defaults(profile)
        return profile

    @staticmethod
    def resolve_profile(item: ProfileItem) -> str:
        """Generate hysteria2:// URI from ProfileItem."""
        params = {}
        if item.sni:
            params["sni"] = item.sni
        if item.allowInsecure:
            params["insecure"] = item.allowInsecure

        extra = item.get_protocol_extra()
        if extra.extra:
            parts = extra.extra.split(":", 1)
            params["obfs"] = parts[0]
            if len(parts) > 1:
                params["obfs-password"] = parts[1]

        query = "&".join(f"{k}={Utils.url_encode(v)}" for k, v in params.items() if v)
        base = (
            f"hysteria2://{Utils.url_encode(item.password)}@{item.address}:{item.port}"
        )
        if query:
            base += f"?{query}"
        if item.remarks:
            base += f"#{Utils.url_encode(item.remarks)}"
        return base
