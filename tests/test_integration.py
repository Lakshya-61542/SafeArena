"""Real sockets, real HTTP. NOTE: these run on one machine, so they test the Docker-mode CODE PATHS
(gateway -> llm-service over HTTP, probe orchestration) but NOT network isolation itself."""
import importlib.util
import json
import sys
import tempfile
import threading
import unittest
import urllib.request
from pathlib import Path

try:
    import yaml
except ImportError:  # optional dev dependency
    yaml = None
from werkzeug.serving import make_server

from backend.app import create_app
from backend.config import Config
from backend.isolation import evaluate_checks, run_probe

ROOT = Path(__file__).resolve().parent.parent


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    mod = importlib.util.module_from_spec(spec); sys.modules[name] = mod; spec.loader.exec_module(mod)
    return mod


class Server:
    def __init__(self, app):
        self.srv = make_server("127.0.0.1", 0, app, threaded=True)
        self.port = self.srv.server_port
        self.thread = threading.Thread(target=self.srv.serve_forever, daemon=True); self.thread.start()
        self.url = f"http://127.0.0.1:{self.port}"
    def stop(self):
        self.srv.shutdown(); self.thread.join(2)


def fetch(url, method="GET", body=None):
    req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body is not None else None, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r: return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        try: return e.code, json.loads(e.read())
        finally: e.close()


class LocalServerTests(unittest.TestCase):
    def test_full_flow_over_real_http(self):
        with tempfile.TemporaryDirectory() as tmp:
            srv = Server(create_app(Config(data_dir=Path(tmp)))); self.addCleanup(srv.stop)
            self.assertEqual(fetch(srv.url + "/api/health")[0], 200)
            self.assertEqual(fetch(srv.url + "/api/gateway", "POST", {"source": "red", "target": "llm", "payload": "hi"})[0], 200)
            self.assertEqual(fetch(srv.url + "/api/gateway", "POST", {"source": "red", "target": "blue", "payload": "hi"})[0], 403)
            self.assertTrue(fetch(srv.url + "/api/audit/verify")[1]["valid"])
            with urllib.request.urlopen(srv.url + "/") as r: self.assertIn(b"Adversarial AI Testing Console", r.read())


class DockerModeCodePathTests(unittest.TestCase):
    """Zone services run as real HTTP servers on ephemeral ports; the gateway is in docker mode."""
    def setUp(self):
        self.llm = Server(load_module("llm_service", "services/llm_service.py").app)
        self.red = Server(load_module("red_service", "services/red_service.py").app)
        self.blue = Server(load_module("blue_service", "services/blue_service.py").app)
        for s in (self.llm, self.red, self.blue): self.addCleanup(s.stop)
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.cfg = Config(mode="docker", data_dir=Path(self.tmp.name), llm_service_url=self.llm.url, red_service_url=self.red.url, blue_service_url=self.blue.url)

    def test_gateway_reaches_llm_service_over_http(self):
        c = create_app(self.cfg).test_client()
        r = c.post("/api/gateway", json={"source": "blue", "target": "llm", "payload": "hello"})
        self.assertEqual(r.status_code, 200)
        self.assertIn("Test prompt received safely from blue", r.get_json()["llm_result"]["response"])
        self.assertIn("llm-service", c.get("/api/status").get_json()["llm"]["transport"])
        self.assertEqual(c.get("/api/status").get_json()["mode"], "docker")

    def test_llm_service_down_is_reported_not_faked(self):
        self.llm.stop()
        r = create_app(self.cfg).test_client().post("/api/gateway", json={"source": "red", "target": "llm", "payload": "x"})
        body = r.get_json(); self.assertEqual(body["decision"], "ALLOWED"); self.assertFalse(body["llm_result"]["ok"]); self.assertIsNone(body["llm_result"]["response"])

    def test_llm_service_rejects_bad_input(self):
        self.assertEqual(fetch(self.llm.url + "/infer", "POST", {"nope": 1})[0], 400)

    def test_probe_in_sandbox_is_inconclusive_not_isolated(self):
        """On a single machine the zone services cannot resolve 'gateway' etc., so the *control* fails and
        the verdict must NOT be ISOLATED. This guards against reporting isolation that was never demonstrated."""
        c = create_app(self.cfg).test_client()
        body = c.post("/api/isolation/probe").get_json()
        self.assertTrue(body["supported"]); self.assertNotEqual(body["verdict"], "ISOLATED")
        self.assertEqual(c.get("/api/events?event_type=ISOLATION_CHECK_INCONCLUSIVE").get_json()["count"] + c.get("/api/events?event_type=ISOLATION_BREACH").get_json()["count"], 1)

    def test_zone_probe_endpoints_use_fixed_targets(self):
        _, red = fetch(self.red.url + "/probe"); _, blue = fetch(self.blue.url + "/probe")
        self.assertEqual({r["target"] for r in red["results"]}, {"blue-service:8102", "llm-service:8103", "gateway:8000"})
        self.assertEqual({r["target"] for r in blue["results"]}, {"red-service:8101", "llm-service:8103", "gateway:8000"})


class ProbeVerdictTests(unittest.TestCase):
    def zone_rows(self, ctl, blk):
        return [{"target": "gateway:8000", "role": "control", "resolved": "1.1.1.1", "connected": ctl, "error": None},
                {"target": "other:1", "role": "must_be_blocked", "resolved": None, "connected": blk, "error": None}]

    def fake_http(self, red, blue):
        class R:
            def __init__(s, rows): s.rows = rows
            def raise_for_status(s): pass
            def json(s): return {"results": s.rows}
        class H:
            def get(s, url, timeout): return R(red if "red" in url else blue)
        return H()

    def run_it(self, red, blue, tcp_ok=True):
        cfg = Config(mode="docker")
        return run_probe(cfg, http=self.fake_http(red, blue), tcp=lambda h, p, timeout=2.0: {"resolved": "10.0.0.1", "connected": tcp_ok, "error": None})

    def test_isolated(self):
        self.assertEqual(self.run_it(self.zone_rows(True, False), self.zone_rows(True, False))["verdict"], "ISOLATED")

    def test_breach_when_blocked_target_reachable(self):
        r = self.run_it(self.zone_rows(True, True), self.zone_rows(True, False))
        self.assertEqual(r["verdict"], "BREACH"); self.assertTrue(any(c["ok"] is False for c in r["checks"]))

    def test_inconclusive_when_control_fails(self):
        self.assertEqual(self.run_it(self.zone_rows(False, False), self.zone_rows(True, False))["verdict"], "INCONCLUSIVE")

    def test_inconclusive_when_gateway_cannot_reach_services(self):
        self.assertEqual(self.run_it(self.zone_rows(True, False), self.zone_rows(True, False), tcp_ok=False)["verdict"], "INCONCLUSIVE")

    def test_evaluate_checks_edge_cases(self):
        self.assertEqual(evaluate_checks([]), "INCONCLUSIVE")
        self.assertEqual(evaluate_checks([{"role": "must_be_blocked", "connected": False}]), "INCONCLUSIVE")

    def test_breach_is_logged_critical_and_audited(self):
        with tempfile.TemporaryDirectory() as tmp:
            http = self.fake_http(self.zone_rows(True, True), self.zone_rows(True, False))
            app = create_app(Config(mode="docker", data_dir=Path(tmp)), http=http, tcp=lambda h, p, timeout=2.0: {"resolved": "x", "connected": True, "error": None})
            c = app.test_client(); c.post("/api/isolation/probe")
            ev = c.get("/api/events?event_type=ISOLATION_BREACH").get_json()["events"]
            self.assertEqual(ev[0]["severity"], "critical")
            self.assertEqual(c.get("/api/status").get_json()["isolation_last"]["event_type"], "ISOLATION_BREACH")


@unittest.skipIf(yaml is None, "PyYAML not installed (pip install -r requirements-dev.txt)")
class ComposeTopologyTests(unittest.TestCase):
    """STATIC check of docker-compose.yml. This is configuration review, not a runtime isolation test;
    the runtime test is scripts/docker_isolation_test.py (requires Docker)."""
    @classmethod
    def setUpClass(cls):
        cls.c = yaml.safe_load((ROOT / "docker-compose.yml").read_text())

    def nets(self, svc): return set(self.c["services"][svc]["networks"])

    def test_zone_services_are_on_exactly_one_private_network(self):
        self.assertEqual(self.nets("red-service"), {"red_net"}); self.assertEqual(self.nets("blue-service"), {"blue_net"}); self.assertEqual(self.nets("llm-service"), {"llm_net"})

    def test_gateway_is_the_only_bridge(self):
        self.assertEqual(self.nets("gateway"), {"frontend", "red_net", "blue_net", "llm_net"})

    def test_private_networks_are_internal(self):
        for n in ("red_net", "blue_net", "llm_net"): self.assertTrue(self.c["networks"][n].get("internal"), n)
        self.assertFalse(self.c["networks"]["frontend"].get("internal", False))

    def test_only_gateway_publishes_ports_on_loopback(self):
        for name, svc in self.c["services"].items():
            if name != "gateway": self.assertNotIn("ports", svc, name)
        self.assertEqual(self.c["services"]["gateway"]["ports"], ["127.0.0.1:8000:8000"])

    def test_containers_are_hardened_and_have_no_secrets_inline(self):
        h = self.c["x-hardening"]
        self.assertTrue(h["read_only"]); self.assertEqual(h["cap_drop"], ["ALL"]); self.assertIn("no-new-privileges:true", h["security_opt"])
        text = (ROOT / "docker-compose.yml").read_text()
        self.assertNotIn("privileged", text); self.assertRegex(text, r"GEMINI_API_KEY: \$\{GEMINI_API_KEY:-\}")
        for df in ROOT.glob("Dockerfile.*"):
            body = df.read_text(); self.assertIn("USER app", body, df.name); self.assertNotIn("GEMINI_API_KEY", body)


class DockerScriptLogicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.s = load_module("docker_isolation_test", "scripts/docker_isolation_test.py")

    def test_verdicts(self):
        ok = lambda kind, passed: {"name": "x", "kind": kind, "passed": passed}
        self.assertEqual(self.s.evaluate([ok("control", True), ok("isolation", True)])["exit_code"], 0)
        self.assertEqual(self.s.evaluate([ok("control", True), ok("isolation", False)])["verdict"], "FAIL")
        self.assertEqual(self.s.evaluate([ok("control", False), ok("isolation", True)])["verdict"], "INCONCLUSIVE")
        self.assertEqual(self.s.evaluate([])["verdict"], "INCONCLUSIVE")

    def test_probe_snippet_is_valid_python_and_detects_unreachable(self):
        import subprocess
        out = subprocess.run([sys.executable, "-c", self.s.PROBE_CODE, "127.0.0.1", "1"], capture_output=True, text=True, timeout=15)
        res = json.loads(out.stdout); self.assertFalse(res["connected"]); self.assertTrue(res["error"].startswith("tcp:"))
        srv = Server(create_app(Config(data_dir=Path(tempfile.mkdtemp())))); self.addCleanup(srv.stop)
        out = subprocess.run([sys.executable, "-c", self.s.PROBE_CODE, "127.0.0.1", str(srv.port)], capture_output=True, text=True, timeout=15)
        self.assertTrue(json.loads(out.stdout)["connected"])

    def test_script_refuses_gracefully_without_docker(self):
        import shutil, subprocess
        if shutil.which("docker"): self.skipTest("Docker is installed here")
        out = subprocess.run([sys.executable, str(ROOT / "scripts/docker_isolation_test.py")], capture_output=True, text=True)
        self.assertEqual(out.returncode, 3); self.assertIn("NOT RUN", out.stdout)


if __name__ == "__main__":
    unittest.main()
