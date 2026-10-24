"""The Security Gateway: the only place where cross-zone requests are decided.

For every request it (1) evaluates policy, (2) either blocks, or forwards to the Client LLM,
(3) writes a hash-chained audit record and (4) emits a security event that points at that record.
Blocked payloads are never forwarded anywhere.
"""
from __future__ import annotations

import hashlib
import re
import threading
import uuid
from datetime import datetime, timezone

from backend.llm import detect_injection

_CONTROL = re.compile(r"[\x00-\x1f\x7f]")


def preview(text: str, limit: int = 100) -> str:
    return _CONTROL.sub(" ", text)[:limit]


class SessionManager:
    def __init__(self):
        self._lock = threading.Lock()
        self.session_id = None
        self.started = None

    def start(self) -> dict:
        with self._lock:
            self.session_id = f"SA-{uuid.uuid4().hex[:8].upper()}"
            self.started = datetime.now(timezone.utc).isoformat()
            return {"session_id": self.session_id, "session_started": self.started}

    def snapshot(self) -> dict:
        with self._lock:
            return {"session_id": self.session_id, "session_started": self.started}


class Gateway:
    def __init__(self, *, policy, audit, events, llm, sessions, mode: str):
        self.policy, self.audit, self.events, self.llm, self.sessions, self.mode = policy, audit, events, llm, sessions, mode

    def handle(self, source: str, target: str, payload: str):
        """Return (http_status, body). 200 = allowed, 403 = blocked by policy."""
        decision = self.policy.evaluate(source, target)
        session_id = self.sessions.snapshot()["session_id"]
        request_id = uuid.uuid4().hex[:12]
        detections = detect_injection(payload) if payload else []
        base_details = {
            "request_id": request_id, "source": decision.source, "target": decision.target, "rule": decision.rule,
            "payload_chars": len(payload), "payload_sha256": hashlib.sha256(payload.encode("utf-8", "replace")).hexdigest(),
            "payload_preview": preview(payload), "detections": detections,
        }

        if not decision.allowed:
            rec = self.audit.append("ACCESS_BLOCKED", decision.source, decision.reason, base_details, session_id)
            event = self.events.add(
                event_type="POLICY_VIOLATION", severity="high", source=decision.source, target=decision.target,
                decision="BLOCKED", session_id=session_id, audit_hash=rec["hash"],
                message=f"Unauthorized {decision.source.upper()} -> {decision.target.upper()} access blocked",
                details={"reason": decision.reason, "rule": decision.rule, "request_id": request_id, "detections": detections},
            )
            return 403, {"decision": "BLOCKED", "reason": decision.reason, "rule": decision.rule, "source": decision.source,
                         "target": decision.target, "request_id": request_id, "session_id": session_id,
                         "security_event": event, "audit_hash": rec["hash"], "audit_seq": rec["seq"]}

        llm_result = None
        if decision.target == "llm":
            llm_result = self.llm.infer(payload, decision.source)
        details = dict(base_details)
        if llm_result is not None:
            details["llm"] = {k: llm_result.get(k) for k in ("provider", "model", "safety", "ok", "error", "latency_ms")}
        rec = self.audit.append("ACCESS_ALLOWED", decision.source, decision.reason, details, session_id)
        common = dict(source=decision.source, target=decision.target, session_id=session_id, audit_hash=rec["hash"])
        event = self.events.add(
            event_type="ACCESS_ALLOWED", severity="info", decision="ALLOWED",
            message=f"{decision.source.upper()} -> {decision.target.upper()} request allowed", details={"request_id": request_id}, **common)
        if detections or (llm_result and llm_result.get("safety") in ("refused", "contained")):
            self.events.add(
                event_type="PROMPT_INJECTION_DETECTED", severity="medium", decision="ALLOWED",
                message=f"Adversarial prompt pattern from {decision.source.upper()} reached the LLM",
                details={"detections": detections, "llm_safety": (llm_result or {}).get("safety"), "request_id": request_id}, **common)
        if llm_result and llm_result.get("safety") == "leaked":
            self.events.add(event_type="LLM_PROTECTED_MARKER_LEAKED", severity="critical", decision="ALLOWED",
                            message="Client LLM leaked its protected marker", details={"request_id": request_id}, **common)
        if llm_result and not llm_result.get("ok"):
            self.events.add(event_type="LLM_ERROR", severity="medium", decision="ALLOWED",
                            message="Client LLM backend failed", details={"error": llm_result.get("error"), "request_id": request_id}, **common)
        body = {"decision": "ALLOWED", "reason": decision.reason, "rule": decision.rule, "source": decision.source,
                "target": decision.target, "request_id": request_id, "session_id": session_id, "detections": detections,
                "llm_result": llm_result, "security_event": event, "audit_hash": rec["hash"], "audit_seq": rec["seq"]}
        return 200, body
