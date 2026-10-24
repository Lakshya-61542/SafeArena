# SafeArena demo guide (about 4 minutes)

**Before you start:** `run_windows.bat` (local mode) or `run_docker.bat` (Docker mode). Open http://127.0.0.1:8000.
Check the sidebar: it says *Local simulation (policy only)* or *Docker (network-isolated zones)*. Say which one you are showing.

## Script

| Time | Do | Say | What the audience should see |
|---|---|---|---|
| 0:00 | Point at the sidebar and zone diagram | "SafeArena isolates Red attackers, Blue defenders and the model under test. Isolate, control, detect, prove." | Three zones, policy matrix (Red→Blue DENY, Blue→Red DENY, both → LLM ALLOW) |
| 0:30 | Click **Red → LLM adversarial prompt** | "Red is allowed to reach the model, through the gateway." | ALLOWED, LLM refuses, a *medium* PROMPT_INJECTION_DETECTED event, an audit hash |
| 1:00 | Click **Blue → LLM defensive query** | "Blue has the same authorized path." | ALLOWED |
| 1:20 | Click **Red → Blue access attempt** | "Now Red tries to reach Blue's defenses directly." | BLOCKED 403, *high* POLICY_VIOLATION event, "Blocked" counter goes up, gateway card turns red |
| 1:40 | Click **Blue → Red access attempt** | "And the reverse." | BLOCKED |
| 2:00 | In *Security events*: Severity = high; then search `RED` | "Everything is logged, persisted and filterable." | Filter counts update from the backend |
| 2:30 | Type a custom request (LLM → Red) and send | "Anything not on the allow-list is denied by default." | BLOCKED, rule `default-deny` |
| 2:50 | Click **Verify audit chain** | "Each record contains the SHA-256 of the previous one." | VERIFIED, record count, head hash |
| 3:10 | Click **Run tamper test** | "We corrupt copies of the log seven different ways. The real verifier catches every one; the live log isn't touched." | Table: every scenario *Detected = Yes* with the record index |
| 3:40 | **Docker only:** click **Run network isolation probe** | "Containers actually try to reach each other." | Verdict ISOLATED with a table of reachable/unreachable results (controls reachable, cross-zone unreachable) |
| 4:00 | *Local mode:* say plainly | "In local mode this is a policy simulation. Network isolation is verified in Docker." | Probe shows *Not applicable* — that is expected |

## Optional extra proof (terminal)

Live tamper demo (stop the server first, or just edit and click Verify):

1. Open `data/audit_log.jsonl`, change any character inside one line, save.
2. Click **Verify audit chain** → **FAILED**, with the record number and the reason. The broken row is highlighted in the audit table.
3. Restore by clicking **Archive audit chain** (old log is kept in `data/archive/`, never deleted).

Docker proof: `run_docker_isolation_test.bat` prints a PASS/FAIL line per check (including "RED → BLUE by name" and "by IP") and writes `reports\docker_isolation_report.json`.

## Q&A answers

- *Is the Red/Blue separation real?* In Docker mode, yes: separate internal networks, verified by the test script. In local mode it is policy only.
- *Can someone spoof the source?* In this prototype the caller names its zone; the network boundary is the real control. Production would use per-zone credentials.
- *Why can't someone just edit the log?* They can, but any edit, deletion, insertion or reorder breaks the chain and is reported; deleting the newest records is caught by the checkpoint. A determined attacker who rewrites both files needs an external anchor to be caught — a documented limitation.
