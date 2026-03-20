"""
Subscription handler - fetch and parse subscription sources.
Mirrors ServiceLib/Handler/SubscriptionHandler.cs.
"""

from __future__ import annotations
import logging
import time
from typing import Optional, List, Callable, Awaitable

import requests

from ..models.sub_item import SubItem
from ..models.profile_item import ProfileItem
from ..handlers.fmt.v2ray_fmt import V2rayFmt
from ..common.utils import Utils

logger = logging.getLogger(__name__)

# Timeout for subscription download (seconds)
DOWNLOAD_TIMEOUT = 30


class SubscriptionHandler:
    """
    Handles subscription fetching, parsing, and profile import.
    Mirrors ServiceLib/Handler/SubscriptionHandler.cs.
    """

    def __init__(self, db_handler, config):
        """
        Args:
            db_handler: DatabaseHandler instance
            config: Config instance
        """
        self._db = db_handler
        self._config = config

    def update_subscription(
        self,
        sub_id: str = "",
        use_proxy: bool = False,
        progress_callback: Optional[Callable[[bool, str], None]] = None,
    ) -> None:
        """
        Update subscription(s) - download and import profiles.
        Mirrors SubscriptionHandler.UpdateProcess().

        Args:
            sub_id: If provided, update only this subscription. Empty = all.
            use_proxy: Use current proxy for downloading.
            progress_callback: fn(success, message)
        """
        subs = self._db.get_all_subs()
        if not subs:
            self._notify(progress_callback, False, "No subscriptions configured.")
            return

        if sub_id:
            subs = [s for s in subs if s.id == sub_id]

        enabled_subs = [s for s in subs if s.enabled and s.url]
        if not enabled_subs:
            self._notify(progress_callback, False, "No enabled subscriptions found.")
            return

        for sub in enabled_subs:
            self._notify(progress_callback, True, f"Updating: {sub.remarks or sub.url}")
            try:
                self._update_single_sub(sub, use_proxy, progress_callback)
            except Exception as e:
                logger.error(f"Subscription update failed for {sub.id}: {e}")
                self._notify(
                    progress_callback, False,
                    f"Failed to update {sub.remarks or sub.url}: {e}"
                )

        self._notify(progress_callback, True, "Subscription update complete.")

    def _update_single_sub(
        self,
        sub: SubItem,
        use_proxy: bool,
        progress_callback: Optional[Callable[[bool, str], None]],
    ) -> None:
        """Download and import a single subscription."""
        content = self._download(sub.url, sub.userAgent, use_proxy)
        if not content:
            self._notify(
                progress_callback, False,
                f"Empty response from {sub.url}"
            )
            return

        # Additional URLs
        if sub.moreUrl:
            for extra_url in sub.moreUrl.split("|"):
                extra_url = extra_url.strip()
                if not extra_url:
                    continue
                extra_content = self._download(extra_url, sub.userAgent, use_proxy)
                if extra_content:
                    content += "\n" + extra_content

        profiles = V2rayFmt.parse_subscription_content(content)
        if not profiles:
            self._notify(
                progress_callback, False,
                f"No valid profiles found in {sub.url}"
            )
            return

        # Apply filter if set
        if sub.filter:
            profiles = self._apply_filter(profiles, sub.filter)

        # Remove old profiles for this subscription
        self._db.delete_profiles_by_subid(sub.id)

        # Save new profiles
        for p in profiles:
            p.subid = sub.id
            p.isSub = True
            if not p.indexId:
                p.indexId = Utils.generate_id()
            p.addTime = Utils.timestamp()
            self._db.upsert_profile(p)

        # Update subscription update time
        sub.updateTime = Utils.timestamp()
        self._db.upsert_sub(sub)

        self._notify(
            progress_callback, True,
            f"Imported {len(profiles)} profiles from {sub.remarks or sub.url}"
        )

    def _download(
        self,
        url: str,
        user_agent: str = "",
        use_proxy: bool = False,
    ) -> Optional[str]:
        """Download subscription content from URL."""
        headers = {
            "User-Agent": user_agent or "v2rayN",
            "Accept": "*/*",
        }
        proxies = None
        if use_proxy:
            from ..handlers.config_handler import ConfigHandler
            socks_port = ConfigHandler.get_socks_port(self._config)
            proxies = {
                "http": f"socks5://127.0.0.1:{socks_port}",
                "https": f"socks5://127.0.0.1:{socks_port}",
            }
        try:
            resp = requests.get(
                url,
                headers=headers,
                timeout=DOWNLOAD_TIMEOUT,
                proxies=proxies,
            )
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as e:
            logger.error(f"Failed to download subscription {url}: {e}")
            return None

    @staticmethod
    def _apply_filter(profiles: List[ProfileItem], filter_str: str) -> List[ProfileItem]:
        """Apply a keyword filter to profile remarks."""
        if not filter_str:
            return profiles
        keywords = [k.strip().lower() for k in filter_str.split("|") if k.strip()]
        if not keywords:
            return profiles
        return [
            p for p in profiles
            if any(kw in (p.remarks or "").lower() for kw in keywords)
        ]

    @staticmethod
    def _notify(
        callback: Optional[Callable[[bool, str], None]],
        success: bool,
        message: str,
    ) -> None:
        logger.info(f"[Sub] {'OK' if success else 'ERR'}: {message}")
        if callback:
            try:
                callback(success, message)
            except Exception:
                pass

    # ── Manual import ─────────────────────────────────────────────────

    def import_from_clipboard(self, text: str, subid: str = "") -> int:
        """
        Import profiles from clipboard text.
        Returns the number of imported profiles.
        """
        profiles = V2rayFmt.parse_subscription_content(text)
        for p in profiles:
            p.subid = subid
            p.isSub = False
            if not p.indexId:
                p.indexId = Utils.generate_id()
            p.addTime = Utils.timestamp()
            self._db.upsert_profile(p)
        return len(profiles)

    def import_from_file(self, path: str, subid: str = "") -> int:
        """
        Import profiles from a file.
        Returns the number of imported profiles.
        """
        content = Utils.read_file(path)
        if not content:
            return 0
        return self.import_from_clipboard(content, subid)

    def export_profiles(self, index_ids: Optional[List[str]] = None) -> str:
        """
        Export selected (or all) profiles as URI list.
        """
        if index_ids:
            profiles = [
                self._db.get_profile(idx)
                for idx in index_ids
                if self._db.get_profile(idx)
            ]
        else:
            profiles = self._db.get_all_profiles()

        lines = []
        for p in profiles:
            uri = V2rayFmt.resolve_profile(p)
            if uri:
                lines.append(uri)
        return "\n".join(lines)
