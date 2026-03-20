"""
VMess format handler.
Mirrors ServiceLib/Handler/Fmt/VmessFmt.cs.
"""

from __future__ import annotations
import json
import base64
from typing import Optional

from .base_fmt import BaseFmt
from ...models.profile_item import ProfileItem
from ...common.utils import Utils


class VmessFmt(BaseFmt):
    """VMess protocol URI parser/generator."""

    SCHEME = "vmess://"

    @staticmethod
    def resolve_config(uri: str) -> Optional[ProfileItem]:
        """
        Parse vmess:// URI into a ProfileItem.
        The content after 'vmess://' is a base64-encoded JSON object.
        """
        if not uri.startswith(VmessFmt.SCHEME):
            return None

        encoded = uri[len(VmessFmt.SCHEME):]
        decoded = Utils.base64_decode(encoded)
        if not decoded:
            return None

        try:
            d = json.loads(decoded)
        except json.JSONDecodeError:
            return None

        profile = ProfileItem()
        profile.indexId = Utils.generate_id()
        profile.configType = 1  # EConfigType.VMess

        profile.id = d.get("id", "")
        profile.alterId = int(d.get("aid", 0))
        profile.security = d.get("scy", d.get("security", "auto"))
        profile.address = d.get("add", "")
        profile.port = int(d.get("port", 0))
        profile.remarks = d.get("ps", "")

        # Transport
        profile.network = d.get("net", "tcp")
        profile.headerType = d.get("type", "none")
        profile.requestHost = d.get("host", "")
        profile.path = d.get("path", "")

        # TLS
        tls = d.get("tls", "")
        profile.streamSecurity = tls if tls in ("tls", "reality") else "none"
        profile.sni = d.get("sni", "")
        profile.alpn = d.get("alpn", "")
        profile.fingerprint = d.get("fp", "")

        # Reality
        profile.publicKey = d.get("pbk", "")
        profile.shortId = d.get("sid", "")
        profile.spiderX = d.get("spx", "")

        VmessFmt._set_base_profile_defaults(profile)
        return profile

    @staticmethod
    def resolve_profile(item: ProfileItem) -> str:
        """Generate vmess:// URI from ProfileItem."""
        d = {
            "v": "2",
            "ps": item.remarks,
            "add": item.address,
            "port": str(item.port),
            "id": item.id,
            "aid": str(item.alterId),
            "scy": item.security or "auto",
            "net": item.network or "tcp",
            "type": item.headerType or "none",
            "host": item.requestHost or "",
            "path": item.path or "",
            "tls": item.streamSecurity or "",
            "sni": item.sni or "",
            "alpn": item.alpn or "",
            "fp": item.fingerprint or "",
        }
        if item.streamSecurity == "reality":
            d["pbk"] = item.publicKey or ""
            d["sid"] = item.shortId or ""
            d["spx"] = item.spiderX or ""

        json_str = json.dumps(d, ensure_ascii=False)
        encoded = base64.b64encode(json_str.encode("utf-8")).decode("ascii")
        return VmessFmt.SCHEME + encoded
