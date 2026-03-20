"""
Common utility functions for v2rayN Python implementation.
Mirrors ServiceLib/Common/Utils.cs.
"""

import os
import sys
import platform
import subprocess
import socket
import time
import json
import base64
import hashlib
import uuid
import re
import logging
from typing import Optional, Any
from urllib.parse import urlparse, parse_qs


logger = logging.getLogger(__name__)


class Utils:
    """Common utility functions."""

    # ── Platform detection ────────────────────────────────────────────

    @staticmethod
    def is_windows() -> bool:
        return platform.system() == "Windows"

    @staticmethod
    def is_linux() -> bool:
        return platform.system() == "Linux"

    @staticmethod
    def is_macos() -> bool:
        return platform.system() == "Darwin"

    # ── Path helpers ──────────────────────────────────────────────────

    @staticmethod
    def get_app_dir() -> str:
        """Get application root directory."""
        return os.path.dirname(os.path.abspath(sys.argv[0]))

    @staticmethod
    def get_bin_dir() -> str:
        """Get core binaries directory."""
        return os.path.join(Utils.get_app_dir(), "bin")

    @staticmethod
    def get_config_dir() -> str:
        """Get user config directory (cross-platform)."""
        if Utils.is_windows():
            base = os.environ.get("APPDATA", os.path.expanduser("~"))
        elif Utils.is_macos():
            base = os.path.expanduser("~/Library/Application Support")
        else:
            base = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
        path = os.path.join(base, "v2rayN")
        os.makedirs(path, exist_ok=True)
        return path

    @staticmethod
    def get_logs_dir() -> str:
        """Get logs directory."""
        path = os.path.join(Utils.get_config_dir(), "logs")
        os.makedirs(path, exist_ok=True)
        return path

    @staticmethod
    def get_temp_dir() -> str:
        """Get temporary directory."""
        import tempfile
        return tempfile.gettempdir()

    # ── String helpers ────────────────────────────────────────────────

    @staticmethod
    def is_null_or_empty(s: Optional[str]) -> bool:
        return not s or not s.strip()

    @staticmethod
    def to_bool(value: Any, default: bool = False) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return value != 0
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes")
        return default

    @staticmethod
    def to_int(value: Any, default: int = 0) -> int:
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def generate_id() -> str:
        """Generate a unique ID."""
        return str(uuid.uuid4())

    @staticmethod
    def get_guid() -> str:
        """Generate a GUID string."""
        return str(uuid.uuid4())

    # ── Base64 helpers ────────────────────────────────────────────────

    @staticmethod
    def base64_encode(text: str) -> str:
        """Encode text to Base64."""
        return base64.b64encode(text.encode("utf-8")).decode("ascii")

    @staticmethod
    def base64_decode(text: str) -> Optional[str]:
        """Decode Base64 text, handling URL-safe and standard variants."""
        if not text:
            return None
        # Normalize padding and variant
        text = text.strip().replace("-", "+").replace("_", "/")
        pad = len(text) % 4
        if pad:
            text += "=" * (4 - pad)
        try:
            return base64.b64decode(text).decode("utf-8")
        except Exception:
            return None

    @staticmethod
    def base64_url_encode(text: str) -> str:
        """URL-safe Base64 encode."""
        return base64.urlsafe_b64encode(text.encode("utf-8")).decode("ascii").rstrip("=")

    @staticmethod
    def base64_url_decode(text: str) -> Optional[str]:
        """URL-safe Base64 decode."""
        if not text:
            return None
        pad = len(text) % 4
        if pad:
            text += "=" * (4 - pad)
        try:
            return base64.urlsafe_b64decode(text).decode("utf-8")
        except Exception:
            return None

    # ── JSON helpers ──────────────────────────────────────────────────

    @staticmethod
    def to_json(obj: Any, indent: int = 2) -> str:
        """Serialize object to JSON string."""
        return json.dumps(obj, ensure_ascii=False, indent=indent, default=str)

    @staticmethod
    def from_json(text: str) -> Any:
        """Deserialize JSON string to object."""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None

    # ── Network helpers ───────────────────────────────────────────────

    @staticmethod
    def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
        """Check if a port is currently in use."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect((host, port))
                return True
            except (ConnectionRefusedError, OSError):
                return False

    @staticmethod
    def get_free_port(start: int = 10000) -> int:
        """Find a free port starting from given number."""
        port = start
        while port < 65535:
            if not Utils.is_port_in_use(port):
                return port
            port += 1
        raise RuntimeError("No free port available")

    @staticmethod
    def is_valid_ip(address: str) -> bool:
        """Check if string is a valid IP address."""
        try:
            socket.inet_aton(address)
            return True
        except socket.error:
            return False

    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Check if string is a valid URL."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    @staticmethod
    def parse_address(address: str) -> tuple[str, int]:
        """Parse 'host:port' string into (host, port) tuple."""
        if ":" in address:
            parts = address.rsplit(":", 1)
            return parts[0], int(parts[1])
        return address, 0

    # ── File helpers ──────────────────────────────────────────────────

    @staticmethod
    def read_file(path: str, encoding: str = "utf-8") -> Optional[str]:
        """Read file contents as string."""
        try:
            with open(path, "r", encoding=encoding) as f:
                return f.read()
        except (OSError, IOError) as e:
            logger.error(f"Failed to read file {path}: {e}")
            return None

    @staticmethod
    def write_file(path: str, content: str, encoding: str = "utf-8") -> bool:
        """Write string content to file."""
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding=encoding) as f:
                f.write(content)
            return True
        except (OSError, IOError) as e:
            logger.error(f"Failed to write file {path}: {e}")
            return False

    @staticmethod
    def file_exists(path: str) -> bool:
        return os.path.isfile(path)

    @staticmethod
    def delete_file(path: str) -> bool:
        """Delete file if it exists."""
        try:
            if os.path.exists(path):
                os.remove(path)
            return True
        except (OSError, IOError) as e:
            logger.error(f"Failed to delete file {path}: {e}")
            return False

    # ── Process helpers ───────────────────────────────────────────────

    @staticmethod
    def run_command(cmd: list[str], cwd: Optional[str] = None) -> tuple[int, str, str]:
        """Run a command and return (returncode, stdout, stderr)."""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=cwd,
            )
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return -1, "", str(e)

    @staticmethod
    def run_command_async(
        cmd: list[str],
        cwd: Optional[str] = None,
        env: Optional[dict] = None,
    ) -> subprocess.Popen:
        """Start a command asynchronously, returning the Popen handle."""
        return subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            env=env,
        )

    # ── Hashing helpers ───────────────────────────────────────────────

    @staticmethod
    def md5(text: str) -> str:
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    @staticmethod
    def sha256(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    # ── Time helpers ──────────────────────────────────────────────────

    @staticmethod
    def timestamp() -> int:
        """Current Unix timestamp in seconds."""
        return int(time.time())

    @staticmethod
    def timestamp_ms() -> int:
        """Current Unix timestamp in milliseconds."""
        return int(time.time() * 1000)

    # ── URI parsing ───────────────────────────────────────────────────

    @staticmethod
    def parse_query_string(url: str) -> dict[str, str]:
        """Parse query parameters from URL into dict."""
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        return {k: v[0] for k, v in params.items()}

    @staticmethod
    def url_decode(text: str) -> str:
        """URL-decode a string."""
        from urllib.parse import unquote
        return unquote(text)

    @staticmethod
    def url_encode(text: str) -> str:
        """URL-encode a string."""
        from urllib.parse import quote
        return quote(text)

    # ── Validation helpers ────────────────────────────────────────────

    @staticmethod
    def is_valid_port(port: int) -> bool:
        return 1 <= port <= 65535

    @staticmethod
    def is_uuid(value: str) -> bool:
        """Check if string is a valid UUID."""
        pattern = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            re.IGNORECASE,
        )
        return bool(pattern.match(value or ""))

    # ── Format helpers ────────────────────────────────────────────────

    @staticmethod
    def format_bytes(size: int) -> str:
        """Format byte size to human readable string."""
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"

    @staticmethod
    def format_speed(speed_bps: float) -> str:
        """Format speed in bytes/sec to human readable string."""
        return Utils.format_bytes(int(speed_bps)) + "/s"
