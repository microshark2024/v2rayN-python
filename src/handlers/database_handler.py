"""
SQLite database handler for v2rayN.
Mirrors the SQLite database setup in AppManager.cs.
"""

from __future__ import annotations
import sqlite3
import json
import os
import logging
from typing import Optional, List, Type, TypeVar
from contextlib import contextmanager

from ..models import (
    ProfileItem, SubItem, RoutingItem, DNSItem,
    ServerStatItem, ProfileExItem
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class DatabaseHandler:
    """
    Handles all SQLite database operations.
    Uses a single database file with separate tables per model type.
    """

    DB_FILE = "v2rayN.db"

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_tables()

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ── Table initialization ──────────────────────────────────────────

    def _init_tables(self) -> None:
        """Create all required tables if they do not exist."""
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS SubItem (
                    id TEXT PRIMARY KEY,
                    data TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS ProfileItem (
                    indexId TEXT PRIMARY KEY,
                    data TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS RoutingItem (
                    id TEXT PRIMARY KEY,
                    data TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS DNSItem (
                    id TEXT PRIMARY KEY,
                    data TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS ServerStatItem (
                    indexId TEXT PRIMARY KEY,
                    data TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS ProfileExItem (
                    indexId TEXT PRIMARY KEY,
                    data TEXT NOT NULL
                );
            """)

    # ── Generic helpers ───────────────────────────────────────────────

    def _serialize(self, obj) -> str:
        """Serialize a dataclass instance to JSON."""
        if hasattr(obj, "to_dict"):
            return json.dumps(obj.to_dict())
        return json.dumps(obj.__dict__)

    def _deserialize(self, cls, data: str):
        """Deserialize JSON string to a dataclass instance."""
        d = json.loads(data)
        if hasattr(cls, "from_dict"):
            return cls.from_dict(d)
        return cls(**d)

    # ── SubItem ───────────────────────────────────────────────────────

    def get_all_subs(self) -> List[SubItem]:
        with self._connect() as conn:
            rows = conn.execute("SELECT data FROM SubItem ORDER BY rowid").fetchall()
        items = []
        for row in rows:
            try:
                items.append(self._deserialize(SubItem, row["data"]))
            except Exception as e:
                logger.error(f"Failed to deserialize SubItem: {e}")
        return items

    def get_sub(self, sub_id: str) -> Optional[SubItem]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT data FROM SubItem WHERE id=?", (sub_id,)
            ).fetchone()
        if row:
            try:
                return self._deserialize(SubItem, row["data"])
            except Exception:
                return None
        return None

    def upsert_sub(self, item: SubItem) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO SubItem (id, data) VALUES (?, ?)",
                (item.id, self._serialize(item))
            )

    def delete_sub(self, sub_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM SubItem WHERE id=?", (sub_id,))

    # ── ProfileItem ───────────────────────────────────────────────────

    def get_all_profiles(self, subid: Optional[str] = None) -> List[ProfileItem]:
        with self._connect() as conn:
            if subid is not None:
                rows = conn.execute(
                    "SELECT data FROM ProfileItem ORDER BY rowid"
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT data FROM ProfileItem ORDER BY rowid"
                ).fetchall()
        items = []
        for row in rows:
            try:
                p = self._deserialize(ProfileItem, row["data"])
                if subid is None or p.subid == subid:
                    items.append(p)
            except Exception as e:
                logger.error(f"Failed to deserialize ProfileItem: {e}")
        return items

    def get_profile(self, index_id: str) -> Optional[ProfileItem]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT data FROM ProfileItem WHERE indexId=?", (index_id,)
            ).fetchone()
        if row:
            try:
                return self._deserialize(ProfileItem, row["data"])
            except Exception:
                return None
        return None

    def upsert_profile(self, item: ProfileItem) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO ProfileItem (indexId, data) VALUES (?, ?)",
                (item.indexId, self._serialize(item))
            )

    def delete_profile(self, index_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM ProfileItem WHERE indexId=?", (index_id,))

    def delete_profiles_by_subid(self, subid: str) -> None:
        """Delete all profiles belonging to a subscription."""
        profiles = self.get_all_profiles(subid=subid)
        with self._connect() as conn:
            for p in profiles:
                conn.execute("DELETE FROM ProfileItem WHERE indexId=?", (p.indexId,))

    # ── RoutingItem ───────────────────────────────────────────────────

    def get_all_routings(self) -> List[RoutingItem]:
        with self._connect() as conn:
            rows = conn.execute("SELECT data FROM RoutingItem ORDER BY rowid").fetchall()
        items = []
        for row in rows:
            try:
                items.append(self._deserialize(RoutingItem, row["data"]))
            except Exception as e:
                logger.error(f"Failed to deserialize RoutingItem: {e}")
        return items

    def upsert_routing(self, item: RoutingItem) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO RoutingItem (id, data) VALUES (?, ?)",
                (item.id, self._serialize(item))
            )

    def delete_routing(self, routing_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM RoutingItem WHERE id=?", (routing_id,))

    # ── DNSItem ───────────────────────────────────────────────────────

    def get_all_dns(self) -> List[DNSItem]:
        with self._connect() as conn:
            rows = conn.execute("SELECT data FROM DNSItem ORDER BY rowid").fetchall()
        items = []
        for row in rows:
            try:
                items.append(self._deserialize(DNSItem, row["data"]))
            except Exception as e:
                logger.error(f"Failed to deserialize DNSItem: {e}")
        return items

    def upsert_dns(self, item: DNSItem) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO DNSItem (id, data) VALUES (?, ?)",
                (item.id, self._serialize(item))
            )

    # ── ServerStatItem ────────────────────────────────────────────────

    def get_stat(self, index_id: str) -> Optional[ServerStatItem]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT data FROM ServerStatItem WHERE indexId=?", (index_id,)
            ).fetchone()
        if row:
            try:
                return self._deserialize(ServerStatItem, row["data"])
            except Exception:
                return None
        return None

    def upsert_stat(self, item: ServerStatItem) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO ServerStatItem (indexId, data) VALUES (?, ?)",
                (item.indexId, self._serialize(item))
            )

    # ── ProfileExItem ─────────────────────────────────────────────────

    def get_profile_ex(self, index_id: str) -> Optional[ProfileExItem]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT data FROM ProfileExItem WHERE indexId=?", (index_id,)
            ).fetchone()
        if row:
            try:
                return self._deserialize(ProfileExItem, row["data"])
            except Exception:
                return None
        return None

    def upsert_profile_ex(self, item: ProfileExItem) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO ProfileExItem (indexId, data) VALUES (?, ?)",
                (item.indexId, self._serialize(item))
            )
