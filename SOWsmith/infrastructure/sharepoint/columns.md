# SharePoint list schemas

## `Reviewers` (GenericList) — drives Power Automate reviewer routing (action 4)
| Column | Type | Notes |
|---|---|---|
| Title | Text | default column; set = ServiceType for convenience |
| ServiceType | Choice | **must match the `SERVICE TYPE` footer token exactly** (see below) |
| ReviewerEmail | Text* | standard **Supply Chain** reviewer for STANDARD REVIEW drafts |
| LegalReviewerEmail | Text* | **Legal/Contracts** reviewer for LEGAL REVIEW REQUIRED drafts |

\* Seeded as Text for POC robustness. Convert to **Person** once the reviewers exist in the tenant.

**Choice values (the canonical `service_type` tokens):**
`Pipeline Construction, Facility Maintenance, Electrical & Instrumentation, Civil & Earthwork,
Coating & Insulation, Hydrotesting & Commissioning, Fabrication, Cathodic Protection,
Pipeline Integrity, Demolition & Abandonment, Station & Terminal, Welding Services`

## `AuditLog` (GenericList) — written by Power Automate (action 10); read in the demo
| Column | Type |
|---|---|
| Title | Text (default) |
| DraftFileName | Text |
| Author | Text |
| Reviewer | Text |
| Action | Text (`Approve` / `Request Changes` / `Reject` / `ERROR`) |
| ReviewStatus | Text (`STANDARD REVIEW` / `LEGAL REVIEW REQUIRED`) |
| Comments | Multiple lines of text |
| Timestamp | use the built-in **Created** column, or add a Text column if you prefer ISO strings |

## Document libraries (no custom columns required for the POC)
`Approved-Exemplars`, `Reference-Library`, `Templates`, `Drafts`, `Approved`, `Rejected`.
Versioning is on by default; the flow increments the version on approval.
