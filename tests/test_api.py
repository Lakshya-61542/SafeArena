import base64
import json
import unittest

from tests.helpers import AppTestCase

JSON = {"Content-Type": "application/json"}


class ApiTests(AppTestCase):
    def post(self, path, body=None, **kw):
        return self.client.post(path, data=json.dumps(body if body is not None else {}), headers=JSON, **kw)

    # ---- basics
    def test_dashboard_and_assets_served(self):
        for path in ("/", "/static/app.js", "/static/styles.css"):
            r = self.client.get(path); self.assertEqual(r.status_code, 200, path); r.close()

    def test_health_status_policy(self):
        self.assertTrue(self.client.get("/api/health").get_json()["ok"])
        s = self.client.get("/api/status").get_json()
        self.assertEqual(s["mode"], "local"); self.assertTrue(s["audit"]["valid"]); self.assertTrue(s["session_id"].startswith("SA-"))
        self.assertIn("policy enforcement only", s["enforcement"]); self.assertEqual(s["llm"]["provider"], "mock")
        m = self.client.get("/api/policy").get_json()
        got = {(r["source"], r["target"]): r["action"] for r in m["rules"]}
        self.assertEqual((got[("red", "llm")], got[("blue", "llm")], got[("red", "blue")], got[("blue", "red")]), ("ALLOW", "ALLOW", "DENY", "DENY"))

    # ---- gateway
    def test_gateway_allow_and_block_status_codes(self):
        r = self.post("/api/gateway", {"source": "red", "target": "llm", "payload": "hello"})
        self.assertEqual(r.status_code, 200); self.assertEqual(r.get_json()["decision"], "ALLOWED"); self.assertIn("Test prompt received safely", r.get_json()["llm_result"]["response"])
        r = self.post("/api/gateway", {"source": "blue", "target": "red", "payload": "x"})
        self.assertEqual(r.status_code, 403); self.assertEqual(r.get_json()["decision"], "BLOCKED")

    def test_gateway_input_validation(self):
        self.assertEqual(self.post("/api/gateway", {"source": "red"}).status_code, 400)
        self.assertEqual(self.post("/api/gateway", {"source": 5, "target": "llm"}).status_code, 400)
        self.assertEqual(self.post("/api/gateway", {"source": "re d!", "target": "llm"}).status_code, 400)
        self.assertEqual(self.post("/api/gateway", {"source": "red", "target": "llm", "payload": 123}).status_code, 400)
        self.assertEqual(self.post("/api/gateway", {"source": "red", "target": "llm", "payload": "x" * 4001}).status_code, 413)
        self.assertEqual(self.client.post("/api/gateway", data="[1]", headers=JSON).status_code, 400)
        self.assertEqual(self.client.post("/api/gateway", data="not json", headers=JSON).status_code, 400)
        self.assertEqual(self.client.post("/api/gateway", data="source=red", content_type="application/x-www-form-urlencoded").status_code, 415)
        self.assertEqual(self.client.post("/api/gateway", data="x" * 70000, headers=JSON).status_code, 413)
        self.assertEqual(self.ctx.events.count(event_type="POLICY_VIOLATION"), 0)

    def test_demo_scenarios(self):
        expect = {"authorized-red-llm": 200, "blue-llm": 200, "red-blue": 403, "blue-red": 403}
        for name, code in expect.items():
            self.assertEqual(self.post(f"/api/demo/{name}").status_code, code, name)
        self.assertEqual(self.post("/api/demo/nope").status_code, 404)

    # ---- events
    def test_events_filtering_through_api(self):
        self.post("/api/demo/authorized-red-llm"); self.post("/api/demo/red-blue"); self.post("/api/demo/blue-red")
        g = lambda q: self.client.get("/api/events?" + q).get_json()
        self.assertEqual(g("severity=high")["count"], 2)
        self.assertEqual(g("decision=BLOCKED&source=red")["count"], 1)
        self.assertEqual(g("event_type=PROMPT_INJECTION_DETECTED")["count"], 1)
        self.assertEqual(g("q=Unauthorized")["count"], 2)
        self.assertEqual(g("limit=2")["count"], 2); self.assertGreater(g("limit=2")["total_matching"], 2)
        self.assertEqual(self.client.get("/api/events?severity=bogus").status_code, 400)
        self.assertEqual(self.client.get("/api/events?limit=abc").status_code, 400)
        self.assertEqual(self.client.get("/api/events?since_id=abc").status_code, 400)
        self.assertEqual(self.client.get("/api/events?q=%27%3B+DROP+TABLE+events%3B--").get_json()["count"], 0)
        self.assertEqual(self.client.get("/api/events/stats").get_json()["by_decision"]["BLOCKED"], 2)

    def test_session_start_scopes_events_without_deleting(self):
        self.post("/api/demo/red-blue"); old = self.client.get("/api/status").get_json()["session_id"]
        new = self.post("/api/session/start").get_json()["session_id"]; self.assertNotEqual(old, new)
        self.assertEqual(self.client.get("/api/events?event_type=POLICY_VIOLATION").get_json()["count"], 0)
        self.assertEqual(self.client.get("/api/events?scope=all&event_type=POLICY_VIOLATION").get_json()["count"], 1)
        self.assertEqual(self.client.get(f"/api/events?scope={old}&event_type=POLICY_VIOLATION").get_json()["count"], 1)

    def test_events_survive_restart(self):
        self.post("/api/demo/red-blue")
        from backend.app import create_app
        again = create_app(self.config).test_client()
        self.assertEqual(again.get("/api/events?scope=all&event_type=POLICY_VIOLATION").get_json()["count"], 1)
        self.assertTrue(again.get("/api/status").get_json()["audit"]["valid"])

    # ---- audit
    def test_audit_verify_flow(self):
        self.post("/api/demo/red-blue")
        self.assertTrue(self.client.get("/api/audit/verify").get_json()["valid"])
        before = self.client.get("/api/audit/verify").get_json()["count"]
        self.assertEqual(self.client.get("/api/audit/verify").get_json()["count"], before)  # GET is read-only
        r = self.post("/api/audit/verify").get_json(); self.assertTrue(r["valid"]); self.assertIn("recorded_as", r)
        self.assertEqual(self.client.get("/api/audit/verify").get_json()["count"], before + 1)
        recs = self.client.get("/api/audit?limit=3").get_json()["records"]; self.assertEqual(recs[0]["event_type"], "AUDIT_VERIFY")

    def test_real_tampering_of_live_file_is_detected_through_api(self):
        self.post("/api/demo/red-blue"); self.post("/api/demo/blue-llm")
        path = self.ctx.audit.path; lines = path.read_text().splitlines(); rec = json.loads(lines[1]); rec["actor"] = "evil"; lines[1] = json.dumps(rec)
        path.write_text("\n".join(lines) + "\n")
        r = self.post("/api/audit/verify").get_json(); self.assertFalse(r["valid"]); self.assertEqual(r["failed_index"], 1)
        self.assertFalse(self.client.get("/api/status").get_json()["audit"]["valid"])
        self.assertEqual(self.client.get("/api/events?event_type=AUDIT_INTEGRITY_FAILURE").get_json()["count"], 1)

    def test_tamper_test_endpoint(self):
        for _ in range(3): self.post("/api/demo/red-blue")
        r = self.post("/api/audit/tamper-test").get_json()
        self.assertTrue(r["all_detected"]); self.assertFalse(r["live_log_modified"]); self.assertTrue(self.client.get("/api/audit/verify").get_json()["valid"])

    def test_rotate_requires_confirm_and_archives(self):
        self.assertEqual(self.post("/api/audit/rotate", {}).status_code, 400)
        r = self.post("/api/audit/rotate", {"confirm": True}); self.assertEqual(r.status_code, 200)
        self.assertTrue((self.data_dir / "archive" / r.get_json()["archived_file"]).exists())
        self.assertTrue(self.client.get("/api/audit/verify").get_json()["valid"])

    def test_export(self):
        r = self.client.get("/api/audit/export"); self.assertEqual(r.status_code, 200)
        self.assertIn("attachment", r.headers["Content-Disposition"]); self.assertIn(b"SESSION_START", r.data); r.close()

    def test_isolation_probe_in_local_mode_claims_nothing(self):
        r = self.post("/api/isolation/probe").get_json()
        self.assertFalse(r["supported"]); self.assertEqual(r["verdict"], "NOT_APPLICABLE")

    def test_llm_status_never_exposes_key(self):
        self.assertNotIn("api_key", json.dumps(self.client.get("/api/llm/status").get_json()).lower())

    # ---- security controls
    def test_host_header_allowlist(self):
        self.assertEqual(self.client.get("/api/health", headers={"Host": "evil.example"}).status_code, 400)
        self.assertEqual(self.client.get("/api/health", headers={"Host": "127.0.0.1:8000"}).status_code, 200)
        self.assertEqual(self.client.get("/api/health", headers={"Host": "[::1]:8000"}).status_code, 200)

    def test_cross_origin_post_rejected_same_origin_allowed(self):
        h = {**JSON, "Origin": "http://evil.example"}
        self.assertEqual(self.client.post("/api/session/start", data="{}", headers=h).status_code, 403)
        h["Origin"] = "http://localhost"
        self.assertEqual(self.client.post("/api/session/start", data="{}", headers=h).status_code, 200)

    def test_security_headers_and_errors_are_json(self):
        r = self.client.get("/api/health")
        self.assertIn("default-src 'self'", r.headers["Content-Security-Policy"]); self.assertEqual(r.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(r.headers["Cache-Control"], "no-store")
        n = self.client.get("/api/nope"); self.assertEqual(n.status_code, 404); self.assertIn("error", n.get_json())
        self.assertEqual(self.client.delete("/api/health").status_code, 405)

    def test_index_has_no_inline_script_or_handlers(self):
        r = self.client.get("/"); html = r.get_data(as_text=True); r.close()
        self.assertNotRegex(html, r"<script(?![^>]*\bsrc=)"); self.assertNotRegex(html, r"\son\w+\s*=")


class RateLimitTests(AppTestCase):
    config_overrides = {"rate_limit_per_minute": 3}

    def test_post_rate_limit(self):
        codes = [self.client.post("/api/demo/red-blue").status_code for _ in range(5)]
        self.assertEqual(codes[:3], [403, 403, 403]); self.assertEqual(codes[3:], [429, 429])
        self.assertEqual(self.client.get("/api/health").status_code, 200)


class UnexpectedErrorTests(AppTestCase):
    def test_500_does_not_leak_details(self):
        def boom(*a, **k): raise RuntimeError("secret internals")
        self.ctx.gateway.handle = boom
        with self.assertLogs("backend.app", level="ERROR"):
            r = self.client.post("/api/demo/red-blue")
        self.assertEqual(r.status_code, 500); self.assertNotIn("secret", r.get_data(as_text=True))



class PublicDemoApiTests(AppTestCase):
    config_overrides = {
        "public_demo": True,
        "demo_username": "judge",
        "demo_password": "safearena-demo-password-123",
        "allowed_hosts": ("demo.example",),
    }

    def _headers(self, credentials=None):
        headers = {"Host": "demo.example"}
        if credentials is not None:
            token = base64.b64encode(credentials.encode("utf-8")).decode("ascii")
            headers["Authorization"] = f"Basic {token}"
        return headers

    def _post(self, path, body=None, credentials=None):
        return self.client.post(path, json=body or {}, headers=self._headers(credentials))

    def test_all_routes_require_auth_except_health(self):
        for path in ("/", "/static/app.js", "/api/status", "/api/policy", "/api/audit", "/api/audit/export"):
            response = self.client.get(path, headers=self._headers())
            self.assertEqual(response.status_code, 401, path)
            self.assertIn('Basic realm="SafeArena Demo"', response.headers.get("WWW-Authenticate", ""))
        self.assertEqual(self.client.get("/api/health", headers=self._headers()).status_code, 200)
        self.assertEqual(self._post("/api/demo/blue-llm").status_code, 401)

    def test_valid_basic_auth_enables_dashboard_and_mock_gateway(self):
        credentials = "judge:safearena-demo-password-123"
        self.assertEqual(self.client.get("/", headers=self._headers(credentials)).status_code, 200)
        status = self.client.get("/api/status", headers=self._headers(credentials)).get_json()
        self.assertTrue(status["public_demo"])
        self.assertEqual(status["mode"], "local")
        self.assertEqual(status["llm"]["provider"], "mock")
        response = self._post("/api/gateway", {
            "source": "red", "target": "llm", "payload": "hello"
        }, credentials)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["decision"], "ALLOWED")

    def test_wrong_basic_auth_is_rejected(self):
        response = self.client.get("/", headers=self._headers("judge:wrong-password"))
        self.assertEqual(response.status_code, 401)
        self.assertIn("WWW-Authenticate", response.headers)

    def test_sensitive_operations_are_disabled_without_mutating_audit(self):
        credentials = "judge:safearena-demo-password-123"
        before = self.ctx.audit.verify()["count"]
        checks = [
            self._post("/api/audit/tamper-test", credentials=credentials),
            self._post("/api/audit/rotate", {"confirm": True}, credentials),
            self._post("/api/isolation/probe", credentials=credentials),
            self.client.get("/api/audit/export", headers=self._headers(credentials)),
        ]
        for response in checks:
            self.assertEqual(response.status_code, 403)
        self.assertEqual(self.ctx.audit.verify()["count"], before)

    def test_failed_authentication_attempts_are_rate_limited(self):
        codes = [self.client.get("/", headers=self._headers()).status_code for _ in range(11)]
        self.assertEqual(codes[:10], [401] * 10)
        self.assertEqual(codes[10], 429)


if __name__ == "__main__":
    unittest.main()
