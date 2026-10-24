"""Persistent, tamper-evident audit log: an append-only JSONL file where every record
contains the SHA-256 hash of the previous record.

Record layout (``hash`` covers every other field):
    seq, timestamp, event_type, actor, message, details, session_id, prev_hash, hash

What the chain detects: modified records, deleted/inserted/reordered records, corrupt lines.
A small *checkpoint* file (``<log>_head.json``) stores the latest count + head hash so that
deleting records from the END of the log is also detected.

What it cannot detect (documented limitation): someone with write access to the data
directory who rewrites the log AND the checkpoint consistently. Protecting against that needs
an external anchor (HMAC key held elsewhere, WORM storage, or periodically publishing the head hash).
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import shutil
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

GENESIS = "GENESIS"
_LOCKS: dict = {}
_LOCKS_GUARD = threading.Lock()


def _lock_for(path: Path) -> threading.RLock:
    key = str(path.resolve())
    with _LOCKS_GUARD:
        return _LOCKS.setdefault(key, threading.RLock())


def _canonical(payload: dict) -> str:
    # ensure_ascii=True keeps hashing safe for any text (including lone surrogates).
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_hash(body: dict) -> str:
    return hashlib.sha256(_canonical(body).encode("ascii")).hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AuditChain:
    def __init__(self, path, checkpoint_path=None):
        self.path = Path(path)
        self.checkpoint_path = Path(checkpoint_path) if checkpoint_path else self.path.with_name(self.path.stem + "_head.json")
        self._lock = _lock_for(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("", encoding="utf-8")

    # ------------------------------------------------------------------ reading
    def _iter_lines(self) -> Iterator[str]:
        with self.path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
            for line in handle:
                stripped = line.strip()
                if stripped:
                    yield stripped

    def _tail(self):
        """Return (record_count, last_record_or_None, last_line_was_corrupt)."""
        count, last_raw = 0, None
        for raw in self._iter_lines():
            count += 1
            last_raw = raw
        if last_raw is None:
            return 0, None, False
        try:
            record = json.loads(last_raw)
            if isinstance(record, dict) and isinstance(record.get("hash"), str):
                return count, record, False
        except ValueError:
            pass
        return count, None, True

    def _read_checkpoint(self):
        """Return (checkpoint_dict | None, error_message | None)."""
        if not self.checkpoint_path.exists():
            return None, None
        try:
            data = json.loads(self.checkpoint_path.read_text(encoding="utf-8"))
            if not (isinstance(data, dict) and isinstance(data.get("count"), int) and data["count"] >= 0
                    and isinstance(data.get("head_hash"), str)):
                return None, "Checkpoint file has an invalid structure"
            return data, None
        except (ValueError, OSError):
            return None, "Checkpoint file is unreadable"

    def _write_checkpoint(self, count: int, head_hash: str) -> None:
        tmp = self.checkpoint_path.with_name(self.checkpoint_path.name + ".tmp")
        tmp.write_text(json.dumps({"count": count, "head_hash": head_hash, "updated": _utc_now()}), encoding="utf-8")
        os.replace(tmp, self.checkpoint_path)

    # ------------------------------------------------------------------ writing
    def append(self, event_type: str, actor: str, message: str, details: dict | None = None,
               session_id: str | None = None) -> dict:
        with self._lock:
            count, last, corrupt_tail = self._tail()
            if last is not None:
                prev_hash = last["hash"]
                seq = last["seq"] + 1 if isinstance(last.get("seq"), int) else count
            elif corrupt_tail:
                prev_hash, seq = "CORRUPT-TAIL", count  # verify() will flag the damaged line
            else:
                prev_hash, seq = GENESIS, 0
            record: dict[str, Any] = {
                "seq": seq,
                "timestamp": _utc_now(),
                "event_type": event_type,
                "actor": actor,
                "message": message,
                "details": details or {},
                "session_id": session_id,
                "prev_hash": prev_hash,
            }
            record["hash"] = compute_hash(record)
            line = json.dumps(record, ensure_ascii=True) + "\n"
            with self.path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(line)
                handle.flush()
                os.fsync(handle.fileno())
            self._write_checkpoint(count + 1, record["hash"])
            return record

    # ------------------------------------------------------------- verification
    def verify(self) -> dict:
        with self._lock:
            checkpoint, cp_error = self._read_checkpoint()
            cp_hash_seen = None
            previous, total = GENESIS, 0
            failure = None
            for index, raw in enumerate(self._iter_lines()):
                total = index + 1
                if failure is not None:
                    continue  # keep counting lines
                failure = self._check_line(index, raw, previous)
                if failure is None:
                    previous = json.loads(raw)["hash"]
                    if checkpoint is not None and index == checkpoint["count"] - 1:
                        cp_hash_seen = previous
            if failure is not None:
                return {"valid": False, "count": total, "failed_index": failure[0], "reason": failure[1], "head_hash": None, "anchored": checkpoint is not None}
            if cp_error:
                return {"valid": False, "count": total, "failed_index": None, "reason": cp_error, "head_hash": None, "anchored": False}
            if checkpoint is not None:
                if checkpoint["count"] > total:
                    return {"valid": False, "count": total, "failed_index": total,
                            "reason": f"Log has {total} records but the checkpoint recorded {checkpoint['count']} (records were deleted from the end)",
                            "head_hash": None, "anchored": True}
                if checkpoint["count"] > 0 and cp_hash_seen != checkpoint["head_hash"]:
                    return {"valid": False, "count": total, "failed_index": checkpoint["count"] - 1,
                            "reason": "Checkpoint head hash does not match the chain", "head_hash": None, "anchored": True}
            elif total > 0:
                # Chain is internally consistent but nothing anchors its tail.
                return {"valid": True, "count": total, "head_hash": previous if total else None, "anchored": False,
                        "warning": "No checkpoint file: tail deletion cannot be detected"}
            return {"valid": True, "count": total, "head_hash": previous if total else None, "anchored": checkpoint is not None}

    @staticmethod
    def _check_line(index: int, raw: str, previous: str):
        try:
            record = json.loads(raw)
        except ValueError:
            return index, "Invalid JSON record"
        if not isinstance(record, dict):
            return index, "Record is not a JSON object"
        supplied = record.get("hash")
        if not isinstance(supplied, str):
            return index, "Record has no hash"
        body = {k: v for k, v in record.items() if k != "hash"}
        if body.get("prev_hash") != previous:
            return index, "Previous hash mismatch (a record was removed, inserted or reordered)"
        if "seq" in body and body["seq"] != index:
            return index, "Sequence number mismatch"
        try:
            computed = compute_hash(body)
        except (TypeError, ValueError):
            return index, "Record cannot be canonicalised"
        if not hmac.compare_digest(supplied, computed):
            return index, "Record hash mismatch (record content was modified)"
        return None

    # ------------------------------------------------------------------ queries
    def records(self) -> list:
        out = []
        for raw in self._iter_lines():
            try:
                out.append(json.loads(raw))
            except ValueError:
                out.append({"_corrupt_line": raw[:200]})
        return out

    def recent(self, limit: int = 40) -> list:
        limit = max(1, min(int(limit), 500))
        return list(reversed(self.records()[-limit:]))

    # ----------------------------------------------------------------- rotation
    def rotate(self, reason: str = "manual", session_id: str | None = None) -> dict:
        """Archive the current log (never delete it) and start a new chain that references
        the archived chain's head hash inside its first, hashed record."""
        with self._lock:
            verification = self.verify()
            if verification["count"] == 0:
                raise ValueError("Audit log is empty; nothing to archive")
            archive_dir = self.path.parent / "archive"
            archive_dir.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            archived = archive_dir / f"{self.path.stem}.{stamp}.{verification['count']}records.jsonl"
            shutil.move(str(self.path), archived)
            if self.checkpoint_path.exists():
                shutil.move(str(self.checkpoint_path), archived.with_name(archived.stem + "_head.json"))
            self.path.write_text("", encoding="utf-8")
            first = self.append(
                "AUDIT_ROTATED", "system", "Audit chain archived; new chain started",
                {"reason": reason, "archived_file": archived.name, "archived_count": verification["count"],
                 "archived_head_hash": verification.get("head_hash"), "archived_chain_valid": verification["valid"]},
                session_id=session_id,
            )
            return {"archived_file": archived.name, "archived_count": verification["count"],
                    "archived_chain_valid": verification["valid"], "new_chain_first_hash": first["hash"]}

    def reset(self) -> None:  # kept for backwards compatibility; archives instead of deleting
        if self.verify()["count"]:
            self.rotate("reset")


# ---------------------------------------------------------------- tamper self-test
def run_tamper_self_test(chain: AuditChain) -> dict:
    """Prove that verification really detects tampering by corrupting *copies* of the log
    in a temporary directory and running the real verifier on each. The live log is never touched."""
    with tempfile.TemporaryDirectory(prefix="safearena-tamper-") as tmp:
        tmp_dir = Path(tmp)
        source = "copy-of-live-log"
        base = tmp_dir / "base.jsonl"
        live = chain.verify()
        if live["valid"] and live["count"] >= 4:
            shutil.copyfile(chain.path, base)
            if chain.checkpoint_path.exists():
                shutil.copyfile(chain.checkpoint_path, tmp_dir / "base_head.json")
        else:
            source = "synthetic-chain (live log is too short or already invalid)"
            synth = AuditChain(base)
            for i in range(5):
                synth.append("SELF_TEST", "system", f"synthetic record {i}", {"i": i})
        baseline = AuditChain(base).verify()
        lines = [ln for ln in base.read_text(encoding="utf-8").splitlines() if ln.strip()]
        mid = len(lines) // 2

        def scenario(name: str, description: str, mutate) -> dict:
            work = tmp_dir / f"{name}.jsonl"
            shutil.copyfile(base, work)
            cp = tmp_dir / "base_head.json"
            if cp.exists():
                shutil.copyfile(cp, tmp_dir / f"{name}_head.json")
            new_lines = mutate(list(lines))
            work.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
            result = AuditChain(work).verify()
            return {"scenario": name, "description": description, "detected": not result["valid"],
                    "failed_index": result.get("failed_index"), "reason": result.get("reason")}

        def edit_message(ls):
            rec = json.loads(ls[mid]); rec["message"] = "TAMPERED: " + str(rec.get("message")); ls[mid] = json.dumps(rec); return ls

        def edit_and_rehash(ls):
            rec = json.loads(ls[mid]); rec["message"] = "TAMPERED"; rec.pop("hash", None)
            rec["hash"] = compute_hash(rec); ls[mid] = json.dumps(rec); return ls

        def delete_record(ls):
            del ls[mid]; return ls

        def reorder(ls):
            ls[mid], ls[mid + 1] = ls[mid + 1], ls[mid]; return ls

        def insert_forged(ls):
            prev = json.loads(ls[mid - 1])
            forged = {"seq": mid, "timestamp": _utc_now(), "event_type": "ACCESS_ALLOWED", "actor": "red",
                      "message": "forged", "details": {}, "session_id": None, "prev_hash": prev["hash"]}
            forged["hash"] = compute_hash(forged); ls.insert(mid, json.dumps(forged)); return ls

        def truncate_tail(ls):
            return ls[:-1]

        def corrupt_line(ls):
            ls[mid] = ls[mid][: len(ls[mid]) // 2]; return ls

        scenarios = [
            scenario("modify_record", "Change the text of one record", edit_message),
            scenario("modify_and_rehash", "Change a record and recompute its own hash", edit_and_rehash),
            scenario("delete_record", "Delete one record from the middle", delete_record),
            scenario("reorder_records", "Swap two adjacent records", reorder),
            scenario("insert_forged_record", "Insert a forged record with a valid self-hash", insert_forged),
            scenario("truncate_tail", "Delete the newest record (caught via checkpoint)", truncate_tail),
            scenario("corrupt_line", "Damage a JSON line", corrupt_line),
        ]
        return {
            "source": source,
            "baseline_valid": baseline["valid"],
            "records_in_copy": len(lines),
            "scenarios": scenarios,
            "all_detected": baseline["valid"] and all(s["detected"] for s in scenarios),
            "live_log_modified": False,
        }
