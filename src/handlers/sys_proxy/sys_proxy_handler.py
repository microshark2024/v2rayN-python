"""
System proxy handler - set/clear system proxy on Windows/Linux/macOS.
Mirrors ServiceLib/Handler/SysProxy/SysProxyHandler.cs.
"""

from __future__ import annotations
import logging
import platform
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)


class SysProxyHandler:
    """
    Cross-platform system proxy manager.
    Mirrors SysProxyHandler.cs + platform-specific implementations.
    """

    @staticmethod
    def set_proxy(host: str, port: int, exceptions: str = "") -> bool:
        """Set system-level HTTP/HTTPS proxy."""
        system = platform.system()
        try:
            if system == "Windows":
                return _WindowsProxy.set_proxy(host, port, exceptions)
            elif system == "Linux":
                return _LinuxProxy.set_proxy(host, port, exceptions)
            elif system == "Darwin":
                return _MacProxy.set_proxy(host, port, exceptions)
        except Exception as e:
            logger.error(f"Failed to set system proxy: {e}")
        return False

    @staticmethod
    def clear_proxy() -> bool:
        """Remove system-level HTTP/HTTPS proxy."""
        system = platform.system()
        try:
            if system == "Windows":
                return _WindowsProxy.clear_proxy()
            elif system == "Linux":
                return _LinuxProxy.clear_proxy()
            elif system == "Darwin":
                return _MacProxy.clear_proxy()
        except Exception as e:
            logger.error(f"Failed to clear system proxy: {e}")
        return False

    @staticmethod
    def set_pac(pac_url: str) -> bool:
        """Set system PAC (proxy auto-config) URL."""
        system = platform.system()
        try:
            if system == "Windows":
                return _WindowsProxy.set_pac(pac_url)
            elif system == "Darwin":
                return _MacProxy.set_pac(pac_url)
        except Exception as e:
            logger.error(f"Failed to set PAC URL: {e}")
        return False


# ── Windows ───────────────────────────────────────────────────────────────────

class _WindowsProxy:
    REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"

    @staticmethod
    def set_proxy(host: str, port: int, exceptions: str = "") -> bool:
        try:
            import winreg
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                _WindowsProxy.REG_PATH,
                0,
                winreg.KEY_WRITE,
            ) as key:
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(
                    key, "ProxyServer", 0, winreg.REG_SZ, f"{host}:{port}"
                )
                if exceptions:
                    winreg.SetValueEx(
                        key, "ProxyOverride", 0, winreg.REG_SZ, exceptions
                    )
            _WindowsProxy._notify_change()
            return True
        except Exception as e:
            logger.error(f"Windows set proxy failed: {e}")
            return False

    @staticmethod
    def clear_proxy() -> bool:
        try:
            import winreg
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                _WindowsProxy.REG_PATH,
                0,
                winreg.KEY_WRITE,
            ) as key:
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
            _WindowsProxy._notify_change()
            return True
        except Exception as e:
            logger.error(f"Windows clear proxy failed: {e}")
            return False

    @staticmethod
    def set_pac(pac_url: str) -> bool:
        try:
            import winreg
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                _WindowsProxy.REG_PATH,
                0,
                winreg.KEY_WRITE,
            ) as key:
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
                winreg.SetValueEx(
                    key, "AutoConfigURL", 0, winreg.REG_SZ, pac_url
                )
            _WindowsProxy._notify_change()
            return True
        except Exception as e:
            logger.error(f"Windows set PAC failed: {e}")
            return False

    @staticmethod
    def _notify_change() -> None:
        """Notify the system of proxy settings change via WinHTTP."""
        try:
            import ctypes
            INTERNET_OPTION_SETTINGS_CHANGED = 39
            INTERNET_OPTION_REFRESH = 37
            wininet = ctypes.windll.wininet  # type: ignore[attr-defined]
            wininet.InternetSetOptionW(0, INTERNET_OPTION_SETTINGS_CHANGED, 0, 0)
            wininet.InternetSetOptionW(0, INTERNET_OPTION_REFRESH, 0, 0)
        except Exception:
            pass


# ── Linux ─────────────────────────────────────────────────────────────────────

class _LinuxProxy:
    """
    Linux system proxy via gsettings (GNOME) or environment variables.
    Mirrors ProxySettingLinux.cs.
    """

    @staticmethod
    def set_proxy(host: str, port: int, exceptions: str = "") -> bool:
        # Try GNOME gsettings
        if _LinuxProxy._has_gsettings():
            return _LinuxProxy._set_gnome_proxy(host, port, exceptions)
        # Fallback: write to /etc/environment (requires root) - skip
        logger.warning("gsettings not available; cannot set system proxy on Linux")
        return False

    @staticmethod
    def clear_proxy() -> bool:
        if _LinuxProxy._has_gsettings():
            return _LinuxProxy._clear_gnome_proxy()
        return False

    @staticmethod
    def _has_gsettings() -> bool:
        result = subprocess.run(["which", "gsettings"], capture_output=True)
        return result.returncode == 0

    @staticmethod
    def _set_gnome_proxy(host: str, port: int, exceptions: str) -> bool:
        try:
            cmds = [
                ["gsettings", "set", "org.gnome.system.proxy", "mode", "manual"],
                ["gsettings", "set", "org.gnome.system.proxy.http", "host", host],
                ["gsettings", "set", "org.gnome.system.proxy.http", "port", str(port)],
                ["gsettings", "set", "org.gnome.system.proxy.https", "host", host],
                ["gsettings", "set", "org.gnome.system.proxy.https", "port", str(port)],
            ]
            if exceptions:
                exc_list = "['" + "', '".join(exceptions.split(";")) + "']"
                cmds.append(
                    ["gsettings", "set", "org.gnome.system.proxy", "ignore-hosts", exc_list]
                )
            for cmd in cmds:
                subprocess.run(cmd, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"gsettings set proxy failed: {e}")
            return False

    @staticmethod
    def _clear_gnome_proxy() -> bool:
        try:
            subprocess.run(
                ["gsettings", "set", "org.gnome.system.proxy", "mode", "none"],
                check=True,
                capture_output=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"gsettings clear proxy failed: {e}")
            return False


# ── macOS ─────────────────────────────────────────────────────────────────────

class _MacProxy:
    """
    macOS system proxy via networksetup.
    Mirrors ProxySettingOSX.cs.
    """

    @staticmethod
    def _get_network_services() -> list[str]:
        result = subprocess.run(
            ["networksetup", "-listallnetworkservices"],
            capture_output=True,
            text=True,
        )
        services = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if line and not line.startswith("An asterisk"):
                services.append(line)
        return services

    @staticmethod
    def set_proxy(host: str, port: int, exceptions: str = "") -> bool:
        services = _MacProxy._get_network_services()
        success = True
        for svc in services:
            try:
                for proxy_type in ("webproxy", "securewebproxy"):
                    subprocess.run(
                        ["networksetup", f"-set{proxy_type}", svc, host, str(port)],
                        check=True,
                        capture_output=True,
                    )
                    subprocess.run(
                        ["networksetup", f"-set{proxy_type}state", svc, "on"],
                        check=True,
                        capture_output=True,
                    )
            except subprocess.CalledProcessError as e:
                logger.error(f"macOS set proxy failed for {svc}: {e}")
                success = False
        return success

    @staticmethod
    def clear_proxy() -> bool:
        services = _MacProxy._get_network_services()
        success = True
        for svc in services:
            try:
                for proxy_type in ("webproxy", "securewebproxy"):
                    subprocess.run(
                        ["networksetup", f"-set{proxy_type}state", svc, "off"],
                        check=True,
                        capture_output=True,
                    )
            except subprocess.CalledProcessError as e:
                logger.error(f"macOS clear proxy failed for {svc}: {e}")
                success = False
        return success

    @staticmethod
    def set_pac(pac_url: str) -> bool:
        services = _MacProxy._get_network_services()
        success = True
        for svc in services:
            try:
                subprocess.run(
                    ["networksetup", "-setautoproxyurl", svc, pac_url],
                    check=True,
                    capture_output=True,
                )
                subprocess.run(
                    ["networksetup", "-setautoproxystate", svc, "on"],
                    check=True,
                    capture_output=True,
                )
            except subprocess.CalledProcessError as e:
                logger.error(f"macOS set PAC failed for {svc}: {e}")
                success = False
        return success
