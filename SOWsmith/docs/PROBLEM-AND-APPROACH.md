# Problem, approach & tooling

## 1. The problem

Producing **bid packages** — the Statements of Work (SOW) and Requests for Proposal (RFP) that SOWsmith's
Supply Chain team issues to subcontractors and vendors — is slow, inconsistent, and risky:

- **Slow.** A new SOW/RFP takes **days** — most of it *not* defining scope, but formatting, restructuring
  to house style, copy-pasting from a past job, and chasing reviewers by email.
- **Inconsistent.** Different buyers and project teams produce different structure, tone and terminology,
  so scope sections vary, exclusions get missed, and quality drifts package to package.
- **Risky.** Non-standard commercial and legal terms (liquidated damages, indemnification, bonding,
  retainage, warranty, insurance limits) can slip into a package without **Legal/Contracts** review, and
  ungrounded drafts can invent prices, quantities or commitments SOWsmith never agreed to.
- **Siloed.** Buyers can't easily find what prior winning bid packages actually said, so the same scope
  language and clause questions get re-asked repeatedly.

For **SOWsmith** — the *fictional* sample company used in this POC — a specialized
**asset maintenance, construction, and contracting services** contractor to the energy, chemical, manufacturing and
industrial sectors (oil & gas pipelines, facilities and terminals; gas processing; CO₂; refining &
chemicals; renewables) with a **safety-first** culture, SOWsmith runs
many concurrent **field projects** governed by **OSHA / DOT / PHMSA**. Its Supply Chain function issues a
high volume of SOWs/RFPs across these disciplines, so consistent, complete, well-governed bid packages are
mission-critical: they set the scope a subcontractor is held to and the terms SOWsmith is exposed to.
(Full profile: [`COMPANY-CONTEXT.md`](COMPANY-CONTEXT.md).)

## 2. What we are solving (Workstream 1 — Bid Package Generation)

Prove a repeatable pattern that gives Supply Chain two capabilities, with quality and governance baked in:

- **Flow A — Bid-document Q&A (read):** answer natural-language questions about *prior bid packages and
  the standard clause library*, grounded and **cited**.
- **Flow B — Draft & publish (write):** turn a short project brief into a **seven-section SOW (or RFP)**
  in SOWsmith's house style, grounded in the organization's own approved exemplar bid packages, then route
  it through **human approval** (Supply Chain, or Legal/Contracts when terms are non-standard) with an
  audit trail.

This is a **POC, not a product**: prove it with one well-chosen service type; success = **5 bid packages
drafted and approved**. It is **not** a fully-automated system, **not** a pricing engine, and **not** a
legal advisor.

## 3. How we solve it

A **two-flow agent** (plus a thin **WS‑4 Bid Evaluation & Award** slice that closes the bidding lifecycle —
see [`BIDDING-LIFECYCLE.md`](BIDDING-LIFECYCLE.md)) delivered in Microsoft Teams:

1. **Ground, don't guess.** Generation and Q&A are both grounded (RAG) in SOWsmith's approved bid documents —
   the model never invents prices, quantities or scope detail and always cites sources.
2. **Two scoped knowledge libraries.** `Approved-Exemplars` (3–5 gold-standard SOWs) is the *style +
   structure anchor* for drafting; `Reference-Library` (the broad corpus of past packages + the clause
   library) is the *answer set* for Q&A. Separating them is the single biggest quality lever.
3. **Safety rails + human-in-the-loop.** A system prompt flags non-standard commercial/legal terms for
   **LEGAL REVIEW REQUIRED**, leaves prices and thresholds as bracketed placeholders, and refuses improper
   requests (invent a price, waive liability, bypass review). **Every** package is approved by a human
   before it is issued.
4. **A machine-readable footer** drives **Power Automate** to route each draft to the right reviewer
   (standard **Supply Chain** vs **Legal/Contracts**) and record every action in an audit log.

## 4. The tools — and why each is the right choice

The client environment is **Microsoft 365**, so the stack is the native M365 AI toolchain. Each tool is
chosen because it removes work a custom build would otherwise force on us:

| Tool | Role | Why it's the right fit (vs the alternative) |
|---|---|---|
| **Microsoft Copilot Studio** | Agent orchestration, topics, Teams publishing | Low-code agent with **built-in SharePoint grounding** and Teams delivery. A custom-coded agent would add infra, auth, hosting and maintenance with no POC benefit. |
| **Azure OpenAI (GPT-4)** | Drafting & reasoning | Enterprise GPT-4 **inside the tenant** — data residency & security. Public model APIs raise data-governance concerns for procurement and contract data. |
| **SharePoint Online** | Knowledge base + output store + governance lists | Already the org's document home; **native Copilot grounding**, versioning, permissions, audit. A standalone vector DB is unnecessary infrastructure for a POC and duplicates what SharePoint already provides. |
| **Power Automate** | Approval routing, conditional legal branch, audit | Native M365 workflow with **Teams Adaptive Cards** and connectors — no backend to build or run. |
| **Microsoft Teams** | Delivery channel | Where buyers and project teams already work; SSO; rich Adaptive Cards for input and approvals. |
| **Microsoft Graph / Adaptive Cards** | Identity, integration, structured UI | First-class in M365; no custom UI framework needed. |

## 5. Why this is the best approach given the tools & the POC

1. **RAG grounding over fine-tuning.** Bid templates and clauses change; RAG keeps drafts current,
   **cites sources**, and prevents hallucinated scope or numbers — with no training cost or stale baked-in
   knowledge. Fine-tuning would be slower, costlier, un-citable, and immediately out of date. ✔
2. **Two scoped libraries over one.** A small clean exemplar set yields consistent house-style SOWs; a
   broad set yields good Q&A. One mixed library degrades both. ✔
3. **Human-in-the-loop over full automation.** Commercial and legal exposure makes auto-issuing
   irresponsible. The approval flow *is* the value (and the demo's credibility moment), not a limitation. ✔
4. **Low-code platform over a custom application.** For a 4-week POC on an existing M365 tenant,
   Copilot Studio + Power Automate is the fastest, most governable, most maintainable path. A bespoke app
   would add hosting, security, identity and upkeep that the POC does not need. ✔
5. **Supported file types only, with spreadsheet mirroring.** Grounding uses just the formats Copilot
   Studio actually indexes (DOCX/PDF/PPTX/XLSX), and rate-sheet / matrix facts are mirrored into narrative
   DOCX/PDF so answers stay accurate (grounded in verified Microsoft limits). ✔
6. **A runnable reference engine in this repo.** Because the platform pieces are GUI-configured, we built
   a Python engine that mirrors the exact logic so it can be **proven, tested and demoed deterministically
   without burning tenant time or exposing secrets** — de-risking the real build. ✔

## 6. Constraints & non-goals
- POC, not a product · one service type to start · **not** fully automated · **not** a pricing/estimating
  engine · **not** legal advice · no confidential vendor pricing used (the KB is illustrative, synthetic
  where sensitive; prices are left as placeholders).

## 7. How the repository embodies this approach
See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the component/layer mapping, and the top-level
[`README.md`](../README.md) §4 for the reference-engine-vs-production boundary. The build order is in
[`BUILD-RUNBOOK.md`](BUILD-RUNBOOK.md); the manual tenant steps in [`MANUAL-SETUP.md`](MANUAL-SETUP.md).
