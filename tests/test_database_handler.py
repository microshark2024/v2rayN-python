"""
Tests for the database handler.
"""

import sys
import os
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from src.handlers.database_handler import DatabaseHandler
from src.models.profile_item import ProfileItem
from src.models.sub_item import SubItem, RoutingItem, DNSItem, ServerStatItem


class TestDatabaseHandler:
    """Tests for DatabaseHandler."""

    @pytest.fixture
    def db(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        return DatabaseHandler(db_path)

    # ── SubItem ───────────────────────────────────────────────────────

    def test_upsert_and_get_sub(self, db):
        sub = SubItem(id="sub-1", remarks="Test Sub", url="https://example.com/sub")
        db.upsert_sub(sub)

        retrieved = db.get_sub("sub-1")
        assert retrieved is not None
        assert retrieved.id == "sub-1"
        assert retrieved.remarks == "Test Sub"
        assert retrieved.url == "https://example.com/sub"

    def test_get_all_subs(self, db):
        db.upsert_sub(SubItem(id="s1", remarks="Sub 1", url="https://a.com"))
        db.upsert_sub(SubItem(id="s2", remarks="Sub 2", url="https://b.com"))
        db.upsert_sub(SubItem(id="s3", remarks="Sub 3", url="https://c.com"))

        subs = db.get_all_subs()
        assert len(subs) == 3

    def test_update_sub(self, db):
        sub = SubItem(id="sub-upd", remarks="Original", url="https://orig.com")
        db.upsert_sub(sub)

        sub.remarks = "Updated"
        db.upsert_sub(sub)

        retrieved = db.get_sub("sub-upd")
        assert retrieved.remarks == "Updated"

    def test_delete_sub(self, db):
        db.upsert_sub(SubItem(id="del-sub", url="https://del.com"))
        db.delete_sub("del-sub")

        assert db.get_sub("del-sub") is None

    def test_get_nonexistent_sub(self, db):
        assert db.get_sub("nonexistent") is None

    # ── ProfileItem ───────────────────────────────────────────────────

    def test_upsert_and_get_profile(self, db):
        p = ProfileItem(
            indexId="p-1",
            address="1.2.3.4",
            port=443,
            configType=7,
            remarks="Test Server",
        )
        db.upsert_profile(p)

        retrieved = db.get_profile("p-1")
        assert retrieved is not None
        assert retrieved.indexId == "p-1"
        assert retrieved.address == "1.2.3.4"
        assert retrieved.port == 443
        assert retrieved.remarks == "Test Server"

    def test_get_all_profiles(self, db):
        for i in range(5):
            db.upsert_profile(ProfileItem(
                indexId=f"p-{i}", address=f"1.1.1.{i}", port=443
            ))
        profiles = db.get_all_profiles()
        assert len(profiles) == 5

    def test_filter_profiles_by_subid(self, db):
        db.upsert_profile(ProfileItem(indexId="sub-p1", address="1.1.1.1", port=80, subid="sub-a"))
        db.upsert_profile(ProfileItem(indexId="sub-p2", address="1.1.1.2", port=80, subid="sub-a"))
        db.upsert_profile(ProfileItem(indexId="sub-p3", address="1.1.1.3", port=80, subid="sub-b"))

        profiles_a = db.get_all_profiles(subid="sub-a")
        assert len(profiles_a) == 2

        profiles_b = db.get_all_profiles(subid="sub-b")
        assert len(profiles_b) == 1

    def test_delete_profile(self, db):
        db.upsert_profile(ProfileItem(indexId="del-p", address="1.2.3.4", port=80))
        db.delete_profile("del-p")
        assert db.get_profile("del-p") is None

    def test_delete_profiles_by_subid(self, db):
        for i in range(3):
            db.upsert_profile(ProfileItem(
                indexId=f"bulk-{i}", address="1.1.1.1", port=80, subid="bulk-sub"
            ))
        db.upsert_profile(ProfileItem(
            indexId="keep-1", address="2.2.2.2", port=80, subid="other-sub"
        ))

        db.delete_profiles_by_subid("bulk-sub")

        remaining = db.get_all_profiles()
        assert len(remaining) == 1
        assert remaining[0].indexId == "keep-1"

    def test_update_profile(self, db):
        p = ProfileItem(indexId="upd-p", address="1.1.1.1", port=80, remarks="Original")
        db.upsert_profile(p)

        p.remarks = "Updated"
        p.port = 8080
        db.upsert_profile(p)

        retrieved = db.get_profile("upd-p")
        assert retrieved.remarks == "Updated"
        assert retrieved.port == 8080

    # ── RoutingItem ───────────────────────────────────────────────────

    def test_upsert_routing(self, db):
        r = RoutingItem(id="r-1", remarks="Default", domainStrategy="IPIfNonMatch")
        db.upsert_routing(r)

        routings = db.get_all_routings()
        assert len(routings) == 1
        assert routings[0].id == "r-1"
        assert routings[0].domainStrategy == "IPIfNonMatch"

    def test_delete_routing(self, db):
        db.upsert_routing(RoutingItem(id="del-r"))
        db.delete_routing("del-r")
        assert len(db.get_all_routings()) == 0

    # ── ServerStatItem ────────────────────────────────────────────────

    def test_upsert_and_get_stat(self, db):
        stat = ServerStatItem(indexId="stat-1", totalUp=1024, totalDown=2048)
        db.upsert_stat(stat)

        retrieved = db.get_stat("stat-1")
        assert retrieved is not None
        assert retrieved.totalUp == 1024
        assert retrieved.totalDown == 2048

    def test_get_nonexistent_stat(self, db):
        assert db.get_stat("nonexistent") is None

    # ── Tables isolation ──────────────────────────────────────────────

    def test_tables_are_isolated(self, db):
        db.upsert_sub(SubItem(id="shared-id", url="https://example.com"))
        db.upsert_profile(ProfileItem(indexId="shared-id2", address="1.1.1.1", port=80))

        assert db.get_sub("shared-id") is not None
        assert db.get_profile("shared-id2") is not None

    def test_multiple_db_instances_share_data(self, tmp_path):
        """Two DatabaseHandler instances pointing to same file should share data."""
        db_path = str(tmp_path / "shared.db")
        db1 = DatabaseHandler(db_path)
        db2 = DatabaseHandler(db_path)

        db1.upsert_sub(SubItem(id="shared", remarks="Written by db1", url="https://x.com"))
        retrieved = db2.get_sub("shared")
        assert retrieved is not None
        assert retrieved.remarks == "Written by db1"
