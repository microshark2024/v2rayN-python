"""
Tests for common utilities.
"""

import sys
import os
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from src.common.utils import Utils


class TestUtils:
    """Tests for Utils class."""

    # ── Platform detection ────────────────────────────────────────────

    def test_platform_detection(self):
        # At least one must be True
        assert Utils.is_windows() or Utils.is_linux() or Utils.is_macos()
        # Not all can be True at once
        platforms = [Utils.is_windows(), Utils.is_linux(), Utils.is_macos()]
        assert sum(platforms) == 1

    # ── String helpers ────────────────────────────────────────────────

    def test_is_null_or_empty(self):
        assert Utils.is_null_or_empty(None) is True
        assert Utils.is_null_or_empty("") is True
        assert Utils.is_null_or_empty("  ") is True
        assert Utils.is_null_or_empty("hello") is False
        assert Utils.is_null_or_empty("  hello  ") is False

    def test_to_bool(self):
        assert Utils.to_bool(True) is True
        assert Utils.to_bool(False) is False
        assert Utils.to_bool(1) is True
        assert Utils.to_bool(0) is False
        assert Utils.to_bool("true") is True
        assert Utils.to_bool("True") is True
        assert Utils.to_bool("1") is True
        assert Utils.to_bool("yes") is True
        assert Utils.to_bool("false") is False
        assert Utils.to_bool(None) is False

    def test_to_int(self):
        assert Utils.to_int("42") == 42
        assert Utils.to_int(100) == 100
        assert Utils.to_int("abc") == 0
        assert Utils.to_int("abc", default=5) == 5
        assert Utils.to_int(None) == 0

    def test_generate_id(self):
        id1 = Utils.generate_id()
        id2 = Utils.generate_id()
        assert id1 != id2
        assert len(id1) == 36  # UUID format

    # ── Base64 helpers ────────────────────────────────────────────────

    def test_base64_encode_decode(self):
        text = "Hello, World!"
        encoded = Utils.base64_encode(text)
        assert encoded != text
        decoded = Utils.base64_decode(encoded)
        assert decoded == text

    def test_base64_decode_url_safe(self):
        import base64
        text = "test string with special chars"
        encoded = base64.urlsafe_b64encode(text.encode()).decode().rstrip("=")
        decoded = Utils.base64_decode(encoded)
        assert decoded == text

    def test_base64_decode_with_padding(self):
        # Test with missing padding (common in proxy URIs)
        import base64
        text = "some text"
        encoded = base64.b64encode(text.encode()).decode()
        # Remove padding
        encoded_no_pad = encoded.rstrip("=")
        decoded = Utils.base64_decode(encoded_no_pad)
        assert decoded == text

    def test_base64_decode_invalid(self):
        assert Utils.base64_decode("!!!invalid!!!") is None
        assert Utils.base64_decode("") is None
        assert Utils.base64_decode(None) is None

    def test_base64_url_encode_decode(self):
        text = "hello world"
        encoded = Utils.base64_url_encode(text)
        decoded = Utils.base64_url_decode(encoded)
        assert decoded == text

    # ── JSON helpers ──────────────────────────────────────────────────

    def test_to_json(self):
        data = {"key": "value", "number": 42}
        result = Utils.to_json(data)
        import json
        parsed = json.loads(result)
        assert parsed["key"] == "value"
        assert parsed["number"] == 42

    def test_from_json(self):
        text = '{"hello": "world", "count": 3}'
        data = Utils.from_json(text)
        assert data["hello"] == "world"
        assert data["count"] == 3

    def test_from_json_invalid(self):
        assert Utils.from_json("not json") is None
        assert Utils.from_json("") is None

    # ── Network helpers ───────────────────────────────────────────────

    def test_is_valid_ip(self):
        assert Utils.is_valid_ip("192.168.1.1") is True
        assert Utils.is_valid_ip("8.8.8.8") is True
        assert Utils.is_valid_ip("0.0.0.0") is True
        assert Utils.is_valid_ip("999.999.999.999") is False
        assert Utils.is_valid_ip("not-an-ip") is False

    def test_is_valid_url(self):
        assert Utils.is_valid_url("https://example.com") is True
        assert Utils.is_valid_url("http://localhost:8080") is True
        assert Utils.is_valid_url("not-a-url") is False
        assert Utils.is_valid_url("") is False

    def test_is_valid_port(self):
        assert Utils.is_valid_port(80) is True
        assert Utils.is_valid_port(443) is True
        assert Utils.is_valid_port(65535) is True
        assert Utils.is_valid_port(0) is False
        assert Utils.is_valid_port(65536) is False
        assert Utils.is_valid_port(-1) is False

    def test_parse_address(self):
        host, port = Utils.parse_address("example.com:8080")
        assert host == "example.com"
        assert port == 8080

        host2, port2 = Utils.parse_address("192.168.1.1")
        assert host2 == "192.168.1.1"
        assert port2 == 0

    # ── File helpers ──────────────────────────────────────────────────

    def test_read_write_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            path = f.name

        try:
            content = "Hello, file!"
            assert Utils.write_file(path, content) is True
            read = Utils.read_file(path)
            assert read == content
        finally:
            os.unlink(path)

    def test_file_exists(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            path = f.name
        try:
            assert Utils.file_exists(path) is True
        finally:
            os.unlink(path)
        assert Utils.file_exists(path) is False

    def test_delete_file(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            path = f.name
        assert Utils.file_exists(path) is True
        assert Utils.delete_file(path) is True
        assert Utils.file_exists(path) is False

    def test_read_nonexistent_file(self):
        result = Utils.read_file("/nonexistent/path/file.txt")
        assert result is None

    # ── Hashing helpers ───────────────────────────────────────────────

    def test_md5(self):
        result = Utils.md5("hello")
        assert len(result) == 32
        assert result == Utils.md5("hello")  # Deterministic
        assert result != Utils.md5("world")

    def test_sha256(self):
        result = Utils.sha256("hello")
        assert len(result) == 64
        assert result == Utils.sha256("hello")  # Deterministic

    # ── UUID validation ───────────────────────────────────────────────

    def test_is_uuid(self):
        assert Utils.is_uuid("550e8400-e29b-41d4-a716-446655440000") is True
        assert Utils.is_uuid(Utils.generate_id()) is True
        assert Utils.is_uuid("not-a-uuid") is False
        assert Utils.is_uuid("") is False
        assert Utils.is_uuid(None) is False

    # ── Format helpers ────────────────────────────────────────────────

    def test_format_bytes(self):
        assert "B" in Utils.format_bytes(512)
        assert "KB" in Utils.format_bytes(2048)
        assert "MB" in Utils.format_bytes(2 * 1024 * 1024)
        assert "GB" in Utils.format_bytes(2 * 1024 * 1024 * 1024)

    def test_format_speed(self):
        result = Utils.format_speed(1024 * 1024)  # 1 MB/s
        assert "MB" in result
        assert "/s" in result

    # ── URL helpers ───────────────────────────────────────────────────

    def test_url_encode_decode(self):
        text = "hello world/path?query=value&key=val"
        encoded = Utils.url_encode(text)
        decoded = Utils.url_decode(encoded)
        assert decoded == text

    def test_parse_query_string(self):
        url = "https://example.com/path?key1=val1&key2=val2"
        params = Utils.parse_query_string(url)
        assert params.get("key1") == "val1"
        assert params.get("key2") == "val2"

    # ── Time helpers ──────────────────────────────────────────────────

    def test_timestamp(self):
        import time
        ts = Utils.timestamp()
        assert ts > 0
        assert abs(ts - int(time.time())) < 2

    def test_timestamp_ms(self):
        import time
        ts_ms = Utils.timestamp_ms()
        assert ts_ms > 0
        assert abs(ts_ms - int(time.time() * 1000)) < 100
