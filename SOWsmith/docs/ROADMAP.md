# Roadmap & extensibility — SOWsmith's Supply-Chain agent ecosystem

This POC (**Bid Package Generation**, WS-1) is deliberately built as **one node in a composable ecosystem**,
not a one-off — and now includes a **thin WS-4 (Bid Evaluation & Award) slice** so it tells the full
*"generate → receive responses → evaluate → recommend award"* bidding‑lifecycle story end-to-end. As the team
observed, the Supply-Chain topics *"build on top of each other"* and form *"an entire ecosystem"* where
*"if I do this, I'll need that"* — so the value is a **reusable substrate** each new node inherits, plus a
clear sequence for adding nodes.

## 1. The reusable substrate (built once, here)
Everything below already exists in this POC and is **shared infrastructure** for any future Supply-Chain agent:

| Capability | Where it lives now | Reused by every future node |
|---|---|---|
| Grounded generation (RAG over a scoped SharePoint library) | Copilot Studio Generative Answers + `knowledge_base.py` | ✔ |
| **Two-library scoping** (gold exemplars vs. broad reference) | `Approved-Exemplars` / `Reference-Library` | ✔ |
| Human-in-the-loop **approval + conditional legal routing** | Power Automate + `approval.py`/`pipeline.py` | ✔ |
| Machine-readable **footer contract** + **audit trail** | `footer.py`, `AuditLog` | ✔ |
| **Deterministic validation**, **explainable routing**, **refusal** guardrails | `validator.py`, `safety.py` | ✔ |

Building these once is what makes the rest of the ecosystem incremental rather than a from-scratch effort each time.

## 2. Adjacent nodes it composes with (candidate next topics)
Natural Supply-Chain extensions that reuse the substrate above (each is a candidate, not a commitment):

| Candidate node | What it does | What it reuses |
|---|---|---|
| **Bid-document Q&A** | Ask about prior packages & the clause library | *Already in this POC (Flow A)* |
| **Clause-library management** | Draft/curate standard clauses; answer "what's our standard X clause?" | grounding + approval + audit |
| **Bid Evaluation & Award (WS-4)** | Normalize bidder responses, compare, recommend award; flag non-standard terms & scope gaps | ✅ **thin slice built** — reuses the legal-trigger logic + approval/audit (`bid_eval.py`) |
| **Vendor / subcontractor prequal Q&A** | Answer questions from prequal packets and vendor records | grounding + citations |
| **PO / spec / drawing Q&A** | Ground answers in purchase orders, specs and project drawings | grounding + **OCR ingestion (§3)** |

## 3. Near-term capability: OCR / document character recognition  ·  ✅ slice built
Flagged as a priority of interest in the review. Many prior bids, vendor submittals, redlines and drawings
arrive as **scanned/image PDFs** that the current text path cannot read.

- **Built (slice):** [`agent/src/bid_package_agent/ocr.py`](../agent/src/bid_package_agent/ocr.py) +
  the **`bidpkg ingest <file>`** command — a **digital‑first** extractor with an **OCR fallback** and a
  graceful "no OCR backend" message. Enable real OCR with `pip install -e ".[ocr]"` (Tesseract) or wire
  Azure AI Document Intelligence in production. Grounding‑only; tested in `test_ocr.py`.
- **Why it matters:** today the engine extracts text from *digital* DOCX/PDF/PPTX/XLSX (`textextract.py`,
  `pypdf`). Image-only/scanned documents yield no text, so they can't ground answers or drafts.
- **Next:** wire ingested text into the `Reference-Library` index (currently staged to `var/run/ingested/`).
- **How it plugs in (low-risk):** text extraction is already isolated in
  [`agent/src/bid_package_agent/textextract.py`](../agent/src/bid_package_agent/textextract.py); OCR becomes
  **one more extractor behind the same interface** — no change to retrieval, generation, routing or approval.
  - **Production:** **Azure AI Document Intelligence** (runs in-tenant; strong on tables/forms — ideal for
    rate sheets and bid forms).
  - **Local/dev:** **Tesseract** (`pytesseract`) for an offline path.
- **Guardrail:** OCR output is noisy, so it **feeds grounding only — never unreviewed generation**. The same
  human approval, deterministic validation and citation rules still apply. (This keeps it consistent with the
  team's "don't trust the model 100%" stance: OCR widens what we can *ground on*, it doesn't bypass review.)

## 4. Sequencing (the "if I do this, I'll need that" point)
1. **Substrate first** — *done* (this POC): grounding, scoping, approval, audit, guardrails — **plus a thin
   WS-4 (Bid Evaluation & Award) slice**, so the LLM/RAG spine of the bidding lifecycle (WS-1 → WS-4) is demoable today.
2. **Widen ingestion** — OCR (§3), so scanned/legacy bid documents become groundable.
3. **Add the heavier adjacent nodes** — WS-2 (BOM takeoffs, **computer vision**, shared with Estimating) and
   WS-3 (Bidder Sourcing, **agentic + scoring**) are different disciplines / separate owners; tackle them as
   their own tracks. Other §2 nodes reuse the substrate; ship and demo one before starting the next.
4. **Compose** — shared Reviewers/AuditLog and a common footer contract let the nodes interoperate as one
   Supply-Chain assistant in Teams.

> **One-line framing for the lead:** *"We built the reusable substrate (grounding + approval + audit +
> guardrails) on the bid-package node; OCR ingestion and the adjacent Supply-Chain topics now plug into it
> incrementally — that's the ecosystem."*
