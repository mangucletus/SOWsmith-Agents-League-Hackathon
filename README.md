# SOWsmith — Bid Package Generator (SOW/RFP) · Supply Chain Agent

An AI agent that turns a buyer's rough project notes into a polished, house-style **Statement of
Work (SOW)** or **Request for Proposal (RFP)** — grounded in SOWsmith's own approved bid packages —
and routes every draft through **human approval** with a full audit trail, plus a **bid-document
Q&A** assistant over prior packages and the clause library.

**Platform:** Microsoft Copilot Studio · Azure OpenAI (GPT-4) · SharePoint Online · Power Automate · Microsoft Teams
**Use case:** Supply Chain · Bid Package Generation · **Success bar:** 5 bid packages drafted **and approved** during the POC.

> **About SOWsmith (sample company)** — SOWsmith is a *fictional* energy & industrial services
> contractor — asset maintenance, construction, and contracting across pipelines, facilities, terminals,
> gas processing, refining, and renewables — used as the sample company for this POC. Its Supply Chain
> team issues the SOWs/RFPs this agent generates. **All data is synthetic; no real company information.**
> Service-type map: [`docs/COMPANY-CONTEXT.md`](docs/COMPANY-CONTEXT.md).

---

## 1. What this POC is

Producing a bid package today is slow and inconsistent — buyers copy-paste from old projects, scope
language is vague or missing exclusions, and quality varies by author. Vague SOWs cause bad bids,
scope disputes, and rework. This POC proves a pattern that turns rough notes into a complete,
house-style package in **~2 hours instead of days**, while a human approves every package and
non-standard commercial terms are routed to Legal/Contracts.

Two flows (see the architecture diagram in [`docs/assets/Bid-Package-Generator_Architecture_Diagram.html`](docs/assets/Bid-Package-Generator_Architecture_Diagram.html)):

- **Flow A — Bid-document Q&A (read):** ask about a prior package or the clause library → grounded,
  **cited** answer. Nothing is changed.
- **Flow B — Draft & approve (write):** rough notes → a seven-section SOW/RFP grounded in 3–5
  gold-standard exemplars → saved to a Drafts library → Power Automate routes it to the right reviewer
  (Supply Chain, or **Legal/Contracts** when non-standard terms are present) → Approve / Request
  changes / Reject → published + logged.

**Scope & lifecycle:** this is **Workstream 1 (Bid Package Generation)** of SOWsmith's 10-workstream Supply
Chain & Quality program — *plus a thin **WS-4 (Bid Evaluation & Award)** slice* so the full bidding lifecycle
(**generate → receive responses → evaluate → recommend award**) demos end-to-end. WS-4's ranking is
deterministic ($0 tokens) and a human approves every award. WS‑4 is shown everywhere — the **interactive
diagram** (an *Evaluate & award (WS‑4)* flow), the **CLI** (`make evaluate` / `make demo`), and the
**web console** (an *Evaluate & award* tab). The heavier streams
(WS-2 takeoffs = computer vision; WS-3 sourcing = agentic) are separate disciplines/owners — full detail in
[`docs/BIDDING-LIFECYCLE.md`](docs/BIDDING-LIFECYCLE.md) and [`docs/ROADMAP.md`](docs/ROADMAP.md).

**Trust & guardrails:** generation is grounded (no invented prices/terms); the system prompt forbids
renaming or editorializing about unfamiliar system/asset names; a **deterministic validator** (zero token
cost) flags invented dollar amounts and inserted speculation before review; and every LEGAL flag is
**explainable** — it states which terms triggered it. A human approves every package.

## 2. How it's intended to go (the production design)

```
Buyer (Microsoft Teams)
  -> Bid Package Agent (Copilot Studio): Topic 1 Draft a Bid Package · Topic 2 Q&A · Topic 3 Status
      -> Azure OpenAI (GPT-4) via the Generative Answers node + the system prompt
      -> SharePoint knowledge:  Approved-Exemplars (generation)  ·  Reference-Library + clause library (Q&A)
  -> draft saved to SharePoint "Drafts"  -> Power Automate approval flow
      -> reviewer decides in Teams (Adaptive Card)  -> Approved / Rejected library + AuditLog
```

## 3. What to achieve (success metrics)

- Bid-package turnaround **days -> ~2 hours**
- **>= 95%** template compliance on drafts (seven-section SOW structure)
- **<= 2** revision rounds before approval
- **5 bid packages** drafted **and approved** during the POC
- **100%** correct routing of non-standard commercial/legal terms to **Legal/Contracts** review

> The 95% / 100% headline numbers require a **live Azure OpenAI** run of the evaluation set
> (see [`docs/EVALUATION.md`](docs/EVALUATION.md)). The offline mock validates plumbing only.

## 4. What runs here vs. what is configured on the tenant

This is a **low-code platform** POC. The Copilot Studio agent and the Power Automate flow are built
in their GUIs on your Microsoft 365 tenant — they cannot be "deployed from code." So this repo gives:

| Layer | In this repo | Runs where |
|---|---|---|
| **Reference engine** (`agent/`) | Runnable Python mirroring the full flow — generate, Q&A, footer-parse, reviewer routing, audit, eval | Locally / CI. Proves & demos the logic **without** a tenant |
| **Web console** (`frontend/`) | A polished UI over the engine | Locally. (Production front-end is **Microsoft Teams**) |
| **Knowledge base** (`knowledge-base/`) | Real SOW/RFP exemplars + clause library + a generator | Upload to SharePoint |
| **Agent config** (`copilot-studio/`) | System prompt, topics, knowledge scoping | **You build in the Copilot Studio GUI** |
| **Approval flow** (`approval-workflow/`) | 10-action flow spec + Adaptive Cards | **You build in the Power Automate GUI** |
| **SharePoint** (`infrastructure/`) | Provisioning scripts (PnP / m365 CLI) | **You run against your tenant** |

A green test suite means **the logic is correct**, not that the production agent is live. To finish
the POC, do the manual steps in **[`docs/MANUAL-SETUP.md`](docs/MANUAL-SETUP.md)**.

## 5. Repository map (by architecture layer)

```
frontend/            UI layer — web console (HTML/CSS/JS). Production = Microsoft Teams.
agent/               Bid Package Agent + Support Layer — runnable reference engine (Python) + tests.
knowledge-base/      SharePoint knowledge base (SOW/RFP exemplars + clause library) + the generator.
copilot-studio/      Agent platform config: system prompt, topics, knowledge scoping.
approval-workflow/   Power Automate flow definition + Adaptive Cards.
infrastructure/      SharePoint provisioning scripts (stand up the real site).
docs/                End-to-end documentation (start here) + source assets.
```

## 6. Quickstart (the reference engine — no secrets needed)

```bash
pip install -e ".[dev]"        # or: pip install -r requirements.txt

# scripted end-to-end demo (offline mock LLM)
PYTHONPATH=agent/src python -m bid_package_agent.cli demo

# web console (open http://127.0.0.1:8080)
PYTHONPATH=agent/src python -m bid_package_agent.cli serve

# draft one from the CLI
PYTHONPATH=agent/src python -m bid_package_agent.cli draft --type "Pipeline Construction" \
  --doc SOW --context "Install a 6-mile 12-inch gas pipeline near Midland: weld, lower-in, hydrotest." --decision Approve

# WS-4: evaluate bidder responses -> award recommendation (built-in sample, or pass --bids file.json)
PYTHONPATH=agent/src python -m bid_package_agent.cli evaluate --type "Pipeline Construction" --doc SOW

# OCR ingestion: extract text from a PDF/image for grounding (digital path always; OCR via the ".[ocr]" extra)
PYTHONPATH=agent/src python -m bid_package_agent.cli ingest <path-to-document>

# tests + the 10-intent evaluation
python -m pytest -q
PYTHONPATH=agent/src python -m bid_package_agent.cli eval
```

Or use the **Makefile** shortcuts: `make help`, `make test`, `make demo`, `make serve`, `make kb`, `make eval`.
See real generated outputs in [`docs/examples/`](docs/examples/).

To run **real grounded generation**, copy `.env.example` -> `.env` and set the Azure OpenAI values
(`.env` is gitignored). Without them the engine uses a deterministic offline mock.

## 7. What has been done so far

See **[`docs/WHAT-HAS-BEEN-DONE.md`](docs/WHAT-HAS-BEEN-DONE.md)**. In short: the knowledge base, the
runnable reference engine + web console, the evaluation harness, the platform artifacts (system prompt,
Adaptive Cards, flow spec), and the SharePoint provisioning scripts are **done and verified**
(45 tests pass, including the deterministic validator, explainable legal-routing, and the WS-4 bid-evaluation
slice). What remains is the **manual tenant configuration** ([`docs/MANUAL-SETUP.md`](docs/MANUAL-SETUP.md)).

## 8. Documentation index

> Full map with reading order and plain-language descriptions: **[`docs/README.md`](docs/README.md)**.

- [`docs/COMPANY-CONTEXT.md`](docs/COMPANY-CONTEXT.md) — **who SOWsmith is** (profile, sectors, service-line mapping, sources)
- [`docs/PRESENTATION-BRIEF.md`](docs/PRESENTATION-BRIEF.md) — **one-page brief for presenting** (problem, solution, diagram walkthrough, talk track)
- [`docs/PROBLEM-AND-APPROACH.md`](docs/PROBLEM-AND-APPROACH.md) — **the problem, how we solve it, the tools, and why this approach fits** (start here)
- [`docs/BIDDING-LIFECYCLE.md`](docs/BIDDING-LIFECYCLE.md) — **the end-to-end bidding lifecycle (WS‑1 → WS‑4), stage by stage** — what's built vs. hand‑off
- [`docs/MANUAL-SETUP.md`](docs/MANUAL-SETUP.md) — **what you must configure** to complete the POC
- [`docs/DEPLOYMENT-CHECKLIST.md`](docs/DEPLOYMENT-CHECKLIST.md) — **printable tick‑box checklist** for the tenant build
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — components, the agent flows + WS‑4, data flows
- [`docs/BUILD-RUNBOOK.md`](docs/BUILD-RUNBOOK.md) — the 4-week build, step by step
- [`docs/EVALUATION.md`](docs/EVALUATION.md) — the 10-intent test set, rubric, how to run it
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — **extensibility & the Supply-Chain agent ecosystem** (reusable substrate, OCR ingestion, adjacent nodes)
- [`docs/examples/`](docs/examples/) — **sample generated outputs** (a standard SOW and a legal-flagged SOW)

---
*Organization: SOWsmith · US English · POC artifact. Figures in the knowledge base are illustrative for the POC.*
