# The bidding lifecycle — what this POC delivers, end to end

This POC implements the **LLM/RAG spine of SOWsmith's Supply‑Chain bidding lifecycle**:

> **Brief a project → draft the bid package → human approval → issue to bidders → bidders respond → evaluate the responses → recommend an award → human awards.**

Concretely that is **Workstream 1 (Bid Package Generation), built deep**, plus a **thin slice of Workstream 4 (Bid Evaluation & Award)** that closes the loop. The two heavier streams in between — **WS‑2 (Bill of Materials / takeoffs)** and **WS‑3 (Bidder Sourcing)** — are **deliberately out of scope** (different AI disciplines / owners) and are represented here as **hand‑offs**. See [`ROADMAP.md`](ROADMAP.md) for why.

A read‑only **Bid‑document Q&A** assistant (Flow A) runs *across the whole lifecycle* — ask about a prior package or a standard clause at any stage.

---

## The lifecycle at a glance

```
                          ┌───────────────────────────── Flow A · Bid-document Q&A (read, anytime) ─────────────────────────────┐
                          │  "What's our standard exclusions clause for pipeline SOWs?"  → grounded, cited answer               │
                          └──────────────────────────────────────────────────────────────────────────────────────────────────┘

  ┌── WS-1 (built) ───────────────────────────────────────────┐   ┌─ hand-offs ─┐   ┌── WS-4 thin slice (built) ──────────────────┐
  0          1                     2                            3 │ 2·BOM (CV)  │ 4   5                    6                         7
 Brief  →  Draft SOW/RFP   →   Route + human approve   →   Issue │ 3·Sourcing  │ →  Receive   →   Evaluate & recommend   →   Human  → Award/
          (grounded,            (SC vs Legal/Contracts,    to    │ (agentic)   │   responses     award (deterministic,    awards   regret
           7 sections,           content-driven,            invited│ — separate │                 explainable)            (never    notices
           guardrails,           explainable) →             bidders│  owners    │                                          auto)
           validator)           Approved/Rejected+Audit          └─────────────┘                                  +AuditLog
```

---

## Stage by stage

### Stage 0 — Project brief *(buyer input)*
A buyer submits a short brief in Teams (Adaptive Card): **service type**, **document type (SOW/RFP)**, **project context** (3–5 sentences), optional **special requirements**.

### Stage 1 — Draft the bid package  ·  **WS‑1, Flow B**  ·  *built*
The agent generates a **seven‑section SOW (or RFP)** grounded in 3–5 **Approved‑Exemplars**, never inventing prices/quantities, with a machine‑readable footer.
- **Guardrails:** carry domain/system names through **verbatim** (no "Linus"‑style editorializing); **no ungrounded sentences**; ambiguity surfaced under **OPEN QUESTIONS**.
- **Deterministic validator** (zero‑token) then scans the draft for invented dollar amounts and inserted speculation.
- Engine: `generator.py` + `prompts.py` + `validator.py`. CLI: `bidpkg draft`.

### Stage 2 — Route & approve  ·  **WS‑1**  ·  *built*
Power Automate parses the footer and routes the draft. **Review tier is content‑driven**: non‑standard commercial/legal terms (liquidated damages, indemnification, bonding, retainage, net‑90, …) route to **Legal/Contracts**; otherwise to the **Supply Chain** reviewer. The reason is **explainable** (it states *which* terms triggered it). A human chooses **Approve / Request changes / Reject** → file moves to **Approved**/**Rejected** and **every action is logged to AuditLog**.
- Engine: `footer.py` + `approval.py` + `pipeline.run()` + `audit.py`. CLI: `bidpkg draft … --decision Approve`.
- Brief's human‑in‑loop: *Supply Chain lead reviews SOW/RFP before release; PM & Engineering confirm scope; Legal reviews non‑standard T&Cs.* ✔

### Stage 3 — Issue to invited bidders  ·  *hand‑off (assumed)*
The approved package goes to a **qualified/invited bidder list**. Finding & qualifying those bidders is **WS‑3 (Bidder Sourcing)** — agentic + external search + scoring, a **separate stream/owner**; this POC **assumes** the list exists. Confirming the materials list that goes out is **WS‑2 (BOM/Takeoffs)** — **computer vision** on drawings, also a separate stream (the brief says *build once, share with Estimating*).

### Stage 4 — Bidders respond  ·  *input boundary*
Vendors submit responses (price, schedule, exclusions, terms). They enter the POC as **structured input** (the WS‑4 normalizer turns messy formats into a common shape). An **`ingest`** slice already extracts text **digital‑first with an optional OCR fallback** (`bidpkg ingest <file>`; OCR via the `.[ocr]` extra / Azure AI Document Intelligence in production) — the unlock for scanned/legacy PDF responses (see [`ROADMAP.md`](ROADMAP.md) §3); *"bid history is the moat."*

### Stage 5 — Evaluate & recommend award  ·  **WS‑4 thin slice**  ·  *built*
The agent **normalizes** the submissions, **compares** them side‑by‑side, and produces an **explainable award recommendation memo**:
- Recommends the **lowest compliant bid** — *but does not pick blindly:* it **flags non‑standard terms** (reusing the same legal‑trigger logic → routes the award to **Legal/Contracts**), and flags **scope gaps** (more exclusions than peers) and **outlier‑low pricing** (possible scope misunderstanding).
- The ranking is **deterministic analytics — $0 tokens, no hallucination, fully explainable** (in production the LLM only normalizes messy formats and writes the prose).
- It pulls **comparable past bids** from the Reference‑Library for context (the "historical retriever").
- Engine: `bid_eval.py` + `pipeline.evaluate_award()`. CLI: `bidpkg evaluate`.

### Stage 6 — Human awards  ·  **WS‑4**  ·  *built (the gate)*
**The agent never awards.** It ranks and flags; a human decides: *buyer recommends → Supply Chain manager / PM approve → Finance signs off above threshold.* The decision is recorded in **AuditLog**. (Brief: *"AI never awards a bid… Buyers, QC and managers retain decision authority."*) ✔

### Stage 7 — Award / regret notices  ·  *hand‑off (thin slice stops here)*
Full WS‑4 includes an **award‑notification agent** (award/regret letters from approved templates). The thin slice stops at the **approved recommendation**; notifications are a documented follow‑on.

---

## What's built vs. what's a hand‑off

| Stage | Capability | Status | Where it lives |
|---|---|---|---|
| 0 | Project brief intake | ✅ built | Adaptive Card · `cli draft` |
| 1 | Draft SOW/RFP (grounded, guardrails, validator) | ✅ **built (deep)** | `generator.py`, `prompts.py`, `validator.py` |
| 2 | Route + human approval + audit | ✅ built | `footer.py`, `approval.py`, `pipeline.py`, `audit.py` |
| — | Bid‑document Q&A (anytime) | ✅ built | `qa.py` (Flow A) |
| 3 | BOM verification (WS‑2) | ⛔ out of scope (computer vision) | *separate stream / Estimating* |
| 3 | Bidder sourcing (WS‑3) | ⛔ out of scope (agentic) | *separate stream* — list assumed |
| 4 | Receive responses | ◻ input boundary | normalizer; `ocr.py` + `ingest` (digital + optional OCR) |
| 5 | Evaluate + recommend award | ✅ **built (thin)** | `bid_eval.py`, `pipeline.evaluate_award()` |
| 6 | Human awards | ✅ built (the gate) | reuses `approval.route()` + audit |
| 7 | Award/regret notices | ◻ documented follow‑on | full WS‑4 |

---

## Trust, cost & explainability across the lifecycle *(the lead's review points)*
- **Deterministic where it counts — $0 tokens, no hallucination.** Structure, footer, routing, validation and the **WS‑4 ranking** are all deterministic code; the LLM is used only for narrative prose (one call per draft). Re‑running checks/rankings costs nothing.
- **A human approves at every gate** — the draft (Stage 2) and the award (Stage 6). The agent drafts, ranks and flags; it never publishes or awards on its own.
- **Explainable** — Q&A answers are cited; every LEGAL flag (draft *and* award) states **which terms triggered it**; the validator names the lines to re‑read.
- **Audited** — every draft decision and award recommendation is written to AuditLog.

## Try the whole lifecycle (no tenant, no secrets)
```bash
# the full arc in one scripted run (draft → contracts → refusal → Q&A → evaluate & award)
make demo

# or step through it:
PYTHONPATH=agent/src python -m bid_package_agent.cli draft  --type "Pipeline Construction" --doc SOW \
  --context "Install a 6-mile 12-inch gas pipeline near Midland: weld, lower-in, hydrotest." --decision Approve
PYTHONPATH=agent/src python -m bid_package_agent.cli evaluate --type "Pipeline Construction" --doc SOW \
  --bids docs/examples/sample-bids_Pipeline-Construction.json

# OCR ingestion (digital text always; OCR fallback with the ".[ocr]" extra + Tesseract)
PYTHONPATH=agent/src python -m bid_package_agent.cli ingest <path-to-document>

# or click through it in the web console (Ask / Draft / Evaluate & award / Audit):
make serve   # http://127.0.0.1:8080
```
See real outputs in [`examples/`](examples/): a standard SOW, a legal‑flagged SOW, sample bids, and the award‑recommendation memo.

## Related docs
[`ARCHITECTURE.md`](ARCHITECTURE.md) (components & flows) · [`ROADMAP.md`](ROADMAP.md) (why WS‑2/3 are separate; OCR next) · [`PRESENTATION-BRIEF.md`](PRESENTATION-BRIEF.md) (talk track) · [`MANUAL-SETUP.md`](MANUAL-SETUP.md) (tenant build).
