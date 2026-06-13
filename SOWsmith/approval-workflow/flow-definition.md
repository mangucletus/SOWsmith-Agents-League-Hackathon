# Power Automate — Approval flow definition

Build this in **Power Automate** (`flow.microsoft.com`), **not** Copilot Studio. It triggers when
the agent saves a draft into the SharePoint **`Drafts`** library and routes it for human approval.
The reference engine in [`../agent/`](../agent/) (`approval.py`, `pipeline.py`, `audit.py`) mirrors
these actions so you can test the logic before building the flow.

## Prerequisites (created by [`../infrastructure/sharepoint/`](../infrastructure/sharepoint/))
- `Drafts`, `Approved`, `Rejected` document libraries in the `POC-BidPackage` site.
- `Reviewers` list: `ServiceType` (choice), `ReviewerEmail` (person), `LegalReviewerEmail` (person).
- `AuditLog` list: `DraftFileName`, `Author`, `Reviewer`, `Action`, `Timestamp`, `ReviewStatus`, `Comments`.
- Teams connector enabled for Power Automate.

## Flow structure (10 actions)

| # | Action | Connector | Configuration |
|---|---|---|---|
| 1 | **Trigger:** When a file is created (properties only) | SharePoint | Site `POC-BidPackage` · Library `Drafts` · new files only |
| 2 | Get file content | SharePoint | File Identifier = `Identifier` from trigger |
| 3 | Parse `service_type` + `review_status` from the footer | Compose / Data Ops | `indexOf()` + `substring()` over the VERSION FOOTER → store as variables |
| 4 | Get reviewer from `Reviewers` | SharePoint | Get items · Filter `ServiceType eq '<service_type>'` · Top 1 |
| 5 | **Condition:** `review_status` = `LEGAL REVIEW REQUIRED` | Control | branch on the parsed variable |
| 6a | If yes → primary reviewer = `LegalReviewerEmail` | Variables | optionally CC the standard reviewer |
| 6b | If no → primary reviewer = `ReviewerEmail` | Variables | standard reviewer |
| 7 | **Post adaptive card and wait for a response** | Teams | card = [`adaptive-card-review.json`](adaptive-card-review.json) · update message after response |
| 8 | **Switch** on response `action`: Approve / RequestChanges / Reject | Control | one branch each |
| 9a | Approve → Move file to `Approved` | SharePoint | then increment version metadata |
| 9b | Request Changes → post comments to author | Teams | leave file in `Drafts` |
| 9c | Reject → Move file to `Rejected`; notify author | SharePoint + Teams | author may resubmit |
| 10 | Log the action to `AuditLog` | SharePoint | capture every field (this is what makes it auditable) |

## Error handling (add to every flow)
- Final **"Catch" scope** with **run-after** = failed/timed-out → alert (don't die silently).
- **Retry policy** on every SharePoint/Teams action: 3 retries, exponential backoff.
- **Time-out** the approval wait at **5 business days**; on timeout escalate to a second reviewer.
- Log failures to `AuditLog` with `Action = "ERROR"`.

## The footer contract
The agent ends every draft with this block (parsed by action 3 — do not change its format):

```
---
VERSION: v0.1 DRAFT
DATE: 2026-06-03
SERVICE TYPE: Pipeline Construction
DOCUMENT TYPE: SOW
REVIEW STATUS: STANDARD REVIEW
---
```
