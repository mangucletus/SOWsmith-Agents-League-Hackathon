# Presentation Brief — Bid Package Generator (SOW/RFP) for SOWsmith

**Use case:** Supply Chain · Bid Package Generation · **Platform:** Microsoft Copilot Studio · Azure OpenAI (GPT-4) · SharePoint Online · Power Automate · Microsoft Teams.
Present with the interactive diagram: **`docs/assets/Bid-Package-Generator_Architecture_Diagram.html`** (open in a browser).

**The sample company:** **SOWsmith** — a *fictional* energy & industrial services contractor (pipelines,
facilities, terminals, gas processing, refining, renewables) used for this POC. Its Supply Chain team
issues the SOWs/RFPs this agent generates. **All data is synthetic — no real company information.**
See [`COMPANY-CONTEXT.md`](COMPANY-CONTEXT.md).

> **Executive summary (30 seconds)**
> - **What it is:** an AI assistant in Microsoft Teams that drafts SOWsmith's bid packages (SOW/RFP) and answers questions about prior ones.
> - **The problem:** producing bid packages is slow, inconsistent, and risky — vague scope, missed exclusions, and un-reviewed commercial/legal terms.
> - **What it does:** turns a short project brief into a grounded, house-style **seven-section SOW/RFP in minutes**, auto-routes non-standard commercial terms to **Legal/Contracts**, and sends **every draft through human approval** with a full audit trail.

---

## 1. In one sentence
An AI assistant, inside Microsoft Teams, that turns a buyer's rough project notes into a polished,
house-style **Statement of Work (SOW)** or **Request for Proposal (RFP)** — **grounded in SOWsmith's
own approved bid packages** — and routes **every draft through human approval**, while also answering
questions about prior packages and the clause library.

## 2. The problem
- Producing a bid package is **slow** — buyers copy-paste from old projects and rebuild structure by hand.
- Output is **inconsistent** (scope, exclusions, terminology drift by author and project).
- It is **risky**: vague scope and missing exclusions cause bad bids, scope disputes, and rework; and
  non-standard commercial/legal terms (liquidated damages, indemnification, bonding) need disciplined
  Legal/Contracts review.
- Prior bid knowledge is **siloed** — buyers can't quickly find what a past SOW or standard clause said.

## 3. The solution — one agent, the bidding lifecycle
- **Flow A · Bid-document Q&A (read):** ask a plain-English question → a grounded, **cited** answer from
  prior packages and the clause library. Nothing changes.
- **Flow B · Draft & approve (write) — WS-1:** rough notes → a **seven-section SOW/RFP** grounded in 3–5
  gold-standard exemplars → saved to a Drafts library → **Power Automate routes it for human approval**
  → Approved / Rejected, with a full audit trail. Packages with **non-standard commercial/legal terms
  are auto-flagged and routed to Legal/Contracts**; improper requests (invent prices, waive liability,
  bypass review) are **refused**.
- **Bid Evaluation & Award — WS-4 (thin slice):** once bidders respond, the agent **normalizes the bids,
  compares them, and recommends an award** — *deterministically ($0 tokens), with explainable reasons and
  risks*. It recommends the lowest compliant bid **but flags** non-standard terms (→ Legal) and scope gaps;
  **a human approves the award** (the agent never auto-awards). This closes the lifecycle: **generate →
  receive responses → evaluate → recommend award.**

## 4. How it works — narrating the architecture diagram (left → right)
1. **Buyer → Chat Interface (Microsoft Teams):** submits the request, or asks a question. (Teams is the
   default channel; the same agent can also run in web chat.)
2. **Bid Package Agent (Microsoft Copilot Studio):** detects intent and routes to three topics —
   T1 Draft a Bid Package, T2 Bid-document Q&A, T3 Status/Help.
3. **Support Layer:** Copilot Studio orchestrates; **Azure OpenAI (GPT-4)** does the generation, governed
   by a production system prompt with **safety rails**.
4. **Knowledge Base (SharePoint) — the key design choice:** two scoped libraries — **Approved-Exemplars**
   (feeds the *generator*) and **Reference-Library + clause library** (feeds *Q&A*). Plus output libraries
   (Drafts/Approved/Rejected) and governance lists (Reviewers, AuditLog).
5. **Draft → Power Automate → Stakeholders Review (in Teams):** the draft triggers an approval flow; a
   human chooses Approve / Request changes / Reject. Approved packages are issued and **every action is logged**.

> **Two ideas to land:** *"Grounded, not guessing"* (it copies our own approved SOWs and cites sources)
> and *"a human approves every package"* (the agent drafts; people decide; non-standard terms go to Legal).

## 5. The tools — and why each fits
| Tool | Role | Why |
|---|---|---|
| Microsoft Copilot Studio | The agent: topics, routing, Teams delivery | Low-code, native SharePoint grounding — no custom app to build/host |
| Azure OpenAI (GPT-4) | Drafting & reasoning | Enterprise GPT-4 **inside the tenant** — bid data stays in Microsoft 365 |
| SharePoint Online | Knowledge base + output store + audit | Already where bid documents live; native grounding, versioning, permissions |
| Power Automate | Approval routing + audit log | Native workflow + Teams approval cards — no backend to run |
| Microsoft Teams | Where buyers work | Familiar surface; single sign-on; rich approval cards |

## 6. What's been built (status)
- A realistic **SharePoint knowledge base** (5 gold-standard SOW exemplars + a broad set of prior bid
  documents, clause library, SOW/RFP template, bidder form, and a rate-sheet template).
- A **runnable reference implementation + web console** proving the whole flow without a live tenant
  (generate → footer → reviewer routing → **deterministic validation** → approve → audit), with an
  automated test suite (**45 tests pass**, including the WS-4 bid-evaluation slice).
- All **platform artifacts** (system prompt, Adaptive Cards, the 10-step Power Automate flow spec) and
  **SharePoint provisioning scripts**, plus documentation.
- **Remaining:** the manual tenant build (agent + flow in their GUIs, Azure OpenAI, publish to Teams) —
  captured step-by-step in `docs/MANUAL-SETUP.md`.

## 7. Target outcomes (POC success measures)
- Turnaround **days → ~2 hours** · **≥ 95%** template compliance · **≤ 2** revision rounds ·
  **100%** correct routing of non-standard terms to Legal/Contracts · **5 packages drafted and approved**.

## 8. Live demo / talk track (~5 minutes — all on the interactive diagram)
All six steps have a **"Run a flow"** button on the **interactive diagram** (the route breadcrumb narrates
each step; the speed slider controls pace; hover any box for detail). WS‑4 also runs in the terminal
(`make evaluate`) and the web console (the *Evaluate & award* tab):
1. **Draft & approve a bid package** *(diagram)* — the headline: notes → grounded SOW → human approval → issued.
2. **Ask a bid-document question** *(diagram)* — the read path; point out the citations.
3. **Reviewer decision** *(diagram)* — Approve / Request changes / Reject, all logged.
4. **Contracts-sensitive path** *(diagram)* — a package with liquidated damages auto-routing to Legal/Contracts.
5. **Improper request** *(diagram)* — the agent refuses (invent price / waive liability / bypass review); responsible-AI moment.
6. **Evaluate & recommend award (WS-4)** *(diagram · terminal · console)* — click the **Evaluate & award (WS‑4)** flow on the diagram (or run **`make evaluate`**, or the *Evaluate & award* tab in `make serve`): the engine ranks the bidder responses, recommends the lowest compliant bid, **flags non-standard terms (→ Legal), Finance sign-off, and a scope gap**, and leaves the award to a human. Closes the lifecycle. *(See [`examples/sample-AWARD-RECOMMENDATION.md`](examples/sample-AWARD-RECOMMENDATION.md).)*

Close on: *"Grounded in our own approved packages, a human approves every one, days become hours, and
non-standard commercial terms are routed to Legal automatically."*

## 9. Addressing the review feedback (determinism · cost · hallucination · explainability)
Built directly in response to the team review:
- **Deterministic by default; cost-aware.** The seven-section structure, the footer, the reviewer routing
  and a full **validation pass are deterministic code — $0 tokens and no hallucination**. The LLM is used
  only for the narrative prose (**one call per draft**); re-running the checks/structure costs nothing.
  *(You pay hosting; token cost is incurred only on that single generation call.)*
- **Anti-hallucination guardrails (the "Linus" failure mode).** The system prompt now forbids renaming or
  editorializing about system/asset names — *"carry domain terms through verbatim; add no ungrounded
  sentence."* A **deterministic validator** then scans every draft for **invented dollar amounts** and
  **speculative inserted sentences** (e.g. *"…looks like a person's name, let the client confirm"*) and
  surfaces them to the reviewer. And **a human approves every package**, line by line.
- **Explainable decisions (the "feature importance" ask).** Every Q&A answer is **cited**; every LEGAL
  flag states **why** — e.g. *"flagged: liquidated damages, indemnification/indemnity, retainage"* —
  recorded in the audit log. A reviewer can always see how the agent reached its decision.
- **An extensible building block.** Bid Package Generation is one node in SOWsmith's broader Supply-Chain
  agent **ecosystem**; the same grounded-generation + human-approval pattern extends to adjacent topics.
  **OCR / character recognition** is a natural next step — to ingest scanned or legacy PDF bid documents
  into the knowledge base. See the [`ROADMAP.md`](ROADMAP.md) for the reusable substrate, the OCR plug-in
  point, and the candidate adjacent nodes.

---
*Companion docs: `README.md` (overview + boundary), `docs/PROBLEM-AND-APPROACH.md` (why this approach),
`docs/BIDDING-LIFECYCLE.md` (the end-to-end WS‑1 → WS‑4 lifecycle, stage by stage),
`docs/ARCHITECTURE.md` (components & flows), `docs/MANUAL-SETUP.md` (what's left to configure).*
