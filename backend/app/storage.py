"""Chart library: ChartSubject records in SQLite, birth data encrypted at rest (Fernet, key file).

Only the id, kind, tags, settings and timestamps are stored in clear; everything that identifies
a person or a birth (name, datetime, place, coordinates, zone, notes) is one encrypted blob.
Delete is soft: rows get deleted_at and can be restored. Nothing is ever destroyed.
"""
from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from cryptography.fernet import Fernet
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = Path(os.environ.get("ASTRO_DB_PATH", ROOT / "data" / "charts.sqlite"))
DEFAULT_KEY_PATH = Path(os.environ.get("ASTRO_KEY_PATH", ROOT / "data" / "keys" / "charts.key"))

Kind = Literal["person", "event", "place", "question"]
TimeConfidence = Literal["exact", "within_5_min", "within_30_min", "unknown"]

SECRET_FIELDS = ("name", "notes", "datetime_local", "place_name", "lat", "lon", "timezone", "utc_offset_override")


class SubjectIn(BaseModel):
    name: str
    kind: Kind = "person"
    tags: list[str] = Field(default_factory=list)
    notes: str = ""
    datetime_local: datetime
    time_confidence: TimeConfidence = "exact"
    place_name: str = ""
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    timezone: str | None = None
    utc_offset_override: str | None = None
    settings: dict = Field(default_factory=dict)


class Subject(SubjectIn):
    id: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def load_or_create_key(key_path: Path) -> bytes:
    if key_path.exists():
        return key_path.read_bytes().strip()
    key_path.parent.mkdir(parents=True, exist_ok=True)
    key = Fernet.generate_key()
    fd = os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(key)
    os.chmod(key_path, 0o600)
    return key


class ChartLibrary:
    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH, key_path: Path | str = DEFAULT_KEY_PATH):
        self.db_path = Path(db_path)
        self.key_path = Path(key_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._fernet = Fernet(load_or_create_key(self.key_path))
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute(
            """CREATE TABLE IF NOT EXISTS subjects (
                 id TEXT PRIMARY KEY,
                 kind TEXT NOT NULL,
                 tags TEXT NOT NULL,
                 time_confidence TEXT NOT NULL,
                 settings TEXT NOT NULL,
                 secret BLOB NOT NULL,
                 created_at TEXT NOT NULL,
                 updated_at TEXT NOT NULL,
                 deleted_at TEXT
               )"""
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    # -- encryption -------------------------------------------------------
    def _seal(self, s: SubjectIn) -> bytes:
        payload = {k: getattr(s, k) for k in SECRET_FIELDS}
        payload["datetime_local"] = s.datetime_local.isoformat()
        return self._fernet.encrypt(json.dumps(payload).encode("utf-8"))

    def _open(self, blob: bytes) -> dict:
        data = json.loads(self._fernet.decrypt(blob).decode("utf-8"))
        data["datetime_local"] = datetime.fromisoformat(data["datetime_local"])
        return data

    def _row_to_subject(self, row: sqlite3.Row) -> Subject:
        secret = self._open(row["secret"])
        return Subject(
            id=row["id"], kind=row["kind"], tags=json.loads(row["tags"]), time_confidence=row["time_confidence"],
            settings=json.loads(row["settings"]), created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            deleted_at=datetime.fromisoformat(row["deleted_at"]) if row["deleted_at"] else None, **secret,
        )

    # -- CRUD ---------------------------------------------------------------
    def create(self, s: SubjectIn) -> Subject:
        sid = uuid.uuid4().hex
        now = _now().isoformat()
        self._conn.execute(
            "INSERT INTO subjects (id, kind, tags, time_confidence, settings, secret, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
            (sid, s.kind, json.dumps(s.tags), s.time_confidence, json.dumps(s.settings), self._seal(s), now, now),
        )
        self._conn.commit()
        return self.get(sid)

    def get(self, sid: str) -> Subject:
        row = self._conn.execute("SELECT * FROM subjects WHERE id = ?", (sid,)).fetchone()
        if row is None:
            raise KeyError(sid)
        return self._row_to_subject(row)

    def update(self, sid: str, s: SubjectIn) -> Subject:
        self.get(sid)
        self._conn.execute(
            "UPDATE subjects SET kind=?, tags=?, time_confidence=?, settings=?, secret=?, updated_at=? WHERE id=?",
            (s.kind, json.dumps(s.tags), s.time_confidence, json.dumps(s.settings), self._seal(s), _now().isoformat(), sid),
        )
        self._conn.commit()
        return self.get(sid)

    def delete(self, sid: str) -> None:
        """Soft delete: the row stays and can be restored."""
        self.get(sid)
        self._conn.execute("UPDATE subjects SET deleted_at=? WHERE id=?", (_now().isoformat(), sid))
        self._conn.commit()

    def restore(self, sid: str) -> Subject:
        self._conn.execute("UPDATE subjects SET deleted_at=NULL WHERE id=?", (sid,))
        self._conn.commit()
        return self.get(sid)

    def list(self, query: str | None = None, tag: str | None = None, include_deleted: bool = False) -> list[Subject]:
        sql = "SELECT * FROM subjects" + ("" if include_deleted else " WHERE deleted_at IS NULL") + " ORDER BY updated_at DESC"
        out = [self._row_to_subject(r) for r in self._conn.execute(sql)]
        if tag:
            out = [s for s in out if tag in s.tags]
        if query:
            q = query.casefold()
            out = [s for s in out if q in s.name.casefold() or q in s.place_name.casefold() or any(q in t.casefold() for t in s.tags)]
        return out

    def tags(self) -> list[str]:
        seen: set[str] = set()
        for r in self._conn.execute("SELECT tags FROM subjects WHERE deleted_at IS NULL"):
            seen.update(json.loads(r["tags"]))
        return sorted(seen)
