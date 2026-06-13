# Documentation map — start here

Plain-language guide to every document in this folder. Read top to bottom, or jump to what you need.

## 1 · Understand the POC (start here)
| Doc | What it tells you |
|---|---|
| [`PROBLEM-AND-APPROACH.md`](PROBLEM-AND-APPROACH.md) | The problem we solve, how we solve it, the tools, and why this approach fits. **Best first read.** |
| [`COMPANY-CONTEXT.md`](COMPANY-CONTEXT.md) | Who **SOWsmith** is (the client) and how the bid-package service types map to their real work. |
| [`BIDDING-LIFECYCLE.md`](BIDDING-LIFECYCLE.md) | The whole bidding lifecycle, stage by stage: **brief → draft → approve → issue → evaluate → award** (WS‑1 + WS‑4). |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | The components, the two agent flows + the WS‑4 slice, and where each piece lives in the repo. |
| [`assets/Bid-Package-Generator_Architecture_Diagram.html`](assets/Bid-Package-Generator_Architecture_Diagram.html) | The **interactive diagram** — open in a browser and click a flow to watch it run. |

## 2 · Present it
| Doc | What it tells you |
|---|---|
| [`PRESENTATION-BRIEF.md`](PRESENTATION-BRIEF.md) | A one-page brief + a 5-minute demo script for showing the POC to a lead or the client. |
| [`examples/`](examples/) | Real generated outputs: a standard SOW, a legal-flagged SOW, sample bids, and an award-recommendation memo. |

## 3 · Build it on the tenant (make it live)
| Doc | What it tells you |
|---|---|
| [`MANUAL-SETUP.md`](MANUAL-SETUP.md) | The **click-by-click** build: SharePoint site → provisioning → Copilot Studio agent → Azure OpenAI → Power Automate flow → publish to Teams. |
| [`DEPLOYMENT-CHECKLIST.md`](DEPLOYMENT-CHECKLIST.md) | A **printable tick-box** version of the build — keep it beside you. |
| [`PHASE-B-SETTINGS.md`](PHASE-B-SETTINGS.md) | The **exact** Copilot Studio node settings + Power Automate expressions (the fiddliest parts, copy-paste ready). |
| [`BUILD-RUNBOOK.md`](BUILD-RUNBOOK.md) | The same work as a week-by-week plan. |
| [`EVALUATION.md`](EVALUATION.md) | The 10-test set + scoring rubric — how to measure the POC and get the headline numbers. |

## 4 · Status & what's next
| Doc | What it tells you |
|---|---|
| [`WHAT-HAS-BEEN-DONE.md`](WHAT-HAS-BEEN-DONE.md) | Everything built and verified so far, plus what remains (the tenant build). |
| [`ROADMAP.md`](ROADMAP.md) | How this extends — the reusable substrate, OCR ingestion, and the adjacent Supply-Chain agents. |

---
**Scope in one line:** this POC is **Workstream 1 (Bid Package Generation)** plus a thin **WS‑4 (Bid Evaluation & Award)** slice — the LLM/RAG spine of SOWsmith's bidding lifecycle. WS‑2 (takeoffs, computer vision) and WS‑3 (bidder sourcing, agentic) are separate efforts.

**Run it locally (no tenant needed):** from the repo root, `make demo` (scripted walk-through) or `make serve` (web console). See the top-level [`../README.md`](../README.md).
