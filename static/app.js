"use strict";
/* SafeArena dashboard. Every number and row shown comes from the backend API.
   Untrusted text (prompts, messages) is only ever inserted with textContent. */

const $ = (id) => document.getElementById(id);
const KNOWN_TYPES = ["ACCESS_ALLOWED", "POLICY_VIOLATION", "PROMPT_INJECTION_DETECTED", "SESSION_START", "AUDIT_VERIFY",
  "AUDIT_INTEGRITY_FAILURE", "AUDIT_TAMPER_TEST", "AUDIT_ROTATED", "NETWORK_ISOLATION_CONFIRMED", "ISOLATION_BREACH",
  "ISOLATION_CHECK_INCONCLUSIVE", "LLM_ERROR", "LLM_PROTECTED_MARKER_LEAKED"];
let refreshing = false;
let flashTimer = null;
let queryTimer = null;

function el(tag, props = {}, ...kids) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "class") node.className = v;
    else if (k === "text") node.textContent = v;
    else node.setAttribute(k, v === true ? "" : v);
  }
  for (const kid of kids.flat()) {
    if (kid === null || kid === undefined || kid === false) continue;
    node.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
  }
  return node;
}
const short = (h, n = 12) => (h ? String(h).slice(0, n) + "…" : "—");
const when = (iso) => (iso ? new Date(iso).toLocaleTimeString() : "—");

async function api(path, { method = "GET", body } = {}) {
  const opts = { method, headers: {} };
  if (body !== undefined) { opts.headers["Content-Type"] = "application/json"; opts.body = JSON.stringify(body); }
  else if (method === "POST") { opts.headers["Content-Type"] = "application/json"; opts.body = "{}"; }
  const res = await fetch(path, opts);
  let data = null;
  try { data = await res.json(); } catch (_) { /* non-JSON error page */ }
  return { ok: res.ok, status: res.status, data: data || { error: `HTTP ${res.status}` } };
}

/* ---------------------------------------------------------------- results */
function facts(rows) {
  const dl = el("dl", { class: "facts" });
  for (const [k, v] of rows) {
    if (v === null || v === undefined || v === "") continue;
    dl.append(el("dt", { text: k }), el("dd", {}, v));
  }
  return dl;
}
function raw(data) {
  return el("details", { class: "raw" }, el("summary", { text: "Raw API response" }), el("pre", { text: JSON.stringify(data, null, 2) }));
}
function showResult(kind, badge, title, ...body) {
  const box = $("resultBox");
  box.className = `result-box ${kind}`;
  box.replaceChildren(el("div", { class: "result-head" }, el("span", { class: `badge ${kind}`, text: badge }), el("span", { class: "result-title", text: title })), ...body);
}
function showError(message) { showResult("bad", "ERROR", "Request failed", el("p", { text: message })); }

function showGateway(r) {
  const d = r.data;
  if (!d.decision) return showError(d.error || "Unexpected response");
  const allowed = d.decision === "ALLOWED";
  const llm = d.llm_result;
  showResult(allowed ? "allowed" : "blocked", d.decision, `${d.source.toUpperCase()} → ${d.target.toUpperCase()}`,
    facts([
      ["Reason", d.reason], ["Rule", d.rule],
      ["LLM response", llm && (llm.response || llm.error)],
      ["LLM safety", llm && llm.safety],
      ["Provider / model", llm && `${llm.provider} / ${llm.model}`],
      ["Latency", llm && llm.latency_ms !== undefined ? `${llm.latency_ms} ms` : null],
      ["Injection patterns", d.detections && d.detections.length ? d.detections.join(", ") : null],
      ["Event", d.security_event && `#${d.security_event.id} ${d.security_event.event_type} (${d.security_event.severity})`],
      ["Audit record", el("code", { text: `#${d.audit_seq} ${d.audit_hash}` })],
    ]), raw(d));
  flashGateway(d.source, d.target, d.decision);
}

function showVerification(d, title = "Audit chain verification") {
  const ok = !!d.valid;
  showResult(ok ? "allowed" : "bad", ok ? "VERIFIED" : "FAILED", title,
    facts([
      ["Records checked", d.count], ["Head hash", d.head_hash && el("code", { text: d.head_hash })],
      ["Anchored by checkpoint", d.anchored ? "yes" : "no"],
      ["Failed at record", d.failed_index !== null && d.failed_index !== undefined ? `#${d.failed_index}` : null],
      ["Reason", d.reason], ["Warning", d.warning],
    ]), raw(d));
}

function showTamper(d) {
  const table = el("table", { class: "mini-table" },
    el("thead", {}, el("tr", {}, ["Tampering applied", "Detected", "Where / why"].map((t) => el("th", { text: t })))),
    el("tbody", {}, d.scenarios.map((s) => el("tr", {},
      el("td", { text: s.description }),
      el("td", { class: s.detected ? "ok" : "no", text: s.detected ? "Yes" : "NO" }),
      el("td", { text: s.detected ? `record #${s.failed_index ?? "?"}: ${s.reason}` : "not detected" })))));
  showResult(d.all_detected ? "allowed" : "bad", d.all_detected ? "ALL DETECTED" : "GAP FOUND", "Tamper test on copies of the audit log",
    el("p", { text: `Ran on: ${d.source} (${d.records_in_copy} records). The live log was not modified.` }), table, raw(d));
}

function showProbe(d) {
  if (!d.supported) {
    showResult("warn", "NOT APPLICABLE", "Network isolation probe", el("p", { text: d.message }));
    return;
  }
  const kind = d.verdict === "ISOLATED" ? "allowed" : d.verdict === "BREACH" ? "bad" : "warn";
  const table = el("table", { class: "mini-table" },
    el("thead", {}, el("tr", {}, ["From", "To", "Expected", "Actual", "Result"].map((t) => el("th", { text: t })))),
    el("tbody", {}, d.checks.map((c) => el("tr", {},
      el("td", { text: c.zone }), el("td", { text: c.target }), el("td", { text: c.expected }),
      el("td", { text: c.connected ? "reachable" : `unreachable${c.error ? " (" + c.error + ")" : ""}` }),
      el("td", { class: c.ok ? "ok" : "no", text: c.ok ? "OK" : "UNEXPECTED" })))));
  showResult(kind, d.verdict, "Docker network isolation probe",
    el("p", { text: d.verdict === "INCONCLUSIVE" ? "A control check failed, so this run cannot confirm isolation." : "Real TCP connection attempts made from inside the containers." }), table, raw(d));
}

function flashGateway(source, target, decision) {
  const pair = [source, target].sort().join("-");
  const gates = pair === "llm-red" ? ["A"] : pair === "blue-llm" ? ["B"] : pair === "blue-red" ? ["A", "B"] : [];
  const cls = decision === "ALLOWED" ? "allowed" : "blocked";
  for (const g of ["A", "B"]) { $(`gate${g}`).querySelector(".gate-card").className = "gate-card"; $(`gate${g}Text`).textContent = "idle"; }
  for (const g of gates) { $(`gate${g}`).querySelector(".gate-card").className = `gate-card ${cls}`; $(`gate${g}Text`).textContent = decision.toLowerCase(); }
  for (const z of ["Red", "Blue", "Llm"]) $(`zone${z}`).classList.remove("flash-red", "flash-blue", "flash-llm");
  $(`zone${source === "llm" ? "Llm" : source[0].toUpperCase() + source.slice(1)}`)?.classList.add(`flash-${source}`);
  clearTimeout(flashTimer);
  flashTimer = setTimeout(() => flashGateway("none", "none", "x"), 4000);
}

/* ---------------------------------------------------------------- renderers */
function renderStatus(s) {
  const publicDemo = !!s.public_demo;
  $("securityNote").textContent = publicDemo
    ? "Password-protected public demo. Local simulation only; no network isolation."
    : "Local prototype. Keep bound to localhost; no authentication in local mode.";
  document.querySelectorAll('[data-action="archive"], [data-action="probe"], [data-action="tamper"], a[href="/api/audit/export"]')
    .forEach((node) => { node.hidden = publicDemo; });
  $("modeBadge").textContent = s.mode_label;
  $("enforcement").textContent = s.enforcement;
  $("llmProvider").textContent = `${s.llm.provider}${s.llm.provider === "mock" ? " (offline mock)" : ""}`;
  $("llmTransport").textContent = s.llm.fallback_reason || `${s.llm.model} · ${s.llm.transport}`;
  $("sessionId").textContent = s.session_id || "—";
  $("sessionStarted").textContent = s.session_started ? new Date(s.session_started).toLocaleString() : "";
  $("blockedCount").textContent = s.events.session.blocked;
  $("allowedCount").textContent = `${s.events.session.allowed} allowed · ${s.events.session.total} events`;
  const a = s.audit;
  const st = $("auditState");
  st.textContent = a.valid ? "Verified" : "FAILED";
  st.className = a.valid ? "state-ok" : "state-bad";
  $("auditCount").textContent = `${a.count} records${a.valid && a.anchored === false && a.count ? " · no checkpoint" : ""}`;
  $("redNetwork").textContent = s.zones.red.network;
  $("llmNetwork").textContent = s.zones.llm.network;
  $("blueNetwork").textContent = s.zones.blue.network;
  const iso = $("isolationState"), note = $("isolationNote");
  if (s.mode === "docker") {
    const last = s.isolation_last;
    if (!last) { iso.textContent = "Not run"; iso.className = "state-wait"; note.textContent = "Click “Run network isolation probe”"; }
    else {
      const v = last.event_type === "NETWORK_ISOLATION_CONFIRMED" ? ["Confirmed", "state-ok"] : last.event_type === "ISOLATION_BREACH" ? ["BREACH", "state-bad"] : ["Inconclusive", "state-warn"];
      iso.textContent = v[0]; iso.className = v[1]; note.textContent = `Last probe ${new Date(last.timestamp).toLocaleTimeString()}`;
    }
    $("topologyPill").textContent = "Separate Docker networks"; $("topologyPill").className = "pill ok";
  } else {
    iso.textContent = "Not applicable"; iso.className = "state-wait"; note.textContent = "Local mode: policy only, no network isolation";
    $("topologyPill").textContent = "Logical zones (simulation)"; $("topologyPill").className = "pill warn";
  }
}

function renderPolicy(m) {
  const t = $("policyMatrix");
  const rows = Object.fromEntries(m.rules.map((r) => [`${r.source}>${r.target}`, r]));
  const name = (z) => (z === "llm" ? "LLM" : z[0].toUpperCase() + z.slice(1));
  t.replaceChildren(t.querySelector("caption"),
    el("thead", {}, el("tr", {}, el("th", { text: "From \\ To" }), m.zones.map((z) => el("th", { text: name(z) })))),
    el("tbody", {}, m.zones.map((s) => el("tr", {}, el("th", { text: name(s) }), m.zones.map((z) => {
      const r = rows[`${s}>${z}`];
      if (s === z) return el("td", { class: "self", text: "n/a", title: "Same-zone traffic is not routed through the gateway" });
      return el("td", { class: r.action === "ALLOW" ? "allow" : "deny", text: r.action, title: r.rule });
    })))));
}

function eventNode(e) {
  const route = e.source || e.target ? `${(e.source || "—").toUpperCase()} → ${(e.target || "—").toUpperCase()}` : null;
  return el("div", { class: `event sev-${e.severity}` },
    el("div", { class: "top" }, el("span", { class: "sev", text: e.severity }), el("b", { text: e.message })),
    el("small", {}, [e.event_type, route, e.decision, `#${e.id}`, new Date(e.timestamp).toLocaleTimeString()].filter(Boolean).join(" · "),
      e.audit_hash ? el("span", {}, " · audit ", el("code", { text: short(e.audit_hash, 10), title: e.audit_hash })) : null));
}

function renderEvents(data) {
  const box = $("events");
  $("eventCountLine").textContent = data.total_matching === data.count
    ? `${data.count} event${data.count === 1 ? "" : "s"} shown`
    : `Showing ${data.count} of ${data.total_matching} matching events`;
  if (!data.events.length) {
    box.replaceChildren(el("div", { class: "empty-state", text: filtersActive() ? "No events match these filters." : "No events yet. Run a test to generate some." }));
    return;
  }
  box.replaceChildren(...data.events.map(eventNode));
}

function renderAudit(data) {
  const v = data.verification;
  $("auditHead").textContent = v.valid
    ? `Chain intact · ${v.count} records · head ${short(v.head_hash, 16)}${v.anchored ? "" : " · no checkpoint"}`
    : `Chain broken at record #${v.failed_index ?? "?"}: ${v.reason}`;
  const header = el("div", { class: "audit-row head" }, ["#", "Time", "Event", "Actor", "Message", "Hash"].map((t) => el("div", { text: t })));
  if (!data.records.length) { $("audit").replaceChildren(el("div", { class: "empty-state", text: "Audit records will appear here." })); return; }
  const bad = v.valid ? null : v.failed_index;
  $("audit").replaceChildren(header, ...data.records.map((r) => el("div", { class: `audit-row${bad !== null && r.seq === bad ? " bad" : ""}` },
    el("div", { text: r.seq ?? "—" }), el("div", { text: when(r.timestamp) }), el("div", {}, el("b", { text: r.event_type || "(corrupt line)" })),
    el("div", { text: r.actor || "" }), el("div", { text: r.message || r._corrupt_line || "" }),
    el("div", {}, el("code", { text: short(r.hash, 16), title: r.hash || "" })))));
}

/* ---------------------------------------------------------------- data flow */
function filterParams() {
  const p = new URLSearchParams();
  for (const [id, key] of [["fSeverity", "severity"], ["fDecision", "decision"], ["fSource", "source"], ["fTarget", "target"], ["fType", "event_type"], ["fScope", "scope"]]) {
    if ($(id).value) p.set(key, $(id).value);
  }
  if ($("fQuery").value.trim()) p.set("q", $("fQuery").value.trim());
  p.set("limit", "100");
  return p;
}
function filtersActive() {
  return ["fSeverity", "fDecision", "fSource", "fTarget", "fType"].some((id) => $(id).value) || $("fQuery").value.trim() !== "";
}
function syncTypeOptions(byType) {
  const sel = $("fType"), current = sel.value;
  const types = [...new Set([...KNOWN_TYPES, ...Object.keys(byType || {})])].sort();
  if (types.join() === [...sel.options].slice(1).map((o) => o.value).join()) return;
  sel.replaceChildren(el("option", { value: "", text: "All types" }), types.map((t) => el("option", { value: t, text: t })));
  sel.value = current;
}

async function refresh() {
  if (refreshing) return;
  refreshing = true;
  try {
    const [status, events, audit, stats] = await Promise.all([
      api("/api/status"), api(`/api/events?${filterParams()}`), api("/api/audit?limit=40"), api("/api/events/stats?scope=all"),
    ]);
    if (status.ok) renderStatus(status.data);
    if (events.ok) renderEvents(events.data);
    if (audit.ok) renderAudit(audit.data);
    if (stats.ok) syncTypeOptions(stats.data.by_type);
  } catch (err) {
    $("auditState").textContent = "Backend offline"; $("auditState").className = "state-bad";
  } finally { refreshing = false; }
}

async function run(button, work) {
  if (button) button.disabled = true;
  try { await work(); } catch (err) { showError(`Could not reach the backend (${err.message}).`); }
  finally { if (button) button.disabled = false; await refresh(); }
}

const actions = {
  session: () => run(null, async () => {
    const r = await api("/api/session/start", { method: "POST" });
    if (!r.ok) return showError(r.data.error);
    showResult("allowed", "NEW SESSION", r.data.session_id, el("p", { text: "Event view now shows only this session. Nothing was deleted: earlier events remain under “All sessions” and the audit chain keeps every record." }), facts([["Audit record", el("code", { text: r.data.audit_hash })]]));
  }),
  archive: () => run(null, async () => {
    if (!confirm("Archive the current audit chain and start a new one?\n\nThe old log is moved to data/archive/ (not deleted) and the new chain's first record references its final hash.")) return;
    const r = await api("/api/audit/rotate", { method: "POST", body: { confirm: true } });
    if (!r.ok) return showError(r.data.error);
    showResult("allowed", "ARCHIVED", r.data.archived_file, facts([["Records archived", r.data.archived_count], ["Archived chain valid", String(r.data.archived_chain_valid)], ["New chain first hash", el("code", { text: r.data.new_chain_first_hash })]]));
  }),
  scenario: (btn) => run(btn, async () => showGateway(await api(`/api/demo/${btn.dataset.scenario}`, { method: "POST" }))),
  probe: (btn) => run(btn, async () => { const r = await api("/api/isolation/probe", { method: "POST" }); r.ok ? showProbe(r.data) : showError(r.data.error); }),
  verify: (btn) => run(btn, async () => { const r = await api("/api/audit/verify", { method: "POST" }); r.ok ? showVerification(r.data) : showError(r.data.error); }),
  tamper: (btn) => run(btn, async () => { const r = await api("/api/audit/tamper-test", { method: "POST" }); r.ok ? showTamper(r.data) : showError(r.data.error); }),
  refresh: (btn) => run(btn, async () => {}),
  "clear-filters": () => { for (const id of ["fSeverity", "fDecision", "fSource", "fTarget", "fType", "fQuery"]) $(id).value = ""; refresh(); },
};

document.addEventListener("click", (ev) => {
  const btn = ev.target.closest("[data-action]");
  if (btn && actions[btn.dataset.action]) actions[btn.dataset.action](btn);
});
$("customForm").addEventListener("submit", (ev) => {
  ev.preventDefault();
  run(ev.submitter, async () => showGateway(await api("/api/gateway", { method: "POST", body: { source: $("cSource").value, target: $("cTarget").value, payload: $("cPayload").value } })));
});
for (const id of ["fSeverity", "fDecision", "fSource", "fTarget", "fType", "fScope"]) $(id).addEventListener("change", refresh);
$("fQuery").addEventListener("input", () => { clearTimeout(queryTimer); queryTimer = setTimeout(refresh, 250); });

(async () => {
  const policy = await api("/api/policy");
  if (policy.ok) renderPolicy(policy.data);
  await refresh();
  setInterval(() => { if ($("liveToggle").checked && !document.hidden) refresh(); }, 3000);
})();
