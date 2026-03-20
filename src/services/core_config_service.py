"""
Core configuration generator.
Generates JSON config files for v2ray/xray/sing-box cores.
Mirrors ServiceLib/Services/CoreConfig/*.cs.
"""

from __future__ import annotations
import json
import os
import logging
from typing import Optional, List

from ..models.config import Config
from ..models.profile_item import ProfileItem

logger = logging.getLogger(__name__)


class CoreConfigService:
    """
    Generates proxy core configuration files.
    Mirrors CoreConfigHandler + CoreConfigV2rayService + CoreConfigSingboxService.
    """

    def __init__(self, config: Config, config_dir: str):
        self.config = config
        self.config_dir = config_dir

    def generate_v2ray_config(
        self,
        profile: ProfileItem,
        output_path: Optional[str] = None,
        inbound_port: int = 10808,
        http_port: int = 10809,
    ) -> Optional[dict]:
        """
        Generate a v2ray/xray JSON configuration for a given profile.
        Returns the config dict; also writes to output_path if provided.
        """
        cfg = self._build_v2ray_config(profile, inbound_port, http_port)
        if output_path:
            try:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(cfg, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.error(f"Failed to write core config: {e}")
                return None
        return cfg

    def generate_singbox_config(
        self,
        profile: ProfileItem,
        output_path: Optional[str] = None,
        inbound_port: int = 10808,
        http_port: int = 10809,
    ) -> Optional[dict]:
        """
        Generate a sing-box JSON configuration for a given profile.
        """
        cfg = self._build_singbox_config(profile, inbound_port, http_port)
        if output_path:
            try:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(cfg, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.error(f"Failed to write sing-box config: {e}")
                return None
        return cfg

    # ── V2ray / Xray config builder ───────────────────────────────────

    def _build_v2ray_config(
        self,
        profile: ProfileItem,
        socks_port: int,
        http_port: int,
    ) -> dict:
        """Build complete v2ray/xray JSON configuration."""
        cfg = self.config
        log_level = cfg.coreBasicItem.loglevel or "warning"

        outbound = self._build_v2ray_outbound(profile)
        inbounds = self._build_v2ray_inbounds(socks_port, http_port)
        routing = self._build_v2ray_routing()
        dns = self._build_v2ray_dns()

        config_dict = {
            "log": {"loglevel": log_level},
            "inbounds": inbounds,
            "outbounds": [
                outbound,
                {"tag": "direct", "protocol": "freedom"},
                {"tag": "block", "protocol": "blackhole"},
            ],
            "routing": routing,
            "dns": dns,
        }

        # Stats API
        config_dict["api"] = {
            "tag": "api",
            "services": ["StatsService"],
        }
        config_dict["stats"] = {}
        config_dict["policy"] = {
            "levels": {"0": {"statsUserUplink": True, "statsUserDownlink": True}},
            "system": {
                "statsInboundDownlink": True,
                "statsInboundUplink": True,
                "statsOutboundDownlink": True,
                "statsOutboundUplink": True,
            },
        }

        return config_dict

    def _build_v2ray_inbounds(self, socks_port: int, http_port: int) -> list:
        """Build inbound configuration."""
        inbounds = [
            {
                "tag": "socks",
                "port": socks_port,
                "listen": "127.0.0.1",
                "protocol": "socks",
                "settings": {"auth": "noauth", "udp": True},
                "sniffing": {"enabled": True, "destOverride": ["http", "tls", "quic"]},
            },
            {
                "tag": "http",
                "port": http_port,
                "listen": "127.0.0.1",
                "protocol": "http",
                "settings": {},
                "sniffing": {"enabled": True, "destOverride": ["http", "tls", "quic"]},
            },
        ]
        return inbounds

    def _build_v2ray_outbound(self, profile: ProfileItem) -> dict:
        """Build outbound config based on profile type."""
        ct = profile.configType

        if ct == 1:  # VMess
            return self._vmess_outbound(profile)
        elif ct == 7:  # VLESS
            return self._vless_outbound(profile)
        elif ct == 2:  # Shadowsocks
            return self._ss_outbound(profile)
        elif ct == 8:  # Trojan
            return self._trojan_outbound(profile)
        elif ct == 3:  # Socks
            return self._socks_outbound(profile)
        else:
            # Fallback to freedom
            return {"tag": "proxy", "protocol": "freedom"}

    def _stream_settings(self, profile: ProfileItem) -> dict:
        """Build streamSettings for v2ray outbound."""
        net = profile.network or "tcp"
        security = profile.streamSecurity or "none"

        settings: dict = {"network": net}

        # TLS / Reality
        if security == "tls":
            tls = {
                "serverName": profile.sni or profile.address,
                "allowInsecure": profile.allowInsecure in ("1", "true", "True"),
            }
            if profile.alpn:
                tls["alpn"] = [a.strip() for a in profile.alpn.split(",")]
            if profile.fingerprint:
                tls["fingerprint"] = profile.fingerprint
            settings["tlsSettings"] = tls
            settings["security"] = "tls"
        elif security == "reality":
            settings["security"] = "reality"
            settings["realitySettings"] = {
                "serverName": profile.sni or profile.address,
                "fingerprint": profile.fingerprint or "chrome",
                "publicKey": profile.publicKey or "",
                "shortId": profile.shortId or "",
                "spiderX": profile.spiderX or "",
            }
        else:
            settings["security"] = "none"

        # Network-specific settings
        if net == "ws":
            ws = {}
            if profile.path:
                ws["path"] = profile.path
            if profile.requestHost:
                ws["headers"] = {"Host": profile.requestHost}
            settings["wsSettings"] = ws
        elif net == "grpc":
            settings["grpcSettings"] = {
                "serviceName": profile.path or "",
                "multiMode": False,
            }
        elif net == "h2":
            h2 = {}
            if profile.path:
                h2["path"] = profile.path
            if profile.requestHost:
                h2["host"] = [profile.requestHost]
            settings["httpSettings"] = h2
        elif net == "tcp":
            if profile.headerType == "http":
                req = {"version": "1.1", "method": "GET", "path": [profile.path or "/"]}
                if profile.requestHost:
                    req["headers"] = {"Host": [profile.requestHost]}
                settings["tcpSettings"] = {
                    "header": {"type": "http", "request": req}
                }
        elif net == "kcp":
            settings["kcpSettings"] = {
                "header": {"type": profile.headerType or "none"},
                "seed": profile.path or "",
            }
        elif net == "httpupgrade":
            settings["httpupgradeSettings"] = {
                "path": profile.path or "/",
                "host": profile.requestHost or "",
            }
        elif net == "xhttp":
            settings["xhttpSettings"] = {
                "path": profile.path or "/",
                "host": profile.requestHost or "",
                "mode": profile.headerType or "auto",
            }

        return settings

    def _vmess_outbound(self, profile: ProfileItem) -> dict:
        return {
            "tag": "proxy",
            "protocol": "vmess",
            "settings": {
                "vnext": [{
                    "address": profile.address,
                    "port": profile.port,
                    "users": [{
                        "id": profile.id,
                        "alterId": profile.alterId or 0,
                        "security": profile.security or "auto",
                    }],
                }]
            },
            "streamSettings": self._stream_settings(profile),
        }

    def _vless_outbound(self, profile: ProfileItem) -> dict:
        user = {
            "id": profile.id,
            "encryption": profile.security or "none",
        }
        extra = profile.get_protocol_extra()
        if extra.flow:
            user["flow"] = extra.flow
        return {
            "tag": "proxy",
            "protocol": "vless",
            "settings": {
                "vnext": [{
                    "address": profile.address,
                    "port": profile.port,
                    "users": [user],
                }]
            },
            "streamSettings": self._stream_settings(profile),
        }

    def _ss_outbound(self, profile: ProfileItem) -> dict:
        return {
            "tag": "proxy",
            "protocol": "shadowsocks",
            "settings": {
                "servers": [{
                    "address": profile.address,
                    "port": profile.port,
                    "method": profile.security or "aes-256-gcm",
                    "password": profile.password,
                    "uot": False,
                }]
            },
        }

    def _trojan_outbound(self, profile: ProfileItem) -> dict:
        return {
            "tag": "proxy",
            "protocol": "trojan",
            "settings": {
                "servers": [{
                    "address": profile.address,
                    "port": profile.port,
                    "password": profile.password,
                }]
            },
            "streamSettings": self._stream_settings(profile),
        }

    def _socks_outbound(self, profile: ProfileItem) -> dict:
        return {
            "tag": "proxy",
            "protocol": "socks",
            "settings": {
                "servers": [{
                    "address": profile.address,
                    "port": profile.port,
                    "users": [{"user": profile.username, "pass": profile.password}]
                    if profile.username else [],
                }]
            },
        }

    def _build_v2ray_routing(self) -> dict:
        """Build routing configuration."""
        cfg = self.config
        rule_mode = 1  # Bypass (default)

        rules = []

        # API rule
        rules.append({
            "type": "field",
            "inboundTag": ["api"],
            "outboundTag": "api",
        })

        if rule_mode == 0:  # Global
            rules.append({"type": "field", "network": "tcp,udp", "outboundTag": "proxy"})
        elif rule_mode == 1:  # Bypass (bypass LAN and China)
            rules += [
                {"type": "field", "ip": ["geoip:private"], "outboundTag": "direct"},
                {"type": "field", "ip": ["geoip:cn"], "outboundTag": "direct"},
                {"type": "field", "domain": ["geosite:cn"], "outboundTag": "direct"},
            ]
        # Default final rule: proxy
        rules.append({"type": "field", "network": "tcp,udp", "outboundTag": "proxy"})

        return {
            "domainStrategy": cfg.routingBasicItem.domainStrategy or "IPIfNonMatch",
            "domainMatcher": cfg.routingBasicItem.domainMatcher or "hybrid",
            "rules": rules,
        }

    def _build_v2ray_dns(self) -> dict:
        """Build DNS configuration."""
        return {
            "servers": [
                {"address": "https://1.1.1.1/dns-query", "domains": ["geosite:geolocation-!cn"]},
                {"address": "223.5.5.5", "domains": ["geosite:cn"]},
                "8.8.8.8",
                "localhost",
            ]
        }

    # ── Sing-box config builder ────────────────────────────────────────

    def _build_singbox_config(
        self,
        profile: ProfileItem,
        socks_port: int,
        http_port: int,
    ) -> dict:
        """Build a basic sing-box JSON configuration."""
        log_level = self.config.coreBasicItem.loglevel or "warn"

        inbounds = [
            {
                "type": "socks",
                "tag": "socks-in",
                "listen": "127.0.0.1",
                "listen_port": socks_port,
                "udp": True,
                "sniff": True,
            },
            {
                "type": "http",
                "tag": "http-in",
                "listen": "127.0.0.1",
                "listen_port": http_port,
                "sniff": True,
            },
        ]

        outbound = self._singbox_outbound(profile)
        outbounds = [
            outbound,
            {"type": "direct", "tag": "direct"},
            {"type": "block", "tag": "block"},
            {"type": "dns", "tag": "dns-out"},
        ]

        return {
            "log": {"level": log_level, "timestamp": True},
            "dns": {
                "servers": [
                    {"tag": "remote", "address": "https://1.1.1.1/dns-query"},
                    {"tag": "local", "address": "223.5.5.5", "detour": "direct"},
                ],
                "rules": [
                    {"geosite": "cn", "server": "local"},
                ],
            },
            "inbounds": inbounds,
            "outbounds": outbounds,
            "route": {
                "rules": [
                    {"geoip": ["private", "cn"], "outbound": "direct"},
                    {"geosite": "cn", "outbound": "direct"},
                ],
                "auto_detect_interface": True,
            },
        }

    def _singbox_outbound(self, profile: ProfileItem) -> dict:
        """Build sing-box outbound for a profile."""
        ct = profile.configType

        base = {
            "tag": "proxy",
            "server": profile.address,
            "server_port": profile.port,
        }

        tls = None
        if profile.streamSecurity in ("tls", "reality"):
            tls = {
                "enabled": True,
                "server_name": profile.sni or profile.address,
                "insecure": profile.allowInsecure in ("1", "true", "True"),
            }
            if profile.alpn:
                tls["alpn"] = [a.strip() for a in profile.alpn.split(",")]
            if profile.streamSecurity == "reality":
                tls["reality"] = {
                    "enabled": True,
                    "public_key": profile.publicKey or "",
                    "short_id": profile.shortId or "",
                }
                tls["utls"] = {"enabled": True, "fingerprint": profile.fingerprint or "chrome"}

        transport = None
        net = profile.network or "tcp"
        if net == "ws":
            transport = {
                "type": "ws",
                "path": profile.path or "/",
                "headers": {"Host": profile.requestHost} if profile.requestHost else {},
            }
        elif net == "grpc":
            transport = {"type": "grpc", "service_name": profile.path or ""}
        elif net == "h2":
            transport = {
                "type": "http",
                "host": [profile.requestHost] if profile.requestHost else [],
                "path": profile.path or "/",
            }

        if ct == 1:  # VMess
            out = {**base, "type": "vmess", "uuid": profile.id,
                   "alter_id": profile.alterId or 0, "security": profile.security or "auto"}
        elif ct == 7:  # VLESS
            out = {**base, "type": "vless", "uuid": profile.id,
                   "flow": profile.get_protocol_extra().flow or ""}
        elif ct == 2:  # Shadowsocks
            out = {**base, "type": "shadowsocks",
                   "method": profile.security or "aes-256-gcm",
                   "password": profile.password}
        elif ct == 8:  # Trojan
            out = {**base, "type": "trojan", "password": profile.password}
        elif ct == 9:  # Hysteria2
            return {
                "tag": "proxy",
                "type": "hysteria2",
                "server": profile.address,
                "server_port": profile.port,
                "password": profile.password,
                "tls": {
                    "enabled": True,
                    "server_name": profile.sni or profile.address,
                    "insecure": profile.allowInsecure in ("1", "true"),
                },
            }
        elif ct == 10:  # TUIC
            return {
                "tag": "proxy",
                "type": "tuic",
                "server": profile.address,
                "server_port": profile.port,
                "uuid": profile.id,
                "password": profile.password,
                "congestion_control": profile.security or "bbr",
                "tls": {
                    "enabled": True,
                    "server_name": profile.sni or profile.address,
                    "insecure": profile.allowInsecure in ("1", "true"),
                    "alpn": ["h3"],
                },
            }
        elif ct == 11:  # WireGuard
            return {
                "tag": "proxy",
                "type": "wireguard",
                "server": profile.address,
                "server_port": profile.port,
                "private_key": profile.id,
                "peer_public_key": profile.publicKey or "",
                "local_address": [profile.path] if profile.path else ["10.0.0.2/32"],
            }
        else:
            out = {**base, "type": "direct"}

        if tls:
            out["tls"] = tls
        if transport:
            out["transport"] = transport

        return out
