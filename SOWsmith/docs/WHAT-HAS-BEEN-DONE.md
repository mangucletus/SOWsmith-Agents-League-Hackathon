# What has been done so far

Status of the **Bid Package Generator (SOW/RFP)** POC as built in this repository, plus the review
findings and what remains.

## Done & verified ✅

### 1. Knowledge base (`knowledge-base/`)
- A generator (`generator/_build_knowledge_base.py`) builds **~30 files** of realistic SOWsmith bid content.
- **Approved-Exemplars:** 5 byte-identical gold-standard SOWs across core service types (Pipeline
  Construction, Facility Maintenance, Electrical & Instrumentation, Civil & Earthwork, Hydrotesting).
- **Reference-Library:** 16 files — prior SOWs/RFPs + the **standard clause library** + multi-format
  resources (Bidder Instructions PDF, Bid-Process Overview PPTX, Rate-Sheet Template XLSX). Only the file
  types Copilot Studio's SharePoint source indexes (**DOCX/PDF/PPTX/XLSX**); rate-sheet facts mirrored into DOCX/PDF.
- **Templates:** blank SOW template, standard clause library, bidder response form.
- **Lists:** `Reviewers.xlsx` (12 service-type routes), `AuditLog.xlsx` (schema + sample trail).
- Verified: byte-identical exemplars across libraries; every footer `SERVICE TYPE` matches the Reviewers
  list; every REFERENCES citation resolves; clean text extraction; all grounding files well under limits.

### 2. Reference engine (`agent/`)
- Runnable Python mirroring the whole flow: KB load + retrieval, generation (Azure OpenAI **or**
  deterministic offline mock), footer parse, **content-driven** legal/standard routing, a **deterministic
  validation pass** (zero token cost), **explainable** legal-routing (the matched trigger terms), file
  moves, audit, Q&A — **plus a thin WS-4 (Bid Evaluation & Award) slice** (`bid_eval.py`): deterministic
  bid comparison + explainable award recommendation (lowest compliant, with non-standard-term → Legal
  routing, **Finance‑threshold sign‑off**, **BAFO** suggestion, and draft **award/regret notices**) that
  reuses the legal-trigger routing and approval/audit — **and an OCR ingestion slice** (`ocr.py`,
  digital‑first with optional OCR fallback).
- CLI: `kb`, `ask`, `draft`, `evaluate`, `ingest`, `demo`, `eval`, `serve`, `audit`.
- **45 tests pass** — `test_spine.py` (seven-section structure, footer, standard vs legal routing, refusal,
  end-to-end approve, Q&A), `test_engine.py` (Q&A no-match, footer edges, decide(), full 10-intent eval,
  **path-traversal rejection**, **legal-trigger word boundaries**, **the validator**, **explainable routing**),
  `test_award.py` (**WS-4**: lowest-compliant recommendation, legal routing, no-compliant-bid, outlier-low,
  no invented numbers, Finance threshold, BAFO, draft notices), `test_ocr.py` (digital-first extraction +
  graceful OCR fallback), and `test_webapp.py` (live JSON API: health, kb, ask, draft, review, refusal,
  **/api/evaluate**, static, **traversal → 404**).
- **Security:** `pipeline.decide()` validates the user-supplied `filename` as a bare name inside the
  Drafts library (rejects `/`, `\`, `..`, dotfiles, and out-of-root paths) — closes a path-traversal
  finding from the automated security review. Regression-tested above.

### 3. Web console (`frontend/`)
- Dependency-free HTML/CSS/JS app served by a stdlib Python API (`agent/.../webapp/server.py`).
- Four modes — Ask (Flow A), Draft a bid package (Flow B with reviewer-decision controls),
  **Evaluate & award (WS-4)**, Audit log.
- Verified: all endpoints return correctly (incl. `/api/evaluate`); UI renders the screens.

### 4. Evaluation (`agent/.../evaluation.py`)
- The 10-intent set + rubric (6 standard, 3 legal-flag, 1 refusal). On the mock: 100%
  structure/footer/routing + correct refusal — **labelled as plumbing validation, not the quality metric**
  (which needs the live model).

### 5. Platform artifacts (`copilot-studio/`, `approval-workflow/`)
- `system-prompt.txt` (generated from the engine's canonical prompt), topics + trigger phrases,
  knowledge-scoping guide; the 10-action Power Automate flow spec + both Adaptive Cards.

### 6. Infrastructure (`infrastructure/`)
- SharePoint provisioning in **PnP PowerShell** and **CLI for Microsoft 365**: creates libraries +
  lists, seeds the **12 service-type reviewer routes**, uploads the KB. Plus the list schemas.

### 7. Documentation (`docs/`) + the interactive architecture diagram + this status.

## Review findings (the "check accuracy / fix gaps" pass)
- ✅ `.env` and `.envrc` are gitignored — no secret can be committed. `.env.example` is placeholders only.
- ✅ KB regenerates correctly from the repo root with no stray copy.
- ✅ **Review tier is content-driven** (not per-service-type): `safety.needs_legal_review()` flags
  non-standard commercial/legal terms, so the same service type can route standard or legal — verified by
  eval intents T-01/T-07 (both Pipeline Construction, different tiers).
- ✅ Added `requirements.txt` / `pyproject.toml`; engine runs with no installs via `PYTHONPATH=agent/src`.
- ✅ **Localized to SOWsmith (US):** the whole repo and KB use **US English, USD, and US conventions**, with
  content contextualized to SOWsmith's energy / industrial construction & maintenance, safety-first, field
  workforce — service types (pipeline, facility, E&I, civil, coating, hydrotesting), regulatory references
  (OSHA, DOT, PHMSA), and the clause library all reflect that.

## What remains (manual, on your tenant) ⛳
See **[`MANUAL-SETUP.md`](MANUAL-SETUP.md)**:
1. Create the `POC-BidPackage` SharePoint site and run the provisioning script.
2. Build the Copilot Studio agent (3 topics, knowledge scoping, system prompt).
3. Connect your Azure OpenAI GPT-4 deployment.
4. Build the Power Automate approval flow.
5. Publish to Teams; run the live evaluation for the headline metrics.

These steps are GUI/tenant work that cannot be performed from this repository.
