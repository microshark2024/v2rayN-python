"""
Shadowsocks format handler.
Mirrors ServiceLib/Handler/Fmt/ShadowsocksFmt.cs.
"""

from __future__ import annotations
import base64
from typing import Optional
from urllib.parse import urlparse

from .base_fmt import BaseFmt
from ...models.profile_item import ProfileItem
from ...common.utils import Utils


class ShadowsocksFmt(BaseFmt):
    """Shadowsocks protocol URI parser/generator."""

    SCHEME = "ss://"

    @staticmethod
    def resolve_config(uri: str) -> Optional[ProfileItem]:
        """
        Parse ss:// URI.
        Two formats:
          1. ss://BASE64(method:password)@host:port#remarks
          2. ss://BASE64(method:password@host:port)#remarks
        """
        if not uri.startswith(ShadowsocksFmt.SCHEME):
            return None

        uri_body, remarks = BaseFmt._parse_fragment(uri)
        uri_body, params = BaseFmt._parse_query(uri_body)
        rest = uri_body[len(ShadowsocksFmt.SCHEME):]

        profile = ProfileItem()
        profile.indexId = Utils.generate_id()
        profile.configType = 2  # EConfigType.Shadowsocks

        if "@" in rest:
            # Format 1: base64(method:password)@host:port
            at_idx = rest.rfind("@")
            userinfo_encoded = rest[:at_idx]
            hostport = rest[at_idx + 1:]

            decoded = Utils.base64_decode(userinfo_encoded)
            if not decoded:
                decoded = userinfo_encoded  # Not base64

            if ":" in decoded:
                method, password = decoded.split(":", 1)
            else:
                method, password = decoded, ""

            profile.security = method
            profile.password = password
        else:
            # Format 2: base64(method:password@host:port)
            decoded = Utils.base64_decode(rest)
            if not decoded:
                return None

            at_idx = decoded.rfind("@")
            if at_idx < 0:
                return None

            userinfo = decoded[:at_idx]
            hostport = decoded[at_idx + 1:]

            if ":" in userinfo:
                method, password = userinfo.split(":", 1)
            else:
                method, password = userinfo, ""

            profile.security = method
            profile.password = password

        # Parse host:port
        if ":" in hostport:
            parts = hostport.rsplit(":", 1)
            profile.address = parts[0].strip("[]")
            try:
                profile.port = int(parts[1])
            except ValueError:
                profile.port = 0
        else:
            profile.address = hostport

        profile.remarks = remarks

        # Plugin
        if "plugin" in params:
            profile.path = params["plugin"]

        ShadowsocksFmt._set_base_profile_defaults(profile)
        return profile

    @staticmethod
    def resolve_profile(item: ProfileItem) -> str:
        """Generate ss:// URI from ProfileItem."""
        userinfo = f"{item.security}:{item.password}"
        encoded = base64.b64encode(userinfo.encode()).decode()
        uri = f"{ShadowsocksFmt.SCHEME}{encoded}@{item.address}:{item.port}"
        if item.path:
            uri += f"?plugin={Utils.url_encode(item.path)}"
        if item.remarks:
            uri += f"#{Utils.url_encode(item.remarks)}"
        return uri
