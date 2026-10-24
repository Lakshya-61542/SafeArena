import tempfile
import sqlite3
import unittest
from pathlib import Path
from unittest import mock

from backend.events import EventStore


class EventTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(); self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name) / "e.db"
        self.s = EventStore(self.path)
        self.s.add(event_type="ACCESS_ALLOWED", severity="info", message="red to llm", source="red", target="llm", decision="ALLOWED", session_id="A")
        self.s.add(event_type="POLICY_VIOLATION", severity="high", message="red to blue blocked", source="red", target="blue", decision="BLOCKED", session_id="A", audit_hash="abc")
        self.s.add(event_type="POLICY_VIOLATION", severity="high", message="blue to red blocked", source="blue", target="red", decision="BLOCKED", session_id="B")
        self.s.add(event_type="SESSION_START", severity="info", message="100% done_ok", session_id="B")

    def test_add_returns_row_and_persists(self):
        self.assertEqual(self.s.count(), 4)
        self.assertEqual(EventStore(self.path).count(), 4)
        row = self.s.query(limit=1)[0]
        self.assertEqual(row["event_type"], "SESSION_START"); self.assertIn("timestamp", row)

    def test_newest_first(self):
        ids = [e["id"] for e in self.s.query()]
        self.assertEqual(ids, sorted(ids, reverse=True))

    def test_filters(self):
        self.assertEqual(len(self.s.query(severity="high")), 2)
        self.assertEqual(len(self.s.query(severity="high,info")), 4)
        self.assertEqual(len(self.s.query(decision="blocked")), 2)
        self.assertEqual(len(self.s.query(source="red")), 2)
        self.assertEqual(len(self.s.query(target="blue")), 1)
        self.assertEqual(len(self.s.query(session_id="A")), 2)
        self.assertEqual(len(self.s.query(event_type="POLICY_VIOLATION", session_id="B")), 1)
        self.assertEqual(self.s.query(session_id="A", severity="high")[0]["audit_hash"], "abc")

    def test_text_search_and_like_escaping(self):
        self.assertEqual(len(self.s.query(q="blocked")), 2)
        self.assertEqual(len(self.s.query(q="100%")), 1)
        self.assertEqual(len(self.s.query(q="%")), 1)       # literal percent, not wildcard
        self.assertEqual(len(self.s.query(q="done_ok")), 1)
        self.assertEqual(len(self.s.query(q="d_ne")), 0)    # underscore is literal

    def test_sql_injection_is_inert(self):
        self.assertEqual(self.s.query(q="'; DROP TABLE events; --"), [])
        self.assertEqual(self.s.query(source="red' OR '1'='1"), [])
        self.assertEqual(self.s.count(), 4)

    def test_since_id_and_limit(self):
        first = self.s.query()[-1]["id"]
        self.assertEqual(len(self.s.query(since_id=first)), 3)
        self.assertEqual(len(self.s.query(limit=2)), 2)
        self.assertEqual(len(self.s.query(limit=-5)), 1)

    def test_validation(self):
        with self.assertRaises(ValueError): self.s.query(severity="nope")
        with self.assertRaises(ValueError): self.s.query(decision="maybe")
        with self.assertRaises(ValueError): self.s.add(event_type="X", severity="bogus", message="m")

    def test_every_connection_is_closed(self):
        """Regression: leaked connections keep events.db locked on Windows (tempdir cleanup fails)."""
        opened = []
        real = sqlite3.connect
        def tracking(*a, **k):
            c = real(*a, **k); opened.append(c); return c
        with mock.patch("backend.events.sqlite3.connect", tracking):
            s = EventStore(Path(self._tmp.name) / "t.db")
            s.add(event_type="X", severity="info", message="m"); s.query(); s.count(); s.stats()
            with self.assertRaises(ValueError): s.query(severity="bad")
        self.assertGreaterEqual(len(opened), 5)
        for c in opened:
            with self.assertRaises(sqlite3.ProgrammingError): c.execute("SELECT 1")  # raises only if closed
        (Path(self._tmp.name) / "t.db").unlink()  # would fail on Windows if still open

    def test_stats(self):
        st = self.s.stats()
        self.assertEqual(st["total"], 4); self.assertEqual(st["by_decision"]["BLOCKED"], 2); self.assertEqual(st["by_severity"]["high"], 2)
        self.assertEqual(self.s.stats(session_id="A")["total"], 2)


if __name__ == "__main__":
    unittest.main()
