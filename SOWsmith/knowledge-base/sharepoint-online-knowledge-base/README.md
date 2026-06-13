# SharePoint Online Knowledge Base — Bid Package Generator (SOW/RFP)

This folder is the **knowledge base** the Bid Package Agent grounds on. Upload it to a SharePoint
Online site (recommended site name **`POC-BidPackage`**) and wire each library as described below.

> **Why two grounding libraries?** `Approved-Exemplars` (5 gold-standard prior SOWs) is what
> the **generator (Flow B)** copies house style and structure from. `Reference-Library` (the broad set
> of prior bid documents + the clause library) is what **Bid-document Q&A (Flow A)** grounds in. Keep
> them separate — mixing them dilutes draft quality.

## Folder map

| Folder | Role | Wire it to |
|---|---|---|
| `Approved-Exemplars/` | 5 gold-standard SOWs — the generator's style + factual anchor | Topic 1 *Draft a Bid Package* → Generative Answers knowledge (this library **only**) |
| `Reference-Library/` | broad corpus (13 bid docs + clause library + resources) | Topic 2 *Bid-document Q&A* → knowledge source |
| `Templates/` | SOW/RFP template, Standard Bid Clause Library, Bidder Response Form | "Get official templates" path |
| `Lists/` | `Reviewers.xlsx`, `AuditLog.xlsx` — import as **SharePoint lists** | Power Automate actions 4 & 10 |
| `Drafts/` `Approved/` `Rejected/` | output libraries — start empty | Power Automate trigger + destinations |

## `service_type` tokens (must match exactly)
Every document's footer `SERVICE TYPE:` value matches a row in `Lists/Reviewers.xlsx` (`ServiceType`).
Power Automate looks up the reviewer with `ServiceType eq '<token>'`. Tokens:
Cathodic Protection, Civil & Earthwork, Coating & Insulation, Demolition & Abandonment, Electrical & Instrumentation, Fabrication, Facility Maintenance, Hydrotesting & Commissioning, Pipeline Construction, Pipeline Integrity, Station & Terminal, Welding Services.

> **Review tier is content-driven:** a package is flagged **LEGAL REVIEW REQUIRED** when it contains
> non-standard commercial/legal terms (liquidated damages, indemnification, bonding, retainage,
> non-standard payment terms) — routed to Legal/Contracts. Otherwise **STANDARD REVIEW** (Supply Chain).

## Approved-Exemplars (feeds the generator — Flow B)

| Service type | Title | Doc | Version | File |
|---|---|---|---|---|
| Pipeline Construction | SOWsmith Pipeline Construction — Statement of Work (Exemplar) | SOW | v2.1 | `Pipeline-Construction-SOW_v2.1_2026-01-15.docx` |
| Facility Maintenance | SOWsmith Facility Maintenance — Statement of Work (Exemplar) | SOW | v1.3 | `Facility-Maintenance-SOW_v1.3_2025-11-03.docx` |
| Electrical & Instrumentation | SOWsmith Electrical & Instrumentation — Statement of Work (Exemplar) | SOW | v1.2 | `Electrical-Instrumentation-SOW_v1.2_2025-09-20.docx` |
| Civil & Earthwork | SOWsmith Civil & Earthwork — Statement of Work (Exemplar) | SOW | v2.0 | `Civil-Earthwork-SOW_v2.0_2026-02-10.docx` |
| Coating & Insulation | SOWsmith Coating & Insulation — Statement of Work (Exemplar) | SOW | v1.1 | `Coating-Insulation-SOW_v1.1_2025-12-05.docx` |

## Reference-Library (feeds Bid-document Q&A — Flow A)

| Service type | Title | Doc | Review status | File |
|---|---|---|---|---|
| Pipeline Construction | SOWsmith Pipeline Construction — Statement of Work (Exemplar) | SOW | STANDARD REVIEW | `Pipeline-Construction-SOW_v2.1_2026-01-15.docx` |
| Facility Maintenance | SOWsmith Facility Maintenance — Statement of Work (Exemplar) | SOW | STANDARD REVIEW | `Facility-Maintenance-SOW_v1.3_2025-11-03.docx` |
| Electrical & Instrumentation | SOWsmith Electrical & Instrumentation — Statement of Work (Exemplar) | SOW | STANDARD REVIEW | `Electrical-Instrumentation-SOW_v1.2_2025-09-20.docx` |
| Civil & Earthwork | SOWsmith Civil & Earthwork — Statement of Work (Exemplar) | SOW | STANDARD REVIEW | `Civil-Earthwork-SOW_v2.0_2026-02-10.docx` |
| Coating & Insulation | SOWsmith Coating & Insulation — Statement of Work (Exemplar) | SOW | STANDARD REVIEW | `Coating-Insulation-SOW_v1.1_2025-12-05.docx` |
| Hydrotesting & Commissioning | SOWsmith Hydrotesting & Commissioning — Statement of Work | SOW | STANDARD REVIEW | `Hydrotesting-Commissioning-SOW_v1.4_2025-07-18.docx` |
| Fabrication | SOWsmith Shop Fabrication — Statement of Work | SOW | STANDARD REVIEW | `Fabrication-SOW_v1.0_2026-01-09.docx` |
| Cathodic Protection | SOWsmith Cathodic Protection — Statement of Work | SOW | STANDARD REVIEW | `Cathodic-Protection-SOW_v1.2_2025-10-12.docx` |
| Pipeline Integrity | SOWsmith Pipeline Integrity & Inspection — Statement of Work | SOW | STANDARD REVIEW | `Pipeline-Integrity-Inspection-SOW_v1.1_2025-08-15.docx` |
| Demolition & Abandonment | SOWsmith Demolition & Abandonment — Statement of Work | SOW | STANDARD REVIEW | `Demolition-Abandonment-SOW_v1.0_2025-12-01.docx` |
| Station & Terminal | SOWsmith Station & Terminal Construction — Statement of Work | SOW | STANDARD REVIEW | `Station-Terminal-Construction-SOW_v1.5_2025-11-28.docx` |
| Welding Services | SOWsmith Welding Services — Statement of Work | SOW | STANDARD REVIEW | `Welding-Services-SOW_v2.3_2025-09-05.docx` |
| Facility Maintenance | SOWsmith Facility Maintenance — Request for Proposal (Example) | RFP | LEGAL REVIEW REQUIRED | `Facility-Maintenance-RFP_v1.0_2026-01-20.docx` |

## Multi-format resources

| Type | File | What it is |
|---|---|---|
| PDF | `Bidder-Instructions_v1.0_2026-01-01.pdf` | How bidders respond to a SOWsmith bid package |
| PPTX | `Bid-Process-Overview_v1.0_2026-01-02.pptx` | Overview of the bid-package process for buyers |
| XLSX | `Rate-Sheet-Template_v1.0.xlsx` | Blank bidder rate sheet (pricing entered by bidders, not by SOWsmith) |

## Upload checklist (SharePoint Online + Copilot Studio)
1. Create the site `POC-BidPackage` (default-themed; custom CSS / accordion nav can break grounding).
2. Create document libraries `Approved-Exemplars`, `Reference-Library`, `Templates`, `Drafts`,
   `Approved`, `Rejected` and upload the matching folder contents.
3. Create the lists `Reviewers` and `AuditLog` (Lists → "From Excel"). `ServiceType` = Choice.
4. In Copilot Studio, add SharePoint knowledge using the **bare URL** (no `https://`). Scope Topic 1 to
   `Approved-Exemplars` only and Topic 2 to `Reference-Library`.
5. **File-size limit:** grounding files must be **< 7 MB** without an M365 Copilot license (< 200 MB with
   Copilot + Work IQ). These files are tiny; verify the tenant setting with the admin.

_Generated by `_build_knowledge_base.py`. Re-run to regenerate. Organization: SOWsmith. US English._
