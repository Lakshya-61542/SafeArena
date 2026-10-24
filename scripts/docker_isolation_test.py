#!/usr/bin/env python3
"""Real cross-zone connectivity test for SafeArena's Docker deployment.

Run from the project root (needs Docker + Docker Compose v2; Python stdlib only):

    python scripts/docker_isolation_test.py            # build, start, test, stop
    python scripts/docker_isolation_test.py --keep     # leave the stack running afterwards

What it does
  1. Starts the stack and waits for health checks.
  2. For each pair it runs a TCP connection attempt *inside* the source container (docker compose exec).
     - must-be-blocked paths: Red<->Blue by DNS name AND by IP, zones -> LLM directly, Red/Blue -> internet
     - positive controls: Red/Blue -> gateway, gateway -> each service (proves the probe itself works)
  3. Inspects the Docker networks (internal flag, membership) and the published port binding.
  4. Calls the gateway API from the host: allowed and blocked flows plus /api/isolation/probe.
  5. Prints PASS/FAIL per check, writes reports/docker_isolation_report.json.

Exit codes: 0 all passed | 1 at least one check failed (isolation BREACH or gateway misbehaviour)
            2 inconclusive (a positive control failed, so blocked results prove nothing) | 3 Docker unavailable.
It never reports PASS for something it did not execute.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GATEWAY_URL = "http://127.0.0.1:8000"
PROBE_CODE = (
    "import socket,sys,json;h,p=sys.argv[1],int(sys.argv[2]);o={'resolved':None,'connected':False,'error':None}\n"
    "try:\n o['resolved']=socket.getaddrinfo(h,p,type=socket.SOCK_STREAM)[0][4][0]\n"
    "except OSError as e:\n o['error']='dns:'+type(e).__name__;print(json.dumps(o));sys.exit(0)\n"
    "try:\n socket.create_connection((h,p),timeout=3).close();o['connected']=True\n"
    "except OSError as e:\n o['error']='tcp:'+type(e).__name__\n"
    "print(json.dumps(o))"
)


def evaluate(checks: list) -> dict:
    """Pure verdict logic (unit-tested). Each check: {name, kind, passed, ...}.
    kind 'control' failing => INCONCLUSIVE; any other failing => FAIL."""
    failed_controls = [c for c in checks if c["kind"] == "control" and not c["passed"]]
    failed_other = [c for c in checks if c["kind"] != "control" and not c["passed"]]
    if failed_other:
        verdict, code = "FAIL", 1
    elif failed_controls:
        verdict, code = "INCONCLUSIVE", 2
    elif not checks:
        verdict, code = "INCONCLUSIVE", 2
    else:
        verdict, code = "PASS", 0
    return {"verdict": verdict, "exit_code": code, "passed": sum(c["passed"] for c in checks), "total": len(checks)}


class Runner:
    def __init__(self):
        self.checks: list = []

    def run(self, cmd, timeout=600, check=False):
        return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout, check=check)

    def compose(self, *args, **kw):
        return self.run(["docker", "compose", *args], **kw)

    def record(self, name, kind, passed, expected, actual, detail=""):
        self.checks.append({"name": name, "kind": kind, "passed": bool(passed), "expected": expected, "actual": actual, "detail": detail})
        print(f"  [{'PASS' if passed else 'FAIL'}] {name:<62} expected={expected:<11} actual={actual}")

    def probe(self, service, host, port):
        r = self.compose("exec", "-T", service, "python", "-c", PROBE_CODE, host, str(port), timeout=30)
        try:
            return json.loads(r.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            return {"resolved": None, "connected": False, "error": f"probe-exec-failed:{(r.stderr or '').strip()[:80]}"}

    def reach(self, label, service, host, port, expect_reachable, kind=None):
        res = self.probe(service, host, port)
        if (res["error"] or "").startswith("probe-exec-failed"):
            # The probe itself did not run: that is never a pass, even for "must be blocked".
            self.record(label, "control", False, "probe ran", res["error"])
            return
        self.record(label, kind or ("control" if expect_reachable else "isolation"), res["connected"] == expect_reachable,
                    "reachable" if expect_reachable else "unreachable",
                    "reachable" if res["connected"] else f"unreachable ({res['error']})")

    def container_ips(self, service):
        cid = self.compose("ps", "-q", service).stdout.strip()
        out = self.run(["docker", "inspect", "-f", "{{json .NetworkSettings.Networks}}", cid]).stdout
        nets = json.loads(out or "{}")
        return {name.split("_", 1)[-1]: v["IPAddress"] for name, v in nets.items() if v.get("IPAddress")}  # red_net -> ip

    def http(self, method, path, body=None):
        data = json.dumps(body if body is not None else {}).encode() if method == "POST" else None
        req = urllib.request.Request(GATEWAY_URL + path, data=data, method=method, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.status, json.loads(resp.read() or b"{}")
        except urllib.error.HTTPError as err:
            return err.code, json.loads(err.read() or b"{}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--keep", action="store_true", help="leave the containers running afterwards")
    ap.add_argument("--no-build", action="store_true", help="reuse existing images")
    args = ap.parse_args()

    if not shutil.which("docker"):
        print("NOT RUN: the 'docker' command was not found. Install Docker Desktop and retry. No results were produced.")
        return 3
    r = Runner()
    if r.run(["docker", "compose", "version"]).returncode != 0 or r.run(["docker", "info"]).returncode != 0:
        print("NOT RUN: Docker Compose v2 is missing or the Docker daemon is not running (start Docker Desktop).")
        return 3

    print("Starting SafeArena stack (this builds images the first time)...")
    up = r.compose("up", "-d", *([] if args.no_build else ["--build"]), "--wait", timeout=1800)
    if up.returncode != 0:
        print("FAILED to start the stack:\n" + (up.stderr or up.stdout)[-2000:])
        return 1
    try:
        print("\nTopology (docker network inspect)")
        for net in ("red_net", "blue_net", "llm_net", "frontend"):
            out = r.run(["docker", "network", "inspect", f"safearena_{net}", "--format", "{{.Internal}}"]).stdout.strip()
            want = "false" if net == "frontend" else "true"
            r.record(f"network {net} internal={want}", "isolation", out == want, f"internal={want}", f"internal={out or '?'}")
        port = r.compose("port", "gateway", "8000").stdout.strip()
        r.record("gateway port published on host loopback only", "isolation", port.startswith("127.0.0.1:"), "127.0.0.1:*", port or "none")

        red_ip, blue_ip = r.container_ips("red-service"), r.container_ips("blue-service")
        llm_ip, gw_ip = r.container_ips("llm-service"), r.container_ips("gateway")
        print(f"  addresses: red={red_ip} blue={blue_ip} llm={llm_ip} gateway={gw_ip}")
        r.record("red-service is attached only to red_net", "isolation", set(red_ip) == {"red_net"}, "{red_net}", str(set(red_ip)))
        r.record("blue-service is attached only to blue_net", "isolation", set(blue_ip) == {"blue_net"}, "{blue_net}", str(set(blue_ip)))
        r.record("llm-service is attached only to llm_net", "isolation", set(llm_ip) == {"llm_net"}, "{llm_net}", str(set(llm_ip)))

        print("\nPositive controls (these MUST be reachable, otherwise the blocked results prove nothing)")
        r.reach("red-service -> gateway:8000 (by name)", "red-service", "gateway", 8000, True)
        r.reach("blue-service -> gateway:8000 (by name)", "blue-service", "gateway", 8000, True)
        r.reach("gateway -> red-service:8101", "gateway", "red-service", 8101, True)
        r.reach("gateway -> blue-service:8102", "gateway", "blue-service", 8102, True)
        r.reach("gateway -> llm-service:8103", "gateway", "llm-service", 8103, True)

        print("\nCross-zone paths that MUST be blocked")
        r.reach("RED  -> BLUE  blue-service:8102 (by name)", "red-service", "blue-service", 8102, False)
        r.reach("BLUE -> RED   red-service:8101 (by name)", "blue-service", "red-service", 8101, False)
        if blue_ip.get("blue_net"):
            r.reach(f"RED  -> BLUE  {blue_ip['blue_net']}:8102 (by IP)", "red-service", blue_ip["blue_net"], 8102, False)
        if red_ip.get("red_net"):
            r.reach(f"BLUE -> RED   {red_ip['red_net']}:8101 (by IP)", "blue-service", red_ip["red_net"], 8101, False)
        r.reach("RED  -> LLM direct llm-service:8103 (must use gateway)", "red-service", "llm-service", 8103, False)
        r.reach("BLUE -> LLM direct llm-service:8103 (must use gateway)", "blue-service", "llm-service", 8103, False)
        r.reach("RED  -> internet 1.1.1.1:443 (internal network)", "red-service", "1.1.1.1", 443, False)
        r.reach("BLUE -> internet 1.1.1.1:443 (internal network)", "blue-service", "1.1.1.1", 443, False)
        r.reach("LLM  -> internet 1.1.1.1:443 (internal network)", "llm-service", "1.1.1.1", 443, False)

        print("\nGateway behaviour over the real network path")
        flows = [("red", "llm", 200, "ALLOWED"), ("blue", "llm", 200, "ALLOWED"), ("red", "blue", 403, "BLOCKED"), ("blue", "red", 403, "BLOCKED")]
        for src, dst, code, decision in flows:
            status, body = r.http("POST", "/api/gateway", {"source": src, "target": dst, "payload": "isolation test"})
            r.record(f"gateway {src}->{dst}", "gateway", status == code and body.get("decision") == decision,
                     f"{code} {decision}", f"{status} {body.get('decision')}")
        status, body = r.http("POST", "/api/isolation/probe")
        r.record("gateway-orchestrated probe verdict (containers' own view)", "isolation", status == 200 and body.get("verdict") == "ISOLATED",
                 "ISOLATED", f"{status} {body.get('verdict')}")
        status, body = r.http("POST", "/api/audit/verify")
        r.record("audit chain verifies after the run", "gateway", status == 200 and body.get("valid") is True, "valid", f"valid={body.get('valid')} count={body.get('count')}")
    finally:
        if not args.keep:
            r.compose("down", timeout=300)

    summary = evaluate(r.checks)
    report = {"generated": datetime.now(timezone.utc).isoformat(), "summary": summary, "checks": r.checks}
    out = ROOT / "reports"; out.mkdir(exist_ok=True)
    (out / "docker_isolation_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nRESULT: {summary['verdict']}  ({summary['passed']}/{summary['total']} checks passed)")
    if summary["verdict"] == "INCONCLUSIVE":
        print("A positive control failed, so 'blocked' results cannot be trusted. Check `docker compose logs`.")
    print(f"Report: {out / 'docker_isolation_report.json'}")
    return summary["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
