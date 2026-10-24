"""Generate SafeArena_Presenter_Script.docx with comprehensive spoken script,
slide-by-slide guidance, timing, judge cues, and anticipated Q&A defense.
"""
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from pathlib import Path

doc = docx.Document()

# Page Margins
sections = doc.sections
for s in sections:
    s.top_margin = Inches(0.8)
    s.bottom_margin = Inches(0.8)
    s.left_margin = Inches(0.8)
    s.right_margin = Inches(0.8)

# Color Constants
PRIMARY_HEX = "0B0F19"
CYAN_HEX = "00A8B8"
BLUE_HEX = "2563EB"
MUTED_HEX = "64748B"

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

# Title & Metadata
title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
r_title = title.add_run("SafeArena: Pitch Deck Presenter Script & Defense Guide")
r_title.font.name = "Segoe UI"
r_title.font.size = Pt(22)
r_title.font.bold = True
r_title.font.color.rgb = RGBColor(11, 15, 25)

sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
r_sub = sub.add_run("Isolate → Control → Detect → Prove  |  Hack in Hills '26  |  Team: VSV The Tech Giants")
r_sub.font.name = "Segoe UI"
r_sub.font.size = Pt(11)
r_sub.font.bold = True
r_sub.font.color.rgb = RGBColor(0, 168, 184)
sub.paragraph_format.space_after = Pt(18)

# Overview Table
meta_tbl = doc.add_table(rows=4, cols=2)
meta_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
meta_data = [
    ("Presentation Title:", "SafeArena: Controlled Security Testing Environment for AI Systems"),
    ("Target Pitch Duration:", "4 Minutes 30 Seconds (+ Q&A)"),
    ("Target Audience:", "Hackathon Judges, Cybersecurity Architects, AI Safety Engineers"),
    ("Accompanying Deck:", "SafeArena_Premium_Pitch_Deck.pptx (12 Widescreen 16:9 Slides)")
]
for row_idx, (k, v) in enumerate(meta_data):
    c0 = meta_tbl.cell(row_idx, 0)
    c1 = meta_tbl.cell(row_idx, 1)
    c0.width = Inches(2.2)
    c1.width = Inches(4.5)
    set_cell_background(c0, "F1F5F9")
    set_cell_background(c1, "F8FAFC")
    set_cell_margins(c0, 60, 60, 100, 100)
    set_cell_margins(c1, 60, 60, 100, 100)
    
    p0 = c0.paragraphs[0]
    r0 = p0.add_run(k)
    r0.font.bold = True
    r0.font.size = Pt(9.5)
    r0.font.color.rgb = RGBColor(30, 41, 59)
    
    p1 = c1.paragraphs[0]
    r1 = p1.add_run(v)
    r1.font.size = Pt(9.5)
    r1.font.color.rgb = RGBColor(51, 65, 85)

doc.add_paragraph().paragraph_format.space_after = Pt(12)

# Slide-by-Slide Script
slides_data = [
    (
        "Slide 1 — The Hero Slide: SafeArena",
        "0:00 – 0:30 (30 seconds)",
        "“Good morning judges. We are team VSV The Tech Giants, and this is SafeArena. "
        "As generative AI and autonomous agents enter production, security teams are tasked with evaluating model guardrails "
        "against prompt injection and jailbreaks. But today, adversarial testing without rigorous controls is dangerous: "
        "aggressive probes run in flat staging networks can accidentally escape and compromise backend databases or defensive state. "
        "SafeArena introduces a purpose-built security testing infrastructure grounded in four core principles: "
        "Isolate, Control, Detect, and Prove. We segregate testing into isolated sandboxes, mediate all traffic through a default-deny "
        "security gateway, detect prompt-injection threats, and mathematically prove every decision using a SHA-256 audit ledger.”",
        "Hook the judges immediately on the four principles and clarify that SafeArena is an integrated infrastructure, not a generic testing script."
    ),
    (
        "Slide 2 — The Problem: Uncontrolled AI Security Testing",
        "0:30 – 1:00 (30 seconds)",
        "“Why is AI security testing fundamentally different from traditional appsec? "
        "First, blast radius. When red teams execute adversarial prompts or multi-step agent jailbreaks, models invoke APIs, tools, "
        "and retrieve memory. In an unsegmented environment, a test probe can trigger lateral movement into defended databases. "
        "Second, there is rarely an intermediary policy gate: testing tools connect directly to the LLM without access control enforcement. "
        "Third, standard application logs are mutable and ephemeral: an operator or compromised system can easily alter or wipe them. "
        "Organizations cannot prove to an auditor or regulator what prompts were tested or how the system reacted.”",
        "Establish the three-part problem: uncontained blast radius, missing policy mediation, and lack of non-repudiable audit evidence."
    ),
    (
        "Slide 3 — The Design Gap: Why Existing Approaches Leave a Void",
        "1:00 – 1:30 (30 seconds)",
        "“When teams attempt to solve this today, they face two unsatisfactory extremes. "
        "On one side, ad-hoc Python scripts and Jupyter notebooks offer zero network boundaries, no policy checks, and raw text logs. "
        "On the other side, enterprise tooling tries to cobble together generic API gateways and cloud SIEMs. But these generic tools "
        "cost tens of thousands of dollars, lack AI-specific prompt heuristics, and still store logs in mutable SQL tables vulnerable to root tampering. "
        "SafeArena bridges this gap with a purpose-built, self-contained architecture that unites container isolation, default-deny "
        "policy mediation, real-time security events, and cryptographic proof into one unified workflow.”",
        "Show fairness to existing approaches while clearly exposing why they leave an evidentiary void in AI testing."
    ),
    (
        "Slide 4 — Our Solution: The SafeArena Framework",
        "1:30 – 2:00 (30 seconds)",
        "“Here is how SafeArena delivers this unified workflow through our four pillars: "
        "Number one: ISOLATE. Red attack tooling and Blue defensive assets exist in completely segregated zones, bounded in Docker by "
        "internal bridge networks with dropped Linux capabilities and read-only filesystems. "
        "Number two: CONTROL. The Security Gateway is the sole bridge between zones, enforcing an uncompromising default-deny stance. "
        "Number three: DETECT. Every blocked attempt and heuristic prompt-injection pattern generates a structured, severity-rated security event. "
        "Number four: PROVE. Every decision is cryptographically chained using SHA-256 and protected by an atomic head checkpoint.”",
        "Walk through the four pillars rhythmically. Emphasize that each pillar builds directly on the previous one."
    ),
    (
        "Slide 5 — System Architecture: Defense-in-Depth Topology",
        "2:00 – 2:40 (40 seconds)",
        "“Let’s look at the architectural blueprint. This is the heart of SafeArena. "
        "On the left is the Red Sandbox—unprivileged, running attack tooling on red_net. "
        "On the right is the Blue Sandbox—defending internal state on blue_net. "
        "At the top is the Client LLM—isolated on llm_net. "
        "Notice that red_net and blue_net have NO route to each other and NO internet route. The only bridge is the Security Gateway. "
        "Our default policy is strict: Red querying the LLM is ALLOWED through the gateway. Blue querying the LLM is ALLOWED. "
        "However, if Red attempts to reach Blue directly, the Gateway terminates the request with HTTP 403 Forbidden. "
        "The blocked payload is dropped immediately—it never reaches the destination. "
        "Every decision is committed to SQLite for rapid querying and appended to the SHA-256 audit ledger.”",
        "Point to the directional flow badges. Emphasize that the Gateway policy is application-level and Docker internal bridges provide Layer-3 network control."
    ),
    (
        "Slide 6 — How a Request Works: The Request Lifecycle",
        "2:40 – 3:10 (30 seconds)",
        "“What happens under the hood during a single test request? "
        "Step 1: The test runner posts a payload with declared source and target zones. "
        "Step 2: The policy engine evaluates the route against the allow-list. "
        "Step 3: If unauthorized, like Red probing Blue, it is immediately rejected with HTTP 403 and the payload is discarded. "
        "Step 4: If authorized, such as Red probing the LLM, regex heuristics scan for prompt injection patterns and dispatch the request. "
        "Step 5: The gateway canonicalizes the JSON transaction, hashes it with SHA-256, chains it to the previous record, and updates the checkpoint. "
        "Step 6: A structured security event is saved to SQLite with a foreign-key pointer to the audit hash, and the dashboard updates in real time.”",
        "Demonstrate the end-to-end speed and deterministic rigor of the evaluation pipeline."
    ),
    (
        "Slide 7 — Security Engineering & Verifiable Trust Architecture",
        "3:10 – 3:45 (35 seconds)",
        "“Now let's examine the cryptographic proof. "
        "Every transaction is appended to an append-only JSONL file where each record contains the SHA-256 hash of all previous fields. "
        "If an attacker or operator modifies even a single character in Record #2—such as changing BLOCKED to ALLOWED—its SHA-256 digest "
        "changes completely. When Record #3 is verified, its previous-hash pointer fails, pinpointing the exact line of tampering. "
        "Our head checkpoint also detects if records are truncated from the tail. "
        "Our built-in tamper test corrupts log copies across 7 distinct scenarios, and our verifier catches 100% of them. "
        "And we are honest about threat boundaries: a local hash chain cannot stop an adversary with full OS root access who rewrites "
        "both files simultaneously. For production, our roadmap anchors head hashes to external KMS-signed HMACs and WORM cloud storage.”",
        "Highlight the concrete tamper example and showcase technical maturity by openly discussing defensible trust boundaries."
    ),
    (
        "Slide 8 — Product Experience & Live Verification",
        "3:45 – 4:10 (25 seconds)",
        "“This is a genuine screenshot of our live running SafeArena console. "
        "It is built with zero external CDN dependencies and a strict Content Security Policy. "
        "Operators can run one-click scenarios: Red to LLM, Blue to LLM, and blocked cross-zone attempts. "
        "When Red attempts to reach Blue, the gateway visual turns red and a high-severity event appears in the real-time filterable feed. "
        "Clicking 'Verify audit chain' recalculates thousands of SHA-256 links in milliseconds. "
        "And clicking 'Run tamper test' proves our engine by corrupting temporary copies and verifying that all 7 attack vectors are caught. "
        "Our entire test suite of 103 automated tests passed in 8.1 seconds.”",
        "Direct the judges' attention to the actual screenshot. Reference real UI metrics (sessions, blocked counts, verified status)."
    ),
    (
        "Slide 9 — Technology Stack & Engineering Status",
        "4:10 – 4:30 (20 seconds)",
        "“Our implementation is grounded in clean, lightweight, decoupled primitives. "
        "The core engines—policy, audit, events, and LLM interfaces—are completely modular Python 3.12. "
        "We built the web API in Flask for zero-dependency offline testability, with a decoupled structure ready for FastAPI. "
        "The container topology uses Docker Compose with internal bridge subnets and dropped capabilities. "
        "For AI models, we support both a deterministic local mock—with benign, refusal, and canary-leak modes—and upstream Google Gemini API. "
        "Crucially, Gemini API keys reside exclusively in gateway memory and are never exposed in API responses or container logs.”",
        "Reassure judges of clean code architecture, portability, and zero secret leakage."
    ),
    (
        "Slide 10 — Target Users & Real-World AI Applications",
        "4:30 – 4:45 (15 seconds)",
        "“SafeArena serves four key stakeholders: "
        "AI Red Teams who need a blast-proof playground for aggressive jailbreak evaluations. "
        "Enterprise AppSec engineers validating multi-agent access boundaries in CI/CD pipelines. "
        "AI Governance and compliance officers who need non-repudiable audit logs for the EU AI Act and NIST AI RMF. "
        "And universities running hands-on AI security capture-the-flag exercises in a safe, unbreachable lab.”",
        "Rapidly connect technical features to real-world commercial and compliance demand."
    ),
    (
        "Slide 11 — Innovation, Feasibility, and Phased Roadmap",
        "4:45 – 5:00 (15 seconds)",
        "“Our engineering roadmap is practical and grounded. "
        "Phase 1 is 100% complete: our core prototype with default-deny enforcement, audit chaining, and 103 automated tests. "
        "Phase 2 is Docker-ready with internal bridge subnets and automated connectivity probes. "
        "In Phase 3, we replace caller-asserted zone headers with mutual TLS and cryptographic JWT attestation. "
        "In Phase 4, we scale to enterprise production with KMS hardware signing, WORM storage, and multi-node agent swarms.”",
        "Demonstrate that SafeArena is not just a hackathon prototype, but an architectural stepping stone toward enterprise AI defense."
    ),
    (
        "Slide 12 — Closing: Isolate. Control. Detect. Prove.",
        "5:00 – 5:15 (15 seconds)",
        "“In conclusion: SafeArena provides the missing foundation for trustworthy AI security evaluation: "
        "Test AI systems in a controlled environment. Enforce the rules. Record what happens. Verify the evidence. "
        "We are team VSV The Tech Giants. SafeArena is built, tested, and ready for your evaluation. "
        "Thank you judges, and we welcome your questions!”",
        "Deliver the memorable punchline with confidence, thank the judging panel, and open the floor for Q&A."
    )
]

for title_s, time_s, script_s, note_s in slides_data:
    h = doc.add_heading(title_s, level=2)
    h.paragraph_format.space_before = Pt(14)
    h.paragraph_format.space_after = Pt(4)
    
    # Timing pill
    p_time = doc.add_paragraph()
    r_tlabel = p_time.add_run("Target Timing: ")
    r_tlabel.font.bold = True
    r_tlabel.font.size = Pt(9.5)
    r_tval = p_time.add_run(time_s)
    r_tval.font.bold = True
    r_tval.font.color.rgb = RGBColor(0, 168, 184)
    p_time.paragraph_format.space_after = Pt(6)

    # Script Box
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    c = tbl.cell(0, 0)
    c.width = Inches(6.7)
    set_cell_background(c, "F8FAFC")
    set_cell_margins(c, 100, 100, 140, 140)
    
    ps = c.paragraphs[0]
    rs = ps.add_run(script_s)
    rs.font.name = "Segoe UI"
    rs.font.size = Pt(10)
    rs.font.color.rgb = RGBColor(15, 23, 42)
    ps.paragraph_format.line_spacing = 1.15
    
    # Judge Takeaway Note
    pn = doc.add_paragraph()
    rn1 = pn.add_run("Presenter Guidance & Judge Objective: ")
    rn1.font.bold = True
    rn1.font.size = Pt(9)
    rn1.font.color.rgb = RGBColor(100, 116, 139)
    rn2 = pn.add_run(note_s)
    rn2.font.size = Pt(9)
    rn2.font.color.rgb = RGBColor(71, 85, 105)
    pn.paragraph_format.space_after = Pt(12)

# Comprehensive Q&A Section
doc.add_page_break()
h_qa = doc.add_heading("Anticipated Judge Questions & Technical Defense", level=1)
h_qa.paragraph_format.space_before = Pt(16)
h_qa.paragraph_format.space_after = Pt(12)

qa_list = [
    (
        "Q1: Is the Red / Blue network separation real, or is it just simulated in software?",
        "SafeArena has two distinct execution modes, and we are completely transparent about which mode is running: "
        "In Local Mode (run_windows.bat), it is a logical simulation within a single process to enable rapid offline evaluation. "
        "The dashboard explicitly indicates 'Local simulation (policy only)'. "
        "In Docker Mode (run_docker.bat), the separation is physical and containerized: red-service, blue-service, and llm-service "
        "run on separate internal bridge networks (red_net, blue_net, llm_net) with internal: true. They have no IP routing to each other. "
        "Our host-side script scripts/docker_isolation_test.py executes real TCP connection attempts across containers to prove that "
        "cross-zone packets are dropped at the Linux bridge level."
    ),
    (
        "Q2: What prevents an attacker in the Red sandbox from spoofing their source identity header?",
        "In our current hackathon prototype, the caller asserts source: 'red' in the JSON body, which is appropriate for a local testbed "
        "where the operator controls the test harness. However, in our Docker architecture, network segmentation prevents unauthorized socket routing. "
        "As outlined in Phase 3 of our roadmap, production hardening replaces caller-asserted headers with Mutual TLS (mTLS) or "
        "cryptographically signed JWT tokens issued during container startup, binding each request to verified cryptographic zone identity."
    ),
    (
        "Q3: Why can't an attacker who compromises the host simply modify the JSONL audit log?",
        "If an attacker modifies any character, deletes a record, or reorders records in the JSONL log, the SHA-256 chain breaks immediately. "
        "Because each record embeds the cryptographic hash of the previous record, recomputing hashes detects the exact tampered row. "
        "Furthermore, our _head.json checkpoint detects tail-truncation. "
        "However, as an honest engineering team, we document that an attacker with full OS root access could rewrite both the log and checkpoint. "
        "Our enterprise roadmap solves this via external trust anchors: HMAC keys held in AWS KMS / HSMs and immutable WORM storage (S3 Object Lock)."
    ),
    (
        "Q4: How does prompt injection detection work in SafeArena?",
        "SafeArena uses a multi-layered detection approach: "
        "1. Heuristic Inspection: The gateway scans ingress payloads using regex heuristics that detect adversarial prompt patterns, "
        "instruction overrides, role-play jailbreaks, and canary exfiltration attempts. "
        "2. LLM Safety Telemetry: When an authorized request reaches the model, the gateway inspects the model's response for refusal states "
        "('I cannot reveal...') or canary token leaks. "
        "3. Severity Classification: Heuristic hits raise MEDIUM severity events, while policy breaches raise HIGH severity, and canary leaks raise CRITICAL."
    ),
    (
        "Q5: Why did you implement the prototype in Flask rather than FastAPI?",
        "Our original MVP was designed for FastAPI, but our build and test environment lacked external internet access to install FastAPI and Pydantic. "
        "To ensure our code could be executed and rigorously tested with 100+ unit tests, we built the prototype with Flask and Werkzeug. "
        "Crucially, our architecture completely decouples the security logic (policy.py, audit.py, events.py, gateway.py) from the web framework. "
        "Porting SafeArena to FastAPI requires only rewriting backend/app.py; every security control, hash chain, and policy check remains identical."
    )
]

for q, a in qa_list:
    pq = doc.add_paragraph()
    rq = pq.add_run(q)
    rq.font.bold = True
    rq.font.size = Pt(10.5)
    rq.font.color.rgb = RGBColor(11, 15, 25)
    pq.paragraph_format.space_before = Pt(8)
    pq.paragraph_format.space_after = Pt(2)

    pa = doc.add_paragraph()
    ra = pa.add_run(a)
    ra.font.size = Pt(9.5)
    ra.font.color.rgb = RGBColor(51, 65, 85)
    pa.paragraph_format.space_after = Pt(8)

output_docx = Path(r"C:\Users\lenovo\.gemini\antigravity\scratch\SafeArena\SafeArena_Presenter_Script.docx")
doc.save(str(output_docx))
print(f"Presenter script successfully generated at: {output_docx}")
