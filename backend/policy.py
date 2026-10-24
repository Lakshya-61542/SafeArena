"""Zone-to-zone access policy. Default stance: deny everything not explicitly allowed.

    Red  -> LLM   ALLOW        Blue -> LLM   ALLOW
    Red  -> Blue  DENY         Blue -> Red   DENY
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

ZONES = ("red", "blue", "llm")

DEFAULT_RULES: Mapping[tuple, bool] = {
    ("red", "llm"): True,
    ("blue", "llm"): True,
    ("red", "blue"): False,
    ("blue", "red"): False,
}

_DENY_REASONS = {
    ("red", "blue"): "Red Team cannot directly access Blue Team defensive state.",
    ("blue", "red"): "Blue Team cannot inspect unreleased Red Team attack payloads.",
}


def _name(zone: str) -> str:
    return "LLM" if zone == "llm" else zone.title()


@dataclass(frozen=True)
class Decision:
    allowed: bool
    source: str
    target: str
    reason: str
    rule: str  # explicit-allow | explicit-deny | default-deny

    @property
    def label(self) -> str:
        return "ALLOWED" if self.allowed else "BLOCKED"


def _norm(value: str) -> str:
    return str(value).strip().lower()


class PolicyEngine:
    def __init__(self, rules: Mapping[tuple, bool] | None = None, zones=ZONES):
        self.rules = dict(DEFAULT_RULES if rules is None else rules)
        self.zones = tuple(zones)

    def evaluate(self, source: str, target: str) -> Decision:
        s, t = _norm(source), _norm(target)
        verdict = self.rules.get((s, t))
        if verdict is True:
            return Decision(True, s, t, f"{_name(s)} is authorized to communicate with {_name(t)} through the gateway.", "explicit-allow")
        if verdict is False:
            reason = _DENY_REASONS.get((s, t), f"{_name(s)} -> {_name(t)} is explicitly denied by SafeArena policy.")
            return Decision(False, s, t, reason, "explicit-deny")
        return Decision(False, s, t, f"Direct {s} -> {t} communication is not permitted by SafeArena policy (default deny).", "default-deny")

    def matrix(self) -> dict:
        rows = []
        for s in self.zones:
            for t in self.zones:
                d = self.evaluate(s, t)
                rows.append({"source": s, "target": t, "action": "ALLOW" if d.allowed else "DENY", "rule": d.rule})
        return {"zones": list(self.zones), "default": "DENY", "rules": rows}


_DEFAULT = PolicyEngine()


def is_allowed(source: str, target: str) -> bool:
    return _DEFAULT.evaluate(source, target).allowed


def policy_reason(source: str, target: str) -> str:
    return _DEFAULT.evaluate(source, target).reason
