"""Optional browser test: clicks every dashboard control against a real server and asserts on the results.

    pip install playwright && playwright install chromium
    python scripts/ui_smoke_test.py
"""
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from playwright.sync_api import sync_playwright  # noqa: E402
from werkzeug.serving import make_server  # noqa: E402

from backend.app import create_app  # noqa: E402
from backend.config import Config  # noqa: E402


def main() -> int:
    srv = make_server("127.0.0.1", 0, create_app(Config(data_dir=Path(tempfile.mkdtemp()))), threaded=True)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_port}"
    failures, errors = [], []

    def check(name, cond, detail=""):
        print(f"[{'PASS' if cond else 'FAIL'}] {name} {detail if not cond else ''}")
        if not cond: failures.append(name)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        pg = browser.new_page(viewport={"width": 1400, "height": 1000})
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.on("dialog", lambda d: d.accept())
        pg.goto(base); pg.wait_for_selector("#policyMatrix td.allow")

        def click(sel): pg.click(sel); pg.wait_for_timeout(500)
        def result(): return pg.inner_text("#resultBox")

        check("policy matrix rendered from API", pg.locator("#policyMatrix td.deny").count() >= 4)
        check("mode shown", "Local simulation" in pg.inner_text("#modeBadge"))
        click('[data-scenario="authorized-red-llm"]'); r = result()
        check("Red->LLM allowed", "ALLOWED" in r and "cannot reveal" in r)
        click('[data-scenario="blue-llm"]'); check("Blue->LLM allowed", "ALLOWED" in result())
        click('[data-scenario="red-blue"]'); check("Red->Blue blocked", "BLOCKED" in result() and "explicit-deny" in result())
        click('[data-scenario="blue-red"]'); check("Blue->Red blocked", "BLOCKED" in result())
        check("blocked counter = 2", pg.inner_text("#blockedCount") == "2")
        click('[data-action="probe"]'); check("probe honest in local mode", "NOT APPLICABLE" in result())
        click('[data-action="verify"]'); check("verify works", "VERIFIED" in result())
        check("audit state verified", pg.inner_text("#auditState") == "Verified")
        click('[data-action="tamper"]'); check("tamper test: all detected", "ALL DETECTED" in result())
        pg.select_option("#cSource", "llm"); pg.select_option("#cTarget", "red"); pg.fill("#cPayload", "<img src=x onerror=alert(1)>")
        click('#customForm button[type=submit]'); check("custom request default-deny", "default-deny" in result())
        check("no HTML injected", pg.locator("#events img, #resultBox img, #audit img, #cPayload ~ img").count() == 0)
        pg.select_option("#fSeverity", "high"); pg.wait_for_timeout(600)
        check("severity filter", pg.locator("#events .event").count() == 3 and all("sev-high" in (c or "") for c in pg.locator("#events .event").evaluate_all("els=>els.map(e=>e.className)")))
        pg.select_option("#fSeverity", ""); pg.select_option("#fDecision", "ALLOWED"); pg.wait_for_timeout(600)
        check("decision filter", pg.locator("#events .event").count() >= 2)
        click('[data-action="clear-filters"]'); pg.fill("#fQuery", "zzz-no-match"); pg.wait_for_timeout(700)
        check("search filter empty state", "No events match" in pg.inner_text("#events"))
        pg.fill("#fQuery", ""); pg.wait_for_timeout(600)
        click('[data-action="session"]'); check("fresh session", "NEW SESSION" in result() and pg.inner_text("#blockedCount") == "0")
        pg.select_option("#fScope", "all"); pg.wait_for_timeout(600)
        check("old events still visible under All sessions", "POLICY_VIOLATION" in pg.inner_text("#events"))
        click('[data-action="archive"]'); check("archive keeps old log", "ARCHIVED" in result() and "Archived chain valid" in result())
        click('[data-action="refresh"]')
        check("export link present", pg.locator('a[href="/api/audit/export"]').count() == 1)
        pg.set_viewport_size({"width": 390, "height": 900}); pg.wait_for_timeout(300)
        check("no horizontal scroll on phone width", not pg.evaluate("document.documentElement.scrollWidth > innerWidth"))
        browser.close()
    srv.shutdown()
    check("no uncaught JS errors", not errors, str(errors))
    print(f"\n{'ALL PASSED' if not failures else 'FAILED: ' + ', '.join(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
