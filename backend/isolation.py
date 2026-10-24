"""Docker network isolation probe.

In Docker mode the Red and Blue zone containers each try to open TCP connections to targets that
are *supposed to be unreachable* (the other zone, the LLM container directly) and to targets that
*must* be reachable (the gateway). The controls matter: if a control fails the probe could not
have shown anything, so the verdict is INCONCLUSIVE rather than "isolated".

In local mode there are no separate networks, so nothing is probed and no result is claimed.
"""
from __future__ import annotations

import socket
from urllib.parse import urlsplit

import requests

BLOCKED, CONTROL = "must_be_blocked", "control"


def tcp_probe(host: str, port: int, timeout: float = 2.0) -> dict:
    """Resolve and connect. Returns what actually happened; never raises."""
    out = {"resolved": None, "connected": False, "error": None}
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        out["resolved"] = infos[0][4][0]
    except OSError as exc:
        out["error"] = f"dns:{type(exc).__name__}"
        return out
    try:
        with socket.create_connection((host, port), timeout=timeout):
            out["connected"] = True
    except OSError as exc:
        out["error"] = f"tcp:{type(exc).__name__}"
    return out


def evaluate_checks(checks: list) -> str:
    """checks: dicts with role + connected. Returns ISOLATED | BREACH | INCONCLUSIVE."""
    controls = [c for c in checks if c["role"] == CONTROL]
    blocked = [c for c in checks if c["role"] == BLOCKED]
    if any(c["connected"] for c in blocked):
        return "BREACH"
    if not controls or not all(c["connected"] for c in controls) or not blocked:
        return "INCONCLUSIVE"
    return "ISOLATED"


def _hostport(url: str):
    parts = urlsplit(url)
    return parts.hostname, parts.port


def run_probe(config, http=requests, tcp=tcp_probe) -> dict:
    if config.mode != "docker":
        return {"supported": False, "mode": config.mode, "verdict": "NOT_APPLICABLE",
                "message": "Local mode has no separate networks, so there is nothing to probe. Policy enforcement is "
                           "demonstrated; network isolation is only verified in Docker mode."}
    zones, flat = {}, []
    for zone, url in (("red", config.red_service_url), ("blue", config.blue_service_url)):
        try:
            resp = http.get(f"{url}/probe", timeout=12)
            resp.raise_for_status()
            rows = resp.json()["results"]
            checks = [{"zone": zone, "target": str(r["target"]), "role": r["role"], "resolved": r.get("resolved"),
                       "connected": bool(r["connected"]), "error": r.get("error")} for r in rows if r.get("role") in (BLOCKED, CONTROL)]
        except Exception as exc:
            zones[zone] = {"verdict": "INCONCLUSIVE", "error": f"{zone}-service probe failed: {type(exc).__name__}", "checks": []}
            continue
        for c in checks:
            c["expected"] = "unreachable" if c["role"] == BLOCKED else "reachable"
            c["ok"] = c["connected"] == (c["role"] == CONTROL)
        zones[zone] = {"verdict": evaluate_checks(checks), "checks": checks}
        flat += checks

    gateway_checks = []
    for name, url in (("red-service", config.red_service_url), ("blue-service", config.blue_service_url), ("llm-service", config.llm_service_url)):
        host, port = _hostport(url)
        r = tcp(host, port)
        gateway_checks.append({"zone": "gateway", "target": f"{host}:{port}", "role": CONTROL, "expected": "reachable",
                               "resolved": r["resolved"], "connected": r["connected"], "error": r["error"], "ok": r["connected"]})
    flat += gateway_checks

    verdicts = [z["verdict"] for z in zones.values()]
    if "BREACH" in verdicts:
        overall = "BREACH"
    elif any(v != "ISOLATED" for v in verdicts) or not all(c["connected"] for c in gateway_checks):
        overall = "INCONCLUSIVE"
    else:
        overall = "ISOLATED"
    return {"supported": True, "mode": "docker", "verdict": overall, "zones": zones, "gateway_controls": gateway_checks, "checks": flat}
