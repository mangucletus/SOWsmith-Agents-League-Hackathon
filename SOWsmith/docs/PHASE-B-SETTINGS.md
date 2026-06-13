# Phase B — exact settings (Copilot Studio agent + Power Automate flow)

The two hand‑built parts of the tenant build, spelled out so you can copy them. Use this **with**
[`MANUAL-SETUP.md`](MANUAL-SETUP.md) / [`DEPLOYMENT-CHECKLIST.md`](DEPLOYMENT-CHECKLIST.md).

---

## Part 1 — Copilot Studio: Topic 1 "Draft a Bid Package"

### 1a. Collect inputs (Adaptive Card)
Paste [`../approval-workflow/adaptive-card-input.json`](../approval-workflow/adaptive-card-input.json). It
returns four topic variables: `service_type`, `document_type`, `project_context`, `special_requirements`.

### 1b. "Create generative answers" node — exact settings
| Setting | Value |
|---|---|
| Data source | **SharePoint**, "Search only selected sources" = **ON** |
| URL | `<tenant>.sharepoint.com/sites/POC-BidPackage/Approved-Exemplars` (bare URL, **no `https://`**) |
| Input | the card variables + `project_context` |
| Custom instructions | paste [`../copilot-studio/system-prompt.txt`](../copilot-studio/system-prompt.txt), replace `[CLIENT_NAME]` → `SOWsmith` |
| Citations | **ON** |
| "Use AI in conversation" (agent Settings → Generative AI) | **OFF** (generation is wired here, not globally) |

### 1c. Save the draft **and set columns** (the important bit)
The model ends every draft with a footer (`SERVICE TYPE`, `DOCUMENT TYPE`, `REVIEW STATUS`). **Do not rely
on parsing that footer back out of a saved `.docx`** — a Word file's content is binary, so string
functions can't read it. Instead, **set the values as SharePoint columns when you save the file**:

1. Save the node output as a `.docx` (or `.md`) into the **`Drafts`** library.
2. Set these Drafts columns from the variables you already have: **`ServiceType`** = `service_type`,
   **`DocumentType`** = `document_type`, and **`ReviewStatus`** = the review status from the draft
   (the prompt prints `STANDARD REVIEW` or `LEGAL REVIEW REQUIRED`; capture it into a variable, e.g. with
   `if(contains(Topic.GenerativeAnswer, "LEGAL REVIEW REQUIRED"), "LEGAL REVIEW REQUIRED", "STANDARD REVIEW")`).

Then Power Automate reads those columns directly — no fragile text parsing. (Add the three columns to the
Drafts library; the provisioning script sets them on `Reviewers`/`AuditLog`, not `Drafts`, so add them here.)

> **Topic 2 (Bid‑document Q&A)** and **Topic 3 (Status/Help)**: see [`../copilot-studio/topics-and-trigger-phrases.md`](../copilot-studio/topics-and-trigger-phrases.md). Topic 2's only difference: Knowledge = **`Reference-Library`**.

---

## Part 2 — Power Automate: the 10 actions, with exact expressions

Full narrative in [`../approval-workflow/flow-definition.md`](../approval-workflow/flow-definition.md).

| # | Action (connector) | Exact config / expression |
|---|---|---|
| 1 | **When a file is created (properties only)** (SharePoint) | Site `POC-BidPackage` · Library **`Drafts`** |
| 2 | Read the metadata | If you set columns in 1c, just use the trigger fields: `triggerOutputs()?['body/ServiceType']`, `triggerOutputs()?['body/DocumentType']`, `triggerOutputs()?['body/ReviewStatus']` — **no parsing needed** |
| 3 | **Get items** (SharePoint) on `Reviewers` | Filter Query: `ServiceType eq '@{triggerOutputs()?['body/ServiceType']}'` · Top Count `1` |
| 4 | **Condition** (Control) | `@{triggerOutputs()?['body/ReviewStatus']}` **is equal to** `LEGAL REVIEW REQUIRED` |
| 5 | Set `reviewerEmail` (Variables) | **If yes:** `first(outputs('Get_items')?['body/value'])?['LegalReviewerEmail']` · **If no:** `…?['ReviewerEmail']` |
| 6 | **Post adaptive card and wait for a response** (Teams) | Recipient = `reviewerEmail` · Card = [`../approval-workflow/adaptive-card-review.json`](../approval-workflow/adaptive-card-review.json). Set the card's variables first: `service_type`, `document_type`, `review_status`. For the preview, use the column/excerpt (don't `substring` a `.docx` body). |
| 7 | **Switch** (Control) | On `body('Post_adaptive_card_and_wait_for_a_response')?['data/action']` → cases `Approve`, `RequestChanges`, `Reject` |
| 8a | Approve → **Move file** (SharePoint) | Destination = **`Approved`**; then increment a version column |
| 8b | RequestChanges → **Post message** (Teams) | To the author with the comments; **leave the file in `Drafts`** |
| 8c | Reject → **Move file** (SharePoint) | Destination = **`Rejected`**; notify the author |
| 9 | **Create item** (SharePoint) on `AuditLog` | `DraftFileName`, `Author`, `Reviewer` = `reviewerEmail`, `Action` = the switch case, `ReviewStatus`, `Comments` = the reviewer's comment |
| 10 | **Error handling** | A final **Scope** with *Configure run after* = *has failed / timed out* → alert + write `AuditLog` with `Action = "ERROR"`. Set a **retry policy** (3×, exponential) on each SharePoint/Teams action and a **5‑business‑day timeout** on action 6. |

### Fallback only — if you saved the draft as **text** (`.md`/`.txt`), not `.docx`
Add a **Get file content** action, then a **Compose** per field (newline = `decodeUriComponent('%0A')`):
```
service_type   = trim(split(split(body('Get_file_content'),'SERVICE TYPE:')?[1],   decodeUriComponent('%0A'))?[0])
document_type  = trim(split(split(body('Get_file_content'),'DOCUMENT TYPE:')?[1],  decodeUriComponent('%0A'))?[0])
review_status  = trim(split(split(body('Get_file_content'),'REVIEW STATUS:')?[1],  decodeUriComponent('%0A'))?[0])
```
These string functions **only work on text** — for `.docx` use the column approach above.

---
**Tip:** the runnable engine mirrors all of this. `make demo` shows generate → route → approve → audit, and
`bidpkg draft --decision Approve` exercises the exact branch logic before you build the flow.
