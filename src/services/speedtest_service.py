"""
Speed test service.
Mirrors ServiceLib/Services/SpeedtestService.cs.
"""

from __future__ import annotations
import logging
import socket
import time
import threading
from typing import Optional, List, Callable

import requests

from ..models.profile_item import ProfileItem, ServerTestItem
from ..common.utils import Utils

logger = logging.getLogger(__name__)


class SpeedtestService:
    """
    Performs latency / speed tests on proxy servers.
    Mirrors ServiceLib/Services/SpeedtestService.cs.
    """

    def __init__(
        self,
        ping_url: str = "https://www.google.com/generate_204",
        speedtest_url: str = "",
        timeout: int = 10,
    ):
        self.ping_url = ping_url
        self.speedtest_url = speedtest_url
        self.timeout = timeout

    # ── Latency test ──────────────────────────────────────────────────

    def ping_server(self, host: str, port: int) -> int:
        """
        TCP connect-time latency test (ms). Returns -1 on failure.
        """
        try:
            start = time.time()
            with socket.create_connection((host, port), timeout=self.timeout):
                pass
            return int((time.time() - start) * 1000)
        except Exception:
            return -1

    def real_ping(
        self,
        proxy_host: str,
        proxy_port: int,
        test_url: Optional[str] = None,
    ) -> int:
        """
        HTTP latency test via local proxy (ms). Returns -1 on failure.
        """
        url = test_url or self.ping_url
        proxies = {
            "http": f"socks5://{proxy_host}:{proxy_port}",
            "https": f"socks5://{proxy_host}:{proxy_port}",
        }
        try:
            start = time.time()
            resp = requests.get(url, proxies=proxies, timeout=self.timeout)
            elapsed_ms = int((time.time() - start) * 1000)
            if resp.status_code in (200, 204):
                return elapsed_ms
            return -1
        except Exception:
            return -1

    # ── Speed test ────────────────────────────────────────────────────

    def speed_test(
        self,
        proxy_host: str,
        proxy_port: int,
        download_url: Optional[str] = None,
        duration_secs: int = 5,
    ) -> float:
        """
        Download speed test via local proxy (bytes/sec). Returns 0 on failure.
        """
        url = download_url or self.speedtest_url
        if not url:
            return 0.0

        proxies = {
            "http": f"socks5://{proxy_host}:{proxy_port}",
            "https": f"socks5://{proxy_host}:{proxy_port}",
        }
        total_bytes = 0
        start = time.time()
        try:
            with requests.get(
                url,
                proxies=proxies,
                timeout=self.timeout,
                stream=True,
            ) as resp:
                resp.raise_for_status()
                for chunk in resp.iter_content(chunk_size=65536):
                    total_bytes += len(chunk)
                    if time.time() - start >= duration_secs:
                        break
            elapsed = time.time() - start
            return total_bytes / elapsed if elapsed > 0 else 0.0
        except Exception as e:
            logger.debug(f"Speed test error: {e}")
            return 0.0

    # ── Batch test ────────────────────────────────────────────────────

    def batch_ping(
        self,
        items: List[ServerTestItem],
        progress_callback: Optional[Callable[[ServerTestItem], None]] = None,
        max_workers: int = 10,
    ) -> List[ServerTestItem]:
        """
        Run TCP ping on multiple servers in parallel.
        """
        results = []
        lock = threading.Lock()
        sem = threading.Semaphore(max_workers)

        def _test(item: ServerTestItem):
            with sem:
                if item.profileItem:
                    p = item.profileItem
                    delay = self.ping_server(p.address, p.port)
                    item.delay = delay
                    item.success = delay >= 0
                with lock:
                    results.append(item)
                if progress_callback:
                    try:
                        progress_callback(item)
                    except Exception:
                        pass

        threads = [threading.Thread(target=_test, args=(it,), daemon=True) for it in items]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        return results
