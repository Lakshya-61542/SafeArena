"""Persistent security-event log (SQLite) with server-side filtering.

All SQL uses bound parameters; user-supplied search text is escaped for LIKE.
Events are operational telemetry for the dashboard; the *evidence* lives in the audit chain
(each event stores the hash of the audit record that proves it).
"""
from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

SEVERITIES = ("info", "low", "medium", "high", "critical")
DECISIONS = ("ALLOWED", "BLOCKED")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    session_id TEXT,
    event_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    source TEXT,
    target TEXT,
    decision TEXT,
    message TEXT NOT NULL,
    details TEXT NOT NULL DEFAULT '{}',
    audit_hash TEXT
);
CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id);
CREATE INDEX IF NOT EXISTS idx_events_severity ON events(severity);
"""


def _escape_like(text: str) -> str:
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class EventStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._write_lock = threading.Lock()
        with self._connect() as conn:
            conn.executescript(_SCHEMA)

    @contextmanager
    def _connect(self):
        """Commit on success, roll back on error, and ALWAYS close.
        (sqlite3's own `with conn:` does not close; on Windows that keeps events.db locked.)"""
        conn = sqlite3.connect(str(self.path), timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    @staticmethod
    def _row(row: sqlite3.Row) -> dict:
        data = dict(row)
        try:
            data["details"] = json.loads(data.get("details") or "{}")
        except ValueError:
            data["details"] = {}
        data["timestamp"] = data.pop("ts")
        return data

    def add(self, *, event_type: str, severity: str, message: str, source=None, target=None, decision=None,
            session_id=None, details=None, audit_hash=None) -> dict:
        if severity not in SEVERITIES:
            raise ValueError(f"severity must be one of {SEVERITIES}")
        ts = datetime.now(timezone.utc).isoformat()
        with self._write_lock, self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO events (ts, session_id, event_type, severity, source, target, decision, message, details, audit_hash)"
                " VALUES (?,?,?,?,?,?,?,?,?,?)",
                (ts, session_id, event_type, severity, source, target, decision, message,
                 json.dumps(details or {}, ensure_ascii=True), audit_hash),
            )
            row = conn.execute("SELECT * FROM events WHERE id = ?", (cur.lastrowid,)).fetchone()
        return self._row(row)

    @staticmethod
    def _where(severity=None, event_type=None, source=None, target=None, decision=None,
               session_id=None, q=None, since_id=None):
        clauses, params = [], []
        if severity:
            sevs = [s.strip().lower() for s in (severity.split(",") if isinstance(severity, str) else severity) if s.strip()]
            bad = [s for s in sevs if s not in SEVERITIES]
            if bad:
                raise ValueError(f"unknown severity: {bad[0]}")
            clauses.append("severity IN (%s)" % ",".join("?" * len(sevs)))
            params += sevs
        if decision:
            if decision.upper() not in DECISIONS:
                raise ValueError(f"decision must be one of {DECISIONS}")
            clauses.append("decision = ?"); params.append(decision.upper())
        for column, value in (("event_type", event_type), ("source", source), ("target", target), ("session_id", session_id)):
            if value:
                clauses.append(f"{column} = ?"); params.append(value)
        if q:
            like = f"%{_escape_like(q.strip()[:200])}%"
            clauses.append("(message LIKE ? ESCAPE '\\' OR event_type LIKE ? ESCAPE '\\' OR details LIKE ? ESCAPE '\\'"
                           " OR source LIKE ? ESCAPE '\\' OR target LIKE ? ESCAPE '\\')")
            params += [like] * 5
        if since_id is not None:
            clauses.append("id > ?"); params.append(int(since_id))
        return (" WHERE " + " AND ".join(clauses)) if clauses else "", params

    def query(self, *, limit: int = 100, **filters) -> list:
        limit = max(1, min(int(limit), 500))
        where, params = self._where(**filters)
        with self._connect() as conn:
            rows = conn.execute(f"SELECT * FROM events{where} ORDER BY id DESC LIMIT ?", (*params, limit)).fetchall()
        return [self._row(r) for r in rows]

    def count(self, **filters) -> int:
        where, params = self._where(**filters)
        with self._connect() as conn:
            return conn.execute(f"SELECT COUNT(*) FROM events{where}", params).fetchone()[0]

    def stats(self, session_id=None) -> dict:
        where, params = self._where(session_id=session_id)
        with self._connect() as conn:
            def group(col):
                rows = conn.execute(f"SELECT {col} AS k, COUNT(*) AS n FROM events{where} GROUP BY {col}", params).fetchall()
                return {r["k"]: r["n"] for r in rows if r["k"] is not None}
            total = conn.execute(f"SELECT COUNT(*) FROM events{where}", params).fetchone()[0]
            return {"total": total, "by_severity": group("severity"), "by_decision": group("decision"), "by_type": group("event_type")}
