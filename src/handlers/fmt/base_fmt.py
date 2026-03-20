"""
Base format handler for proxy URI parsing.
Mirrors ServiceLib/Handler/Fmt/BaseFmt.cs.
"""

from __future__ import annotations
import re
from typing import Optional, List
from ...models.profile_item import ProfileItem
from ...common.utils import Utils


class BaseFmt:
    """Base class for proxy format parsers/generators."""

    @staticmethod
    def resolve_profile(item: ProfileItem) -> str:
        """Generate URI string from profile item (to be overridden)."""
        return ""

    @staticmethod
    def resolve_config(uri: str) -> Optional[ProfileItem]:
        """Parse URI string into ProfileItem (to be overridden)."""
        return None

    @staticmethod
    def _set_base_profile_defaults(profile: ProfileItem) -> None:
        """Set default values on a newly created profile."""
        if not profile.indexId:
            profile.indexId = Utils.generate_id()
        if not profile.remarks:
            profile.remarks = f"{profile.address}:{profile.port}"

    @staticmethod
    def _parse_fragment(uri: str) -> tuple[str, str]:
        """Split URI into (main_part, fragment_part)."""
        if "#" in uri:
            idx = uri.index("#")
            return uri[:idx], Utils.url_decode(uri[idx + 1:])
        return uri, ""

    @staticmethod
    def _parse_query(uri: str) -> tuple[str, dict]:
        """Split URI into (path_part, query_dict)."""
        if "?" in uri:
            idx = uri.index("?")
            path = uri[:idx]
            query_str = uri[idx + 1:]
            if "#" in query_str:
                query_str = query_str[: query_str.index("#")]
            params = {}
            for kv in query_str.split("&"):
                if "=" in kv:
                    k, v = kv.split("=", 1)
                    params[Utils.url_decode(k)] = Utils.url_decode(v)
            return path, params
        return uri, {}
