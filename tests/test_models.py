"""
Tests for models - Config, ProfileItem, SubItem.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import pytest

from src.models.config import Config, CoreBasicItem, TunModeItem, UIItem
from src.models.profile_item import ProfileItem, ProtocolExtraItem
from src.models.sub_item import SubItem, RoutingItem, DNSItem


class TestConfig:
    """Tests for the Config model."""

    def test_default_config(self):
        cfg = Config()
        assert cfg.coreBasicItem.loglevel == "warning"
        assert cfg.tunModeItem.enableTun is False
        assert cfg.uiItem.mainWidth == 1366

    def test_config_serialization(self):
        cfg = Config()
        cfg.coreBasicItem.loglevel = "info"
        cfg.uiItem.mainWidth = 1920

        d = cfg.to_dict()
        assert d["coreBasicItem"]["loglevel"] == "info"
        assert d["uiItem"]["mainWidth"] == 1920

    def test_config_deserialization(self):
        data = {
            "indexId": "test-id",
            "coreBasicItem": {"loglevel": "debug", "muxEnabled": True},
            "uiItem": {"mainWidth": 1280, "mainHeight": 720},
        }
        cfg = Config.from_dict(data)
        assert cfg.indexId == "test-id"
        assert cfg.coreBasicItem.loglevel == "debug"
        assert cfg.coreBasicItem.muxEnabled is True
        assert cfg.uiItem.mainWidth == 1280
        assert cfg.uiItem.mainHeight == 720

    def test_config_roundtrip(self):
        cfg = Config()
        cfg.indexId = "roundtrip-test"
        cfg.coreBasicItem.loglevel = "error"
        cfg.tunModeItem.enableTun = True
        cfg.tunModeItem.mtu = 8000
        cfg.inbound = [{"protocol": "socks", "localPort": 10808}]

        serialized = cfg.to_dict()
        cfg2 = Config.from_dict(serialized)

        assert cfg2.indexId == "roundtrip-test"
        assert cfg2.coreBasicItem.loglevel == "error"
        assert cfg2.tunModeItem.enableTun is True
        assert cfg2.tunModeItem.mtu == 8000

    def test_partial_deserialization(self):
        """Config should handle missing fields gracefully."""
        cfg = Config.from_dict({"indexId": "only-id"})
        assert cfg.indexId == "only-id"
        # Defaults should be preserved
        assert cfg.coreBasicItem.loglevel == "warning"
        assert cfg.tunModeItem.enableTun is False

    def test_unknown_fields_ignored(self):
        """Unknown keys in the data should not raise errors."""
        cfg = Config.from_dict({"unknownField": "should be ignored", "indexId": "test"})
        assert cfg.indexId == "test"


class TestProfileItem:
    """Tests for ProfileItem model."""

    def test_default_profile(self):
        p = ProfileItem()
        assert p.configType == 1
        assert p.network == "tcp"
        assert p.delay == -1
        assert p.displayLog is True

    def test_profile_validity(self):
        p = ProfileItem(address="1.2.3.4", port=443)
        assert p.is_valid() is True

        p_empty = ProfileItem()
        assert p_empty.is_valid() is False  # No address

        p_bad_port = ProfileItem(address="1.2.3.4", port=0)
        assert p_bad_port.is_valid() is False

    def test_profile_summary(self):
        p = ProfileItem(address="1.2.3.4", port=443, remarks="MyServer")
        assert "MyServer" in p.get_summary()
        assert "443" in p.get_summary()

    def test_protocol_extra(self):
        p = ProfileItem()
        extra = ProtocolExtraItem(flow="xtls-rprx-vision")
        p.set_protocol_extra(extra)

        retrieved = p.get_protocol_extra()
        assert retrieved.flow == "xtls-rprx-vision"

    def test_profile_to_dict(self):
        p = ProfileItem(indexId="test-id", address="10.0.0.1", port=80)
        d = p.to_dict()
        assert d["indexId"] == "test-id"
        assert d["address"] == "10.0.0.1"
        assert d["port"] == 80

    def test_profile_from_dict(self):
        data = {"indexId": "abc", "address": "8.8.8.8", "port": 53, "configType": 2}
        p = ProfileItem.from_dict(data)
        assert p.indexId == "abc"
        assert p.address == "8.8.8.8"
        assert p.port == 53
        assert p.configType == 2

    def test_get_network_default(self):
        p = ProfileItem(network="")
        assert p.get_network() == "tcp"

        p2 = ProfileItem(network="ws")
        assert p2.get_network() == "ws"

    def test_alpn_parsing(self):
        p = ProfileItem(alpn="h2,http/1.1")
        alpn_list = p.get_alpn_list()
        assert alpn_list == ["h2", "http/1.1"]

        p2 = ProfileItem(alpn="")
        assert p2.get_alpn_list() is None

    def test_is_custom(self):
        p = ProfileItem(configType=99)
        assert p.is_custom() is True

        p2 = ProfileItem(configType=1)
        assert p2.is_custom() is False


class TestSubItem:
    """Tests for SubItem model."""

    def test_default_sub_item(self):
        s = SubItem()
        assert s.enabled is True
        assert s.userAgent == ""
        assert s.sort == 0

    def test_sub_item_serialization(self):
        s = SubItem(
            id="test-sub",
            remarks="My Sub",
            url="https://example.com/sub",
            enabled=True,
        )
        d = s.to_dict()
        assert d["id"] == "test-sub"
        assert d["remarks"] == "My Sub"
        assert d["url"] == "https://example.com/sub"
        assert d["enabled"] is True

    def test_sub_item_from_dict(self):
        data = {
            "id": "sub-1",
            "remarks": "Test",
            "url": "https://sub.example.com/link",
            "enabled": False,
            "autoUpdateInterval": 24,
        }
        s = SubItem.from_dict(data)
        assert s.id == "sub-1"
        assert s.remarks == "Test"
        assert s.enabled is False
        assert s.autoUpdateInterval == 24

    def test_unknown_fields_ignored(self):
        s = SubItem.from_dict({"id": "x", "unknownField": "y"})
        assert s.id == "x"


class TestRoutingItem:
    """Tests for RoutingItem model."""

    def test_default_routing(self):
        r = RoutingItem()
        assert r.enabled is True
        assert r.domainStrategy == ""

    def test_routing_from_dict(self):
        data = {"id": "r1", "remarks": "Default Routing", "domainStrategy": "IPIfNonMatch"}
        r = RoutingItem.from_dict(data)
        assert r.id == "r1"
        assert r.domainStrategy == "IPIfNonMatch"


class TestProtocolExtraItem:
    """Tests for ProtocolExtraItem."""

    def test_extra_item_defaults(self):
        e = ProtocolExtraItem()
        assert e.flow is None
        assert e.encryption is None
        assert e.extra is None

    def test_set_and_get_via_profile(self):
        p = ProfileItem()
        extra = ProtocolExtraItem(flow="xtls-rprx-vision", encryption="none")
        p.set_protocol_extra(extra)

        retrieved = p.get_protocol_extra()
        assert retrieved.flow == "xtls-rprx-vision"
        assert retrieved.encryption == "none"

    def test_empty_proto_extra(self):
        p = ProfileItem(protoExtra="")
        e = p.get_protocol_extra()
        assert e.flow is None
