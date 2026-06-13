# Architecture

Open the visual diagram: [`assets/Bid-Package-Generator_Architecture_Diagram.html`](assets/Bid-Package-Generator_Architecture_Diagram.html)
(interactive — click a flow to watch it run end-to-end). The problem framing and tooling rationale live in
[`PROBLEM-AND-APPROACH.md`](PROBLEM-AND-APPROACH.md); the build order in [`BUILD-RUNBOOK.md`](BUILD-RUNBOOK.md);
the full end-to-end **bidding lifecycle (WS‑1 + WS‑4)** in [`BIDDING-LIFECYCLE.md`](BIDDING-LIFECYCLE.md).

## Components (and where each lives in this repo)

| Architecture box | Role | Repo layer |
|---|---|---|
| Users · Chat Interface | Buyers / Supply Chain staff interact via Microsoft Teams (prod) / the web console (demo) | `frontend/` |
| Bid Package Agent | Copilot Studio agent: intent detection + 3 topics | `copilot-studio/` (config) · `agent/` (engine mirror) |
| Support Layer | Copilot Studio orchestration + Azure OpenAI (GPT-4) | `agent/src/bid_package_agent/llm.py`, `prompts.py` |
| Knowledge Base | SharePoint Online: grounding sources + output libraries + governance lists | `knowledge-base/`, provisioned by `infrastructure/` |
| Power Automate | Approval routing, conditional legal branch, audit | `approval-workflow/` (spec) · `agent/.../approval.py,pipeline.py,audit.py` |

## The agent flows (and the WS‑4 evaluation slice)

The Copilot Studio agent has **two flows** (read / write); a downstream **WS‑4** slice closes the bidding
lifecycle (generate → evaluate → award). Full stage‑by‑stage detail: [`BIDDING-LIFECYCLE.md`](BIDDING-LIFECYCLE.md).

**Flow A — Bid-document Q&A (read).** User question → RAG over the **Reference-Library** → grounded answer
with citations. Read-only. Runs across the whole lifecycle.
Engine: `qa.py` → `knowledge_base.search_reference()` (TF-IDF locally; Copilot Studio semantic search in prod).

**Flow B — Draft & publish (write) · WS‑1.** Rough notes → grounded on **Approved-Exemplars** (3–5 gold-standard)
→ seven-section SOW (or RFP) with a version footer → **deterministic validation** → saved to **Drafts** →
Power Automate routes to the reviewer (standard **Supply Chain** vs **Legal/Contracts**) → Approve / Request
changes / Reject → **Approved**/**Rejected** + **AuditLog**.
Engine: `generator.py` → `validator.py` → `pipeline.run()` → `approval.route()` / `apply_decision()` → `audit.append_audit()`.

**WS‑4 — Bid Evaluation & Award (thin slice).** After bidders respond, the agent normalizes the submissions,
compares them **deterministically**, and produces an **explainable award recommendation** — the lowest
compliant bid, with non-standard terms flagged (→ Legal/Contracts, reusing the same routing) and scope/outlier
risks surfaced. **The agent never awards — a human does.**
Engine: `bid_eval.py` → `pipeline.evaluate_award()` → `approval.route()` + `audit.append_audit()`.

## The critical scoping choice (two libraries, not one)

- **`Approved-Exemplars`** feeds the **generator** — a small, clean set so drafts copy the right house style.
- **`Reference-Library`** feeds **Q&A** — the broad published corpus.

Mixing them dilutes draft quality. This split is enforced by topic-level knowledge scoping in
Copilot Studio and mirrored by the two indexes in `knowledge_base.py`.

## The footer contract

Every draft ends with a machine-readable footer:
```
---
VERSION: v0.1 DRAFT
DATE: 2026-06-03
SERVICE TYPE: Pipeline Construction
DOCUMENT TYPE: SOW
REVIEW STATUS: STANDARD REVIEW
---
```
Power Automate (action 3) parses `SERVICE TYPE` + `REVIEW STATUS` from it to look up the reviewer and
choose the legal vs standard branch. The engine's `footer.py` parses the same block; the **review tier
is content-driven** — `safety.needs_legal_review()` flags non-standard commercial/legal terms (liquidated
damages, indemnification, bonding, retainage, …) so the *same* service type can route standard or legal.

## Reference engine ↔ production mapping

| Production | Reference engine |
|---|---|
| Copilot Studio semantic search over SharePoint | `retrieval.py` (TF-IDF) + `textextract.py` (DOCX/PDF/PPTX/XLSX) |
| Azure OpenAI generative answers + system prompt | `llm.py` (Azure backend) + `prompts.py`; offline **mock** when no key |
| SharePoint Drafts/Approved/Rejected libraries | folders under `var/run/` |
| SharePoint Reviewers list | `Lists/Reviewers.xlsx` (read by `knowledge_base.load_reviewers`) |
| SharePoint AuditLog list + Power Automate action 10 | `var/run/AuditLog.csv` (`audit.py`) |
| WS‑4 bid comparison + award recommendation (LLM normalizes formats in prod) | `bid_eval.py` (deterministic ranking) → `pipeline.evaluate_award()` → memo in `var/run/Evaluations/` |

The engine lets you prove and demo the logic without a tenant; the platform is the production target.
