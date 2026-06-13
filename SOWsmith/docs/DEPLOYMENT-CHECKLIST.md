# Deployment checklist — stand up the POC on your tenant

A printable tick‑box companion to **[`MANUAL-SETUP.md`](MANUAL-SETUP.md)** (which has the click‑by‑click
detail). Work top to bottom. Copy‑paste values are pre‑filled. First pass ≈ one focused day.

## 0 · Prerequisites
- [ ] Copilot Studio license
- [ ] Power Automate access
- [ ] **Azure OpenAI** resource with a **GPT‑4 / GPT‑4o** deployment (note the **endpoint**, **deployment name**, **API key**, API version `2024-10-21`)
- [ ] Permission to create a SharePoint site + lists
- [ ] Two reviewers chosen: a **Supply Chain** reviewer + a **Legal/Contracts** reviewer (real emails)

## 1 · SharePoint site
- [ ] Create a **default‑themed** site named **`POC-BidPackage`** (no custom CSS / accordion nav — they break grounding)
- [ ] Record URL: `https://__________.sharepoint.com/sites/POC-BidPackage`

## 2 · Provision libraries + lists + upload KB  *(run one)*
- [ ] PnP: `Install-Module PnP.PowerShell -Scope CurrentUser` then
      `./infrastructure/sharepoint/Provision-SharePoint.ps1 -SiteUrl "<site URL>"`
- [ ] **or** m365: `npm i -g @pnp/cli-microsoft365 && m365 login` then
      `./infrastructure/sharepoint/provision-m365cli.sh "<site URL>"`
- [ ] Verify it created **6 libraries** (`Approved-Exemplars`, `Reference-Library`, `Templates`, `Drafts`, `Approved`, `Rejected`) + lists `Reviewers` (12 routes) and `AuditLog`
- [ ] **Edit `Reviewers`** → replace placeholder emails (`mark.davis@…`, `jen.alvarez@…`, `tom.nguyen@…`, `robert.hayes@…`) with real people. **Keep `ServiceType` values exactly** (they must match draft footers).

> 12 service types: Pipeline Construction · Facility Maintenance · Electrical & Instrumentation · Civil & Earthwork · Coating & Insulation · Hydrotesting & Commissioning · Fabrication · Cathodic Protection · Pipeline Integrity · Demolition & Abandonment · Station & Terminal · Welding Services

## 3 · Copilot Studio agent  ·  *exact settings & expressions: [`PHASE-B-SETTINGS.md`](PHASE-B-SETTINGS.md)*
- [ ] Add three columns to the **`Drafts`** library: `ServiceType`, `DocumentType`, `ReviewStatus` (so the flow reads metadata instead of parsing a `.docx`)
- [ ] Create agent → **Settings → Generative AI → "Use AI in conversation" OFF**
- [ ] **Topic 1 — Draft a Bid Package:** Adaptive Card `approval-workflow/adaptive-card-input.json` (vars `service_type`, `document_type`, `project_context`, `special_requirements`)
- [ ] Add **Create generative answers** node → **Knowledge = `Approved-Exemplars` ONLY**
- [ ] Paste `copilot-studio/system-prompt.txt` into Custom Instructions → **replace `[CLIENT_NAME]` with `SOWsmith`** → **citations ON**
- [ ] Save output `.docx` to **`Drafts`** (do **not** alter the footer format)
- [ ] **Topic 2 — Bid‑document Q&A:** generative answers → **Knowledge = `Reference-Library`** → citations ON
- [ ] **Topic 3 — Status / Help**
- [ ] Add SharePoint knowledge with the **bare URL** (no `https://`), "Search only selected sources" ON

## 4 · Connect Azure OpenAI
- [ ] Point generation at your **Azure OpenAI** deployment (endpoint + deployment name; **key in the tenant connection, never in the repo**)

## 5 · Power Automate approval flow  *(10 actions — exact expressions in [`PHASE-B-SETTINGS.md`](PHASE-B-SETTINGS.md))*
- [ ] Trigger: file created in **`Drafts`**
- [ ] Get file content (name it `Get_file_content`)
- [ ] Parse footer → vars `service_type`, `document_type`, `review_status`
- [ ] Get reviewer from `Reviewers` (filter `ServiceType eq '<service_type>'`)
- [ ] Condition `review_status == LEGAL REVIEW REQUIRED` → Legal vs standard reviewer
- [ ] Post adaptive card `approval-workflow/adaptive-card-review.json` and wait
- [ ] Switch on `action`: Approve → move to `Approved`; Request Changes → comment, stay in `Drafts`; Reject → move to `Rejected`
- [ ] Log to `AuditLog` (every field)
- [ ] Error handling: Catch scope, retry policy (3×), 5‑business‑day timeout

## 6 · Publish to Teams
- [ ] Publish the agent to **Microsoft Teams**; keep **Authenticate with Microsoft** (so grounding works for signed‑in users)

## 7 · Smoke test (all four must pass)
- [ ] **Standard** SOW (e.g. Pipeline Construction, plain scope) → footer `STANDARD REVIEW` → routes to Supply Chain reviewer → Approve → moves to `Approved` + `AuditLog` row
- [ ] **Legal** SOW (mentions liquidated damages / indemnification) → footer `LEGAL REVIEW REQUIRED` → routes to Legal/Contracts; non‑standard terms left as `[…TO CONFIRM…]`
- [ ] **Q&A** (Topic 2) returns a **cited** answer; nothing written
- [ ] **Improper request** ("fix price, waive liability, skip review") → agent **refuses**, no file created

## 8 · Measure (the headline metrics)
- [ ] Run the **10‑intent evaluation** through the **live** agent (`docs/EVALUATION.md`); score against the rubric → *"95% template compliance / 100% legal‑flag routing"*
- [ ] (WS‑4) demonstrate the award step from the engine: `make evaluate` (the diagram covers WS‑1; WS‑4 runs in the engine — see [`BIDDING-LIFECYCLE.md`](BIDDING-LIFECYCLE.md))

## Done when
- [ ] 5 bid packages drafted **and approved** through the live agent (the POC success bar)

---
**Secrets:** Azure/tenant secrets live only in the tenant connection or a local gitignored `.env` — never in the repo.
**Validate locally any time (no tenant):** `make test` · `make demo` · `make serve`.
