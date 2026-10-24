import json
import tempfile
import threading
import unittest
from pathlib import Path

from backend.audit import GENESIS, AuditChain, compute_hash, run_tamper_self_test


class AuditTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)
        self.chain = AuditChain(self.dir / "audit.jsonl")

    def fill(self, n=5):
        for i in range(n):
            self.chain.append("T", "red", f"msg {i}", {"i": i}, "S1")

    def lines(self):
        return self.chain.path.read_text(encoding="utf-8").splitlines()

    def write(self, lines):
        self.chain.path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def test_empty_log_is_valid(self):
        r = self.chain.verify()
        self.assertTrue(r["valid"]); self.assertEqual(r["count"], 0)

    def test_records_are_chained_with_sha256(self):
        self.fill(3)
        recs = self.chain.records()
        self.assertEqual(recs[0]["prev_hash"], GENESIS)
        self.assertEqual(recs[1]["prev_hash"], recs[0]["hash"])
        body = {k: v for k, v in recs[2].items() if k != "hash"}
        self.assertEqual(recs[2]["hash"], compute_hash(body))
        self.assertEqual(len(recs[2]["hash"]), 64)
        self.assertEqual([r["seq"] for r in recs], [0, 1, 2])

    def test_valid_chain_verifies_and_is_anchored(self):
        self.fill(5)
        r = self.chain.verify()
        self.assertTrue(r["valid"]); self.assertEqual(r["count"], 5); self.assertTrue(r["anchored"])
        self.assertEqual(r["head_hash"], self.chain.records()[-1]["hash"])

    def test_persistence_across_instances(self):
        self.fill(2)
        again = AuditChain(self.dir / "audit.jsonl")
        again.append("T", "blue", "third")
        self.assertEqual(AuditChain(self.dir / "audit.jsonl").verify()["count"], 3)
        self.assertTrue(AuditChain(self.dir / "audit.jsonl").verify()["valid"])

    def test_modified_record_detected_at_right_index(self):
        self.fill(5)
        ls = self.lines(); rec = json.loads(ls[2]); rec["message"] = "evil"; ls[2] = json.dumps(rec); self.write(ls)
        r = self.chain.verify()
        self.assertFalse(r["valid"]); self.assertEqual(r["failed_index"], 2); self.assertIn("modified", r["reason"])

    def test_modified_and_rehashed_record_breaks_next_link(self):
        self.fill(5)
        ls = self.lines(); rec = json.loads(ls[2]); rec["message"] = "evil"; rec.pop("hash"); rec["hash"] = compute_hash(rec)
        ls[2] = json.dumps(rec); self.write(ls)
        r = self.chain.verify()
        self.assertFalse(r["valid"]); self.assertEqual(r["failed_index"], 3)

    def test_deleted_middle_record_detected(self):
        self.fill(5); ls = self.lines(); del ls[2]; self.write(ls)
        r = self.chain.verify(); self.assertFalse(r["valid"]); self.assertEqual(r["failed_index"], 2)

    def test_reordered_records_detected(self):
        self.fill(5); ls = self.lines(); ls[1], ls[2] = ls[2], ls[1]; self.write(ls)
        self.assertFalse(self.chain.verify()["valid"])

    def test_tail_truncation_detected_via_checkpoint(self):
        self.fill(5); self.write(self.lines()[:-1])
        r = self.chain.verify(); self.assertFalse(r["valid"]); self.assertIn("deleted from the end", r["reason"])

    def test_full_deletion_detected(self):
        self.fill(3); self.chain.path.write_text("", encoding="utf-8")
        self.assertFalse(self.chain.verify()["valid"])

    def test_corrupt_json_detected(self):
        self.fill(3); ls = self.lines(); ls[1] = ls[1][:20]; self.write(ls)
        r = self.chain.verify(); self.assertFalse(r["valid"]); self.assertEqual(r["failed_index"], 1)

    def test_garbage_bytes_do_not_crash(self):
        self.fill(2)
        with self.chain.path.open("ab") as f: f.write(b"\xff\xfe\x00garbage\n")
        self.assertFalse(self.chain.verify()["valid"])

    def test_corrupt_checkpoint_fails_verification(self):
        self.fill(2); self.chain.checkpoint_path.write_text("{not json", encoding="utf-8")
        self.assertFalse(self.chain.verify()["valid"])

    def test_checkpoint_lagging_after_crash_is_tolerated(self):
        self.fill(3)
        cp = json.loads(self.chain.checkpoint_path.read_text()); recs = self.chain.records()
        self.chain.checkpoint_path.write_text(json.dumps({"count": 2, "head_hash": recs[1]["hash"]}))
        self.assertTrue(self.chain.verify()["valid"])

    def test_missing_checkpoint_valid_but_warns(self):
        self.fill(2); self.chain.checkpoint_path.unlink()
        r = self.chain.verify(); self.assertTrue(r["valid"]); self.assertFalse(r["anchored"]); self.assertIn("warning", r)

    def test_crlf_legacy_file_verifies(self):
        self.fill(3); data = self.chain.path.read_bytes().replace(b"\n", b"\r\n"); self.chain.path.write_bytes(data)
        self.assertTrue(self.chain.verify()["valid"])

    def test_unicode_and_lone_surrogate_payloads(self):
        self.chain.append("T", "red", "caf\u00e9 \u2603", {"x": "\ud800 lone"})
        self.assertTrue(self.chain.verify()["valid"])

    def test_concurrent_appends_keep_chain_valid(self):
        def work(n):
            for i in range(15): self.chain.append("T", "red", f"{n}-{i}")
        threads = [threading.Thread(target=work, args=(n,)) for n in range(6)]
        [t.start() for t in threads]; [t.join() for t in threads]
        r = self.chain.verify(); self.assertTrue(r["valid"]); self.assertEqual(r["count"], 90)

    def test_rotate_archives_and_links_new_chain(self):
        self.fill(4); head = self.chain.verify()["head_hash"]
        info = self.chain.rotate("test")
        archived = self.dir / "archive" / info["archived_file"]
        self.assertTrue(archived.exists())
        self.assertEqual(len([l for l in archived.read_text().splitlines() if l]), 4)
        first = self.chain.records()[0]
        self.assertEqual(first["event_type"], "AUDIT_ROTATED"); self.assertEqual(first["details"]["archived_head_hash"], head)
        self.assertTrue(self.chain.verify()["valid"])

    def test_rotate_empty_refused(self):
        with self.assertRaises(ValueError): self.chain.rotate()

    def test_tamper_self_test_detects_everything_and_leaves_live_log_alone(self):
        self.fill(6); before = self.chain.path.read_bytes()
        res = run_tamper_self_test(self.chain)
        self.assertTrue(res["baseline_valid"]); self.assertTrue(res["all_detected"], res)
        self.assertEqual(len(res["scenarios"]), 7)
        self.assertEqual(self.chain.path.read_bytes(), before); self.assertTrue(self.chain.verify()["valid"])
        self.assertTrue(res["source"].startswith("copy-of-live-log"))

    def test_tamper_self_test_uses_synthetic_chain_when_log_short(self):
        res = run_tamper_self_test(self.chain)
        self.assertIn("synthetic", res["source"]); self.assertTrue(res["all_detected"])
        self.assertEqual(self.chain.verify()["count"], 0)


if __name__ == "__main__":
    unittest.main()
