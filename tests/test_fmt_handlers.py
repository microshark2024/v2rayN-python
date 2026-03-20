"""
Tests for format handlers - URI parsing and generation.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from src.handlers.fmt.vmess_fmt import VmessFmt
from src.handlers.fmt.vless_fmt import VlessFmt
from src.handlers.fmt.shadowsocks_fmt import ShadowsocksFmt
from src.handlers.fmt.trojan_fmt import TrojanFmt
from src.handlers.fmt.hysteria2_fmt import Hysteria2Fmt
from src.handlers.fmt.tuic_fmt import TuicFmt
from src.handlers.fmt.wireguard_fmt import WireguardFmt
from src.handlers.fmt.v2ray_fmt import V2rayFmt


class TestVmessFmt:
    """Tests for VMess URI parsing/generation."""

    SAMPLE_VMESS = (
        "vmess://eyJ2IjoiMiIsInBzIjoidGVzdCIsImFkZCI6IjEuMi4zLjQiLCJwb3J0IjoiNDQzIiwi"
        "aWQiOiJhYmNkZWZnaCIsImFpZCI6IjAiLCJzY3kiOiJhdXRvIiwibmV0Ijoid3MiLCJ0eXBlIjoibm9uZSIs"
        "Imhvc3QiOiJleGFtcGxlLmNvbSIsInBhdGgiOiIvd3MiLCJ0bHMiOiJ0bHMiLCJzbmkiOiJleGFtcGxlLmNvbSIsImFscG4iOiIiLCJmcCI6IiJ9"
    )

    def test_parse_vmess_uri(self):
        import json, base64
        payload = {
            "v": "2", "ps": "test", "add": "1.2.3.4", "port": "443",
            "id": "abcdefgh", "aid": "0", "scy": "auto",
            "net": "ws", "type": "none", "host": "example.com",
            "path": "/ws", "tls": "tls", "sni": "example.com", "alpn": "", "fp": ""
        }
        encoded = base64.b64encode(json.dumps(payload).encode()).decode()
        uri = "vmess://" + encoded
        profile = VmessFmt.resolve_config(uri)

        assert profile is not None
        assert profile.address == "1.2.3.4"
        assert profile.port == 443
        assert profile.id == "abcdefgh"
        assert profile.network == "ws"
        assert profile.streamSecurity == "tls"
        assert profile.sni == "example.com"
        assert profile.remarks == "test"

    def test_roundtrip_vmess(self):
        import json, base64
        payload = {
            "v": "2", "ps": "MyServer", "add": "10.0.0.1", "port": "8443",
            "id": "test-uuid-1234", "aid": "0", "scy": "auto",
            "net": "tcp", "type": "none", "host": "", "path": "",
            "tls": "", "sni": "", "alpn": "", "fp": ""
        }
        encoded = base64.b64encode(json.dumps(payload).encode()).decode()
        uri = "vmess://" + encoded
        profile = VmessFmt.resolve_config(uri)
        assert profile is not None

        generated = VmessFmt.resolve_profile(profile)
        assert generated.startswith("vmess://")

        # Parse again and verify
        profile2 = VmessFmt.resolve_config(generated)
        assert profile2 is not None
        assert profile2.address == profile.address
        assert profile2.port == profile.port
        assert profile2.id == profile.id

    def test_invalid_vmess(self):
        assert VmessFmt.resolve_config("vmess://") is None
        assert VmessFmt.resolve_config("vmess://notbase64!!") is None
        assert VmessFmt.resolve_config("vless://something") is None


class TestVlessFmt:
    """Tests for VLESS URI parsing/generation."""

    def test_parse_basic_vless(self):
        uri = "vless://my-uuid-1234@192.168.1.1:443?type=ws&host=example.com&path=%2Fws&security=tls&sni=example.com#MyServer"
        profile = VlessFmt.resolve_config(uri)

        assert profile is not None
        assert profile.id == "my-uuid-1234"
        assert profile.address == "192.168.1.1"
        assert profile.port == 443
        assert profile.network == "ws"
        assert profile.requestHost == "example.com"
        assert profile.path == "/ws"
        assert profile.streamSecurity == "tls"
        assert profile.sni == "example.com"
        assert profile.remarks == "MyServer"

    def test_parse_vless_reality(self):
        uri = (
            "vless://uuid123@example.com:443"
            "?type=tcp&security=reality&pbk=pubkey123&sid=shortid&fp=chrome&sni=example.com"
            "#RealityServer"
        )
        profile = VlessFmt.resolve_config(uri)
        assert profile is not None
        assert profile.streamSecurity == "reality"
        assert profile.publicKey == "pubkey123"
        assert profile.shortId == "shortid"
        assert profile.fingerprint == "chrome"

    def test_generate_vless_uri(self):
        uri = "vless://my-uuid@10.0.0.1:80?type=tcp#Test"
        profile = VlessFmt.resolve_config(uri)
        assert profile is not None
        generated = VlessFmt.resolve_profile(profile)
        assert "vless://" in generated
        assert "my-uuid" in generated
        assert "10.0.0.1" in generated

    def test_invalid_vless(self):
        assert VlessFmt.resolve_config("vless://") is None
        assert VlessFmt.resolve_config("not a vless uri") is None


class TestShadowsocksFmt:
    """Tests for Shadowsocks URI parsing/generation."""

    def test_parse_ss_format1(self):
        # Format: ss://base64(method:password)@host:port#remarks
        import base64
        userinfo = base64.b64encode(b"aes-256-gcm:mypassword").decode()
        uri = f"ss://{userinfo}@1.2.3.4:8388#MyServer"
        profile = ShadowsocksFmt.resolve_config(uri)

        assert profile is not None
        assert profile.address == "1.2.3.4"
        assert profile.port == 8388
        assert profile.security == "aes-256-gcm"
        assert profile.password == "mypassword"
        assert profile.remarks == "MyServer"

    def test_parse_ss_format2(self):
        # Format: ss://base64(method:password@host:port)#remarks
        import base64
        content = "aes-256-gcm:pass@1.2.3.4:1080"
        encoded = base64.b64encode(content.encode()).decode()
        uri = f"ss://{encoded}#Server2"
        profile = ShadowsocksFmt.resolve_config(uri)

        assert profile is not None
        assert profile.address == "1.2.3.4"
        assert profile.port == 1080
        assert profile.security == "aes-256-gcm"
        assert profile.password == "pass"

    def test_roundtrip_ss(self):
        import base64
        userinfo = base64.b64encode(b"chacha20-poly1305:secret").decode()
        uri = f"ss://{userinfo}@5.5.5.5:9999#TestSS"
        profile = ShadowsocksFmt.resolve_config(uri)
        assert profile is not None

        generated = ShadowsocksFmt.resolve_profile(profile)
        assert generated.startswith("ss://")

        profile2 = ShadowsocksFmt.resolve_config(generated)
        assert profile2 is not None
        assert profile2.address == profile.address
        assert profile2.port == profile.port
        assert profile2.security == profile.security
        assert profile2.password == profile.password

    def test_invalid_ss(self):
        assert ShadowsocksFmt.resolve_config("ss://") is None
        assert ShadowsocksFmt.resolve_config("trojan://test@1.2.3.4:443") is None


class TestTrojanFmt:
    """Tests for Trojan URI parsing/generation."""

    def test_parse_trojan(self):
        uri = "trojan://mypassword@1.2.3.4:443?sni=example.com#TrojanServer"
        profile = TrojanFmt.resolve_config(uri)

        assert profile is not None
        assert profile.password == "mypassword"
        assert profile.address == "1.2.3.4"
        assert profile.port == 443
        assert profile.sni == "example.com"
        assert profile.remarks == "TrojanServer"

    def test_roundtrip_trojan(self):
        uri = "trojan://pass@10.0.0.1:443?sni=test.example.com#Test"
        profile = TrojanFmt.resolve_config(uri)
        assert profile is not None

        generated = TrojanFmt.resolve_profile(profile)
        assert "trojan://" in generated

        profile2 = TrojanFmt.resolve_config(generated)
        assert profile2 is not None
        assert profile2.password == profile.password
        assert profile2.address == profile.address

    def test_invalid_trojan(self):
        assert TrojanFmt.resolve_config("trojan://") is None
        assert TrojanFmt.resolve_config("vmess://something") is None


class TestHysteria2Fmt:
    """Tests for Hysteria2 URI parsing/generation."""

    def test_parse_hysteria2(self):
        uri = "hysteria2://mypassword@1.2.3.4:443?sni=example.com&insecure=0#Hy2Server"
        profile = Hysteria2Fmt.resolve_config(uri)

        assert profile is not None
        assert profile.password == "mypassword"
        assert profile.address == "1.2.3.4"
        assert profile.port == 443
        assert profile.sni == "example.com"
        assert profile.remarks == "Hy2Server"

    def test_parse_hy2_scheme(self):
        uri = "hy2://password@10.0.0.1:8080#Test"
        profile = Hysteria2Fmt.resolve_config(uri)
        assert profile is not None
        assert profile.password == "password"

    def test_roundtrip_hysteria2(self):
        uri = "hysteria2://secret@1.1.1.1:443?sni=cloudflare.com#Test"
        profile = Hysteria2Fmt.resolve_config(uri)
        assert profile is not None
        generated = Hysteria2Fmt.resolve_profile(profile)
        assert "hysteria2://" in generated
        profile2 = Hysteria2Fmt.resolve_config(generated)
        assert profile2 is not None
        assert profile2.password == profile.password
        assert profile2.address == profile.address


class TestV2rayFmt:
    """Tests for V2rayFmt dispatcher."""

    def test_dispatch_vmess(self):
        import json, base64
        payload = {"v": "2", "ps": "t", "add": "1.1.1.1", "port": "443",
                   "id": "id", "aid": "0", "scy": "auto", "net": "tcp",
                   "type": "none", "host": "", "path": "", "tls": "", "sni": "", "alpn": "", "fp": ""}
        uri = "vmess://" + base64.b64encode(json.dumps(payload).encode()).decode()
        p = V2rayFmt.resolve_config(uri)
        assert p is not None
        assert p.configType == 1

    def test_dispatch_vless(self):
        uri = "vless://uuid@1.2.3.4:443?type=tcp#Test"
        p = V2rayFmt.resolve_config(uri)
        assert p is not None
        assert p.configType == 7

    def test_dispatch_ss(self):
        import base64
        userinfo = base64.b64encode(b"aes-256-gcm:pass").decode()
        uri = f"ss://{userinfo}@1.2.3.4:8388#T"
        p = V2rayFmt.resolve_config(uri)
        assert p is not None
        assert p.configType == 2

    def test_dispatch_trojan(self):
        uri = "trojan://pass@1.2.3.4:443#T"
        p = V2rayFmt.resolve_config(uri)
        assert p is not None
        assert p.configType == 8

    def test_dispatch_hy2(self):
        uri = "hysteria2://pass@1.2.3.4:443#T"
        p = V2rayFmt.resolve_config(uri)
        assert p is not None
        assert p.configType == 9

    def test_dispatch_unknown(self):
        assert V2rayFmt.resolve_config("unknown://test") is None
        assert V2rayFmt.resolve_config("") is None

    def test_parse_subscription_content_base64(self):
        import base64
        lines = [
            "vless://uuid1@1.1.1.1:443?type=tcp#S1",
            "trojan://pass@2.2.2.2:443#S2",
        ]
        content = base64.b64encode("\n".join(lines).encode()).decode()
        profiles = V2rayFmt.parse_subscription_content(content)
        assert len(profiles) == 2

    def test_parse_subscription_content_plain(self):
        lines = [
            "vless://uuid2@3.3.3.3:443?type=tcp#S3",
            "trojan://pw@4.4.4.4:443#S4",
            "not-a-proxy://invalid",
        ]
        content = "\n".join(lines)
        profiles = V2rayFmt.parse_subscription_content(content)
        assert len(profiles) == 2
