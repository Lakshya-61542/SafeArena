# SafeArena

**Isolate → Control → Detect → Prove**

SafeArena is a sandbox for testing adversarial prompts against an AI model without letting the attackers and defenders touch each other. A **Red** zone (attack) and a **Blue** zone (defense) can only reach the **Client LLM** through a **Security Gateway**. Every decision becomes a security event and a tamper-evident, SHA-256 hash-chained audit record.

| Step | What it means here |
|---|---|
| **Isolate** | Red, Blue and LLM are separate zones; in Docker they sit on separate internal networks |
| **Control** | The gateway enforces a default-deny policy |
| **Detect** | Blocked access and suspicious prompts raise severity-rated events (filterable, persisted) |
| **Prove** | Every decision is appended to a hash-chained audit log that can be verified and exported |

## Default security policy

| From \ To | Red | Blue | LLM |
|---|---|---|---|
| **Red** | – | **DENY** | **ALLOW** |
| **Blue** | **DENY** | – | **ALLOW** |
| **LLM** | DENY | DENY | – |

Anything not explicitly allowed is denied (including unknown zone names).

---

## Two run modes — read this before demoing

| | **Local mode** (`run_windows.bat`) | **Docker mode** (`run_docker.bat`) |
|---|---|---|
| Policy enforcement by the gateway | Yes | Yes |
| Audit chain, events, dashboard, tests | Yes | Yes |
| Separate networks per zone | **No – logical zones in one process (simulation)** | **Yes – `red_net`, `blue_net`, `llm_net`, all `internal: true`** |
| "Isolation evidence" / network probe | Shows *Not applicable* | Real TCP attempts from inside the containers |

The dashboard always shows which mode you are in. **Local mode demonstrates policy enforcement only. Do not describe it as network isolation.** Network isolation is only claimed when `scripts/docker_isolation_test.py` (or the dashboard probe in Docker mode) has actually run and passed on a machine with Docker.

---

## Quick start (Windows)

Requirements: Python 3.10+ ([python.org](https://www.python.org/downloads/), tick *Add python.exe to PATH*). Docker Desktop is only needed for Docker mode.

**Easiest:** double-click `run_windows.bat` (creates `.venv`, installs dependencies, copies `.env.example` → `.env`, opens the dashboard).

**Manual, PowerShell:**

```powershell
cd SafeArena
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1          # if blocked: Set-ExecutionPolicy -Scope Process Bypass
pip install -r requirements.txt
copy .env.example .env
python run_local.py
```

**Manual, Command Prompt (cmd.exe):**

```bat
cd SafeArena
py -3 -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
copy .env.example .env
python run_local.py
```

Open <http://127.0.0.1:8000>. macOS/Linux: `./run_local.sh`.

### Run the automated tests

```bat
run_tests.bat
```
or, with the venv active:
```bat
pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```
(No pytest needed; the suite uses Python's built-in `unittest`.)

### Docker mode and the real isolation test

```bat
run_docker.bat                         :: builds and starts the 4 containers, dashboard at http://127.0.0.1:8000
run_docker_isolation_test.bat          :: builds, starts, runs the connectivity tests, writes reports\docker_isolation_report.json, stops
```
Equivalent: `docker compose up --build` and `python scripts/docker_isolation_test.py [--keep] [--no-build]`.
Exit codes: `0` pass · `1` fail · `2` inconclusive (a positive control failed) · `3` Docker not available. The script never prints PASS for something it did not run.

---

## Optional: real Gemini instead of the mock

1. Get an API key from Google AI Studio.
2. In `.env`: `LLM_PROVIDER=gemini` and `GEMINI_API_KEY=your-key` (optionally `GEMINI_MODEL=...`).
3. Restart. The sidebar shows `gemini`. The key stays on the server: it is sent only in a request header to Google, never returned by any endpoint, never logged, never part of error text, and `.env` is excluded from Git and from Docker images.

If the provider is `gemini` but the key is missing, the app falls back to the mock **and says so** in the sidebar and `/api/llm/status`. In Docker mode, Gemini calls are made by the gateway (the only container with internet access); the isolated `llm-service` stays mock-only.

---

## Architecture

```
Browser ─► Gateway (Flask, 127.0.0.1:8000) ──► Policy ─► allow ─► Client LLM (mock | Gemini)
                │                               └─► deny  ─► 403
                ├─► Audit chain  data/audit_log.jsonl  (+ _head.json checkpoint)
                └─► Event store  data/events.db        (SQLite, filterable)

Docker:  red-service ─red_net─┐
         blue-service ─blue_net─┼─ gateway ─ llm_net ─ llm-service
                                └─ frontend ─ host 127.0.0.1:8000
```

| Path | Purpose |
|---|---|
| `backend/policy.py` | Default-deny policy engine |
| `backend/gateway.py` | Decision → dispatch → audit → event |
| `backend/audit.py` | Hash chain, checkpoint, verification, rotation, tamper self-test |
| `backend/events.py` | Persistent event store + filters |
| `backend/llm.py`, `common/mock_llm.py` | Client LLM (mock / remote mock / Gemini) and prompt-injection heuristics |
| `backend/isolation.py` | Docker probe orchestration; INCONCLUSIVE if controls fail |
| `backend/app.py` | Flask API, Host/Origin checks, CSP, rate limit |
| `services/*.py` | Red, Blue and LLM zone containers |
| `static/` | Dashboard (all data from the API) |
| `scripts/docker_isolation_test.py` | Host-side real connectivity test |
| `tests/` | 100+ unit/API/integration tests |

### API

`GET /api/status · /api/policy · /api/llm/status · /api/events (severity, decision, source, target, event_type, q, scope, since_id, limit) · /api/events/stats · /api/audit · /api/audit/verify · /api/audit/export`
`POST /api/gateway · /api/demo/{authorized-red-llm|blue-llm|red-blue|blue-red} · /api/session/start · /api/audit/verify · /api/audit/tamper-test · /api/audit/rotate {"confirm":true} · /api/isolation/probe`

`POST /api/gateway` takes `{"source","target","payload"}` and returns **200 ALLOWED** or **403 BLOCKED**.

### Audit log

Each line is `{seq, timestamp, event_type, actor, message, details, session_id, prev_hash, hash}` with `hash = SHA-256(canonical JSON of all other fields)` and `prev_hash` = previous record's hash (`GENESIS` for the first). Verification recomputes every hash and link, then checks the stored checkpoint to catch deletion from the end of the log. It is persistent (survives restarts) and never wiped: "Archive audit chain" moves the old log to `data/archive/` and starts a new chain whose first record contains the archived chain's head hash.

The **tamper test** button corrupts *copies* of the log in a temp directory (edit, edit+rehash, delete, reorder, forged insert, tail truncation, corrupt line) and runs the real verifier on each. The live log is never touched.

---

## Security measures

Bound to `127.0.0.1` (non-loopback refused unless explicitly overridden; Docker publishes to host loopback only) · Host-header allow-list (DNS-rebinding) · same-origin check on all POSTs + JSON content-type · input validation and size limits · POST rate limit · strict CSP, no inline scripts, DOM built with `textContent` (prompts can't inject HTML) · parameterised SQL · no secrets in responses/logs · containers: non-root, read-only filesystem, all capabilities dropped, `no-new-privileges`, internal networks.

## Known limitations

- **No authentication.** Anyone who can reach the port can use the API. It is localhost-only by design; do not expose it.
- **Zone identity is asserted by the caller.** In this prototype the `source` field is trusted (the dashboard "acts as" a zone). Network segmentation (Docker mode) is the real boundary; production would need per-zone credentials (mTLS or signed tokens).
- **Local mode is a simulation** of isolation (policy only).
- **Audit chain limits:** an attacker who can rewrite *both* the log and its checkpoint file consistently is not detected. Production needs an external anchor (HMAC key kept elsewhere, WORM storage, or publishing the head hash).
- **Prompt-injection detection is heuristic** (regex + the model's own refusals); it is an alert, not a guarantee.
- The Docker probe relies on the zone containers reporting honestly; the host-side script runs probes via `docker exec` instead.
- **Gemini integration** is covered by mocked-HTTP tests only; it has not been run against the live API in the build environment (no key/network). Model names change; set `GEMINI_MODEL` as needed.
- Flask's built-in server is used (fine for a localhost prototype, not for production); events DB and audit log are single-node files.
- Windows `.bat` scripts and Docker mode could not be executed in the environment where this was built — see `docs/TEST_RESULTS.md`.

## Backend framework note

The original MVP used FastAPI. This build uses Flask because the build environment had no network to install FastAPI/pydantic, and a backend that cannot be executed cannot be honestly tested. All logic lives in framework-independent modules (`policy`, `audit`, `events`, `llm`, `gateway`, `isolation`), so a FastAPI port only needs to rewrite `backend/app.py`.
