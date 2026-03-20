"""
Core process service - manages a single proxy core process.
Mirrors ServiceLib/Services/ProcessService.cs.
"""

from __future__ import annotations
import os
import subprocess
import threading
import logging
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class ProcessService:
    """
    Manages a single proxy-core subprocess (v2ray, xray, sing-box, etc.).
    Mirrors ServiceLib/Services/ProcessService.cs.
    """

    def __init__(
        self,
        executable: str,
        config_path: str,
        working_dir: str = "",
        display_log: bool = True,
        env: Optional[dict] = None,
        log_callback: Optional[Callable[[str], None]] = None,
    ):
        self.executable = executable
        self.config_path = config_path
        self.working_dir = working_dir or os.path.dirname(executable)
        self.display_log = display_log
        self.env = env
        self.log_callback = log_callback

        self._process: Optional[subprocess.Popen] = None
        self._log_thread: Optional[threading.Thread] = None
        self._running = False

    @property
    def is_running(self) -> bool:
        if self._process is None:
            return False
        return self._process.poll() is None

    def start(self) -> bool:
        """Start the proxy core process."""
        if not os.path.isfile(self.executable):
            logger.error(f"Core executable not found: {self.executable}")
            return False

        cmd = self._build_command()
        env = {**os.environ, **(self.env or {})}

        try:
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=self.working_dir,
                env=env,
            )
            self._running = True

            if self.display_log:
                self._log_thread = threading.Thread(
                    target=self._read_logs, daemon=True
                )
                self._log_thread.start()

            logger.info(f"Started core: {' '.join(cmd)} (PID={self._process.pid})")
            return True
        except Exception as e:
            logger.error(f"Failed to start core process: {e}")
            return False

    def stop(self) -> None:
        """Stop the proxy core process."""
        self._running = False
        if self._process and self._process.poll() is None:
            try:
                self._process.terminate()
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
            except Exception as e:
                logger.error(f"Error stopping core process: {e}")
            finally:
                self._process = None
        logger.info("Core process stopped.")

    def _build_command(self) -> list[str]:
        """Build the subprocess command list."""
        # Most cores: <executable> run -c <config>
        # Some cores use different argument styles
        exe_name = os.path.basename(self.executable).lower()
        if "sing-box" in exe_name or "singbox" in exe_name:
            return [self.executable, "run", "-c", self.config_path]
        elif "mihomo" in exe_name or "clash" in exe_name:
            return [self.executable, "-f", self.config_path]
        elif "hysteria" in exe_name:
            return [self.executable, "client", "--config", self.config_path]
        elif "naiveproxy" in exe_name or "naive" in exe_name:
            return [self.executable, self.config_path]
        elif "brook" in exe_name:
            return [self.executable, "--config", self.config_path]
        else:
            # v2ray/xray default
            return [self.executable, "run", "-c", self.config_path]

    def _read_logs(self) -> None:
        """Read and forward stdout/stderr lines."""
        if not self._process or not self._process.stdout:
            return
        try:
            for line in self._process.stdout:
                if not self._running:
                    break
                text = line.decode("utf-8", errors="replace").rstrip()
                logger.debug(f"[CORE] {text}")
                if self.log_callback:
                    try:
                        self.log_callback(text)
                    except Exception:
                        pass
        except Exception:
            pass
