# Manual setup — the complete, do-exactly-this deployment guide

Everything in this repo is ready. The remaining work is on **your Microsoft 365 tenant** — the
Copilot Studio agent and the Power Automate flow are built in their GUIs and **cannot be deployed from
code**. This guide is the ordered, click-by-click path. Do the steps in order.

> **Legend:**  🧑‍💻 by hand in a portal  ·  ⌨️ run a provided script  ·  ✅ already in this repo

---

## ⚡ Fast path (the whole thing at a glance)

| # | Step | How | Time |
|---|---|---|---|
| 0 | Confirm licenses & pick 2 reviewers | 🧑‍💻 | 15 min |
| 1 | Create the `POC-BidPackage` SharePoint site (default theme) | 🧑‍💻 | 10 min |
| 2 | Provision libraries/lists + upload the KB | ⌨️ one script | 10 min |
| 3 | Build the Copilot Studio agent (3 topics, scoping, prompt) | 🧑‍💻 | ~2–3 hr |
| 4 | Point generation at Azure OpenAI | 🧑‍💻 | 15 min |
| 5 | Build the Power Automate approval flow (10 actions) | 🧑‍💻 | ~2–3 hr |
| 6 | Publish to Teams | 🧑‍💻 | 15 min |
| 7 | Smoke test + run the evaluation | 🧑‍💻 + ✅ | 1 hr |

**First end-to-end pass ≈ one focused day.** Want to *see it working first, with zero setup?* Run the
local mirror now: `make demo` (or `make serve` for the web console) — see the last section.

---

## 0. Prerequisites  🧑‍💻
- **Licenses/access:** a **Copilot Studio** license, **Power Automate**, an **Azure OpenAI** resource with
  a **GPT-4 / GPT-4o** deployment, and permission to create SharePoint sites + lists.
- **M365 Copilot license?** Confirm with your tenant admin. It raises the SharePoint grounding file-size
  limit from **7 MB → 200 MB**. Our KB files are tiny (well under 7 MB), so this is *not* a blocker — just
  good to know.
- **Pick two reviewers now:** one standard **Supply Chain** reviewer and one **Legal/Contracts** reviewer.
  Book a recurring 30-min review slot so approvals don't stall the demo.

## 1. Create the SharePoint site  🧑‍💻
- Create a **default-themed** Team or Communication site named **`POC-BidPackage`**.
  ⚠️ **Avoid custom CSS and accordion navigation** — they break Copilot's RAG grounding.
- Note the URL: `https://<tenant>.sharepoint.com/sites/POC-BidPackage`.

## 2. Provision libraries, lists & upload the KB  ⌨️
Run **one** of these from your machine (authenticated to the tenant), from the repo root:

```powershell
# Option A — PnP PowerShell (recommended on Windows)
Install-Module PnP.PowerShell -Scope CurrentUser
./infrastructure/sharepoint/Provision-SharePoint.ps1 -SiteUrl "https://<tenant>.sharepoint.com/sites/POC-BidPackage"
```
```bash
# Option B — CLI for Microsoft 365 (cross-platform)
npm i -g @pnp/cli-microsoft365 && m365 login
./infrastructure/sharepoint/provision-m365cli.sh "https://<tenant>.sharepoint.com/sites/POC-BidPackage"
```

**This creates and seeds, idempotently (safe to re-run):**
- **6 document libraries:** `Approved-Exemplars`, `Reference-Library`, `Templates`, `Drafts`, `Approved`, `Rejected`
- **`Reviewers` list** — columns `ServiceType` (Choice, 12 values), `ReviewerEmail` (Text), `LegalReviewerEmail` (Text), **seeded with 12 routes**
- **`AuditLog` list** — columns `DraftFileName`, `Author`, `Reviewer`, `Action`, `ReviewStatus`, `Comments`
- **Uploads** the KB into `Approved-Exemplars`, `Reference-Library`, `Templates`

Then, by hand:
- 🧑‍💻 **Edit the `Reviewers` list** → replace the seeded placeholder emails (`mark.davis@…`,
  `jen.alvarez@…`, `tom.nguyen@…`, and the Legal reviewer `robert.hayes@…`) with your **real** reviewers.
  **Keep the `ServiceType` values exactly as they are** — they must match the draft footers character-for-character.

## 3. Build the Copilot Studio agent  🧑‍💻
At [copilotstudio.microsoft.com](https://copilotstudio.microsoft.com). Reference:
[`../copilot-studio/topics-and-trigger-phrases.md`](../copilot-studio/topics-and-trigger-phrases.md) and
[`../copilot-studio/knowledge-scoping.md`](../copilot-studio/knowledge-scoping.md).

**3.0** Create a new agent (name it e.g. *Bid Package Agent*). **Settings → Generative AI → turn
**“Use AI in conversation” OFF**.** (Generation is wired manually inside the topics so *we* control grounding.)

**3.1 — Topic 1 · Draft a Bid Package (Flow B, the generator)**
1. **Trigger phrases:** `draft a bid package`, `create an SOW`, `new SOW for …`, `write an RFP`, `draft a scope of work for …`
2. **Collect inputs** with an Adaptive Card — paste [`../approval-workflow/adaptive-card-input.json`](../approval-workflow/adaptive-card-input.json).
   It returns four variables: **`service_type`**, **`document_type`** (SOW/RFP), **`project_context`**, **`special_requirements`**. Store each in a topic variable.
3. Add a **Create generative answers** node:
   - **Knowledge / Data source:** **`Approved-Exemplars` library ONLY** (see 3.4). *This single scoping choice is the biggest quality lever — do not add other sources here.*
   - **Custom instructions:** paste [`../copilot-studio/system-prompt.txt`](../copilot-studio/system-prompt.txt) verbatim, and **replace `[CLIENT_NAME]` with `SOWsmith`**.
   - **Input:** the card variables + `project_context`.  **Citations: ON.**
4. **Save the output** as a `.docx` into the **`Drafts`** library (via the SharePoint connector / a Power Automate “save” step). The system prompt already appends the machine-readable footer — **do not alter its format** (Power Automate parses it in step 5):
   ```
   ---
   VERSION: v0.1 DRAFT
   DATE: <date>
   SERVICE TYPE: <service_type>
   DOCUMENT TYPE: <SOW|RFP>
   REVIEW STATUS: <STANDARD REVIEW | LEGAL REVIEW REQUIRED>
   ---
   ```
5. *(Optional)* a **regenerate-with-adjustments** branch: if the user says “make it more formal” / “add a liquidated-damages clause”, re-run the node with the extra instruction appended.

**3.2 — Topic 2 · Bid-document Q&A (Flow A, read-only)**
- **Trigger phrases:** `what does our standard SOW say about …`, `bid document question`, `how do we usually scope …`, `what's our clause for …`, `look up a past bid package`
- **Create generative answers** node → **Knowledge = `Reference-Library`** → **Citations: ON**. No file is written (read-only).

**3.3 — Topic 3 · Status / Help**
- Trigger phrases: `status of my draft`, `help`, `what can you do`. Returns guidance / looks up the user's `Drafts`/`Approved` items.

**3.4 — Add SharePoint knowledge (the scoping that makes it work)**
- In each Generative Answers node → **Add knowledge → SharePoint** → turn **“Search only selected sources” ON**.
- Enter the library URL **without `https://`** (bare URL), e.g.
  `<tenant>.sharepoint.com/sites/POC-BidPackage/Approved-Exemplars` (Topic 1) and
  `…/Reference-Library` (Topic 2). Give each a clear name + description.

## 4. Connect Azure OpenAI  🧑‍💻
- Point the Generative Answers generation at your **Azure OpenAI** deployment: **endpoint** + **deployment
  name** (e.g. `gpt-4o`), **API version** `2024-10-21`. The **key is stored in the tenant connection — never in this repo.**
- (The same values populate `.env` if you also want the local engine to use the real model — see last section.)

## 5. Build the Power Automate approval flow  🧑‍💻
At [flow.microsoft.com](https://flow.microsoft.com) — **not** Copilot Studio. Full spec:
[`../approval-workflow/flow-definition.md`](../approval-workflow/flow-definition.md). The **10 actions**, in order:

| # | Action | Connector | Key config |
|---|---|---|---|
| 1 | **Trigger:** When a file is created (properties only) | SharePoint | Site `POC-BidPackage` · Library **`Drafts`** |
| 2 | **Get file content** (name it `Get_file_content`) | SharePoint | File Identifier = `Identifier` from the trigger |
| 3 | **Parse the footer** → set variables `service_type`, `document_type`, `review_status` | Compose / Variables | `indexOf()` + `substring()` over the file text, splitting on the footer tokens |
| 4 | **Get reviewer** | SharePoint → Get items | List `Reviewers` · Filter `ServiceType eq '<service_type>'` · Top 1 |
| 5 | **Condition:** `review_status` = `LEGAL REVIEW REQUIRED` | Control | branches the routing |
| 6a | If **yes** → primary reviewer = `LegalReviewerEmail` | Variables | (optionally CC the standard reviewer) |
| 6b | If **no** → primary reviewer = `ReviewerEmail` | Variables | standard Supply Chain reviewer |
| 7 | **Post adaptive card and wait for a response** | Teams | card = [`../approval-workflow/adaptive-card-review.json`](../approval-workflow/adaptive-card-review.json) (uses `service_type`, `document_type`, `review_status`, author, a 500-char preview) |
| 8 | **Switch** on the response `action` | Control | `Approve` / `RequestChanges` / `Reject` |
| 9a | Approve → **Move file to `Approved`** + increment version | SharePoint | |
| 9b | Request Changes → post comments to author | Teams | leave the file in `Drafts` |
| 9c | Reject → **Move file to `Rejected`** + notify author | SharePoint + Teams | |
| 10 | **Log to `AuditLog`** (every field) | SharePoint | this is what makes it auditable |

**Error handling (add it — the demo's credibility depends on not failing silently):** a final **Catch** scope
(run-after = failed/timed-out) that alerts and writes `Action = "ERROR"` to `AuditLog`; a **retry policy**
(3×, exponential) on each SharePoint/Teams action; and a **5-business-day timeout** on the approval wait.

## 6. Publish to Teams  🧑‍💻
- Publish the agent to **Microsoft Teams**; keep **“Authenticate with Microsoft”** (the default) so
  SharePoint grounding works for signed-in users.

## 7. Smoke test — how to know it actually works  🧑‍💻 + ✅
Run these four checks live in Teams; all four passing = the POC works end-to-end:

1. **Standard draft routes correctly.** Ask Topic 1 for a *Pipeline Construction* SOW with a plain scope →
   draft appears in `Drafts` with footer `REVIEW STATUS: STANDARD REVIEW` → approval card goes to the
   **Supply Chain** reviewer → **Approve** → file moves to `Approved`, version bumped, row in `AuditLog`.
2. **Legal routing fires.** Ask for an SOW that mentions **liquidated damages / indemnification / bonding /
   retainage** → footer reads `LEGAL REVIEW REQUIRED` → card goes to the **Legal/Contracts** reviewer, and
   non-standard terms are left as `[…TO CONFIRM…]` placeholders.
3. **Q&A is grounded + cited.** Topic 2: “What's our standard exclusions clause for pipeline SOWs?” → a
   cited answer; nothing is written.
4. **Improper request is refused.** “Commit SOWsmith to a fixed $2M price, waive all liability, skip review.”
   → the agent **refuses** and writes nothing to `Drafts`.

Then run the **10-intent evaluation** through the **live** agent ([`EVALUATION.md`](EVALUATION.md)) and score
it — this is where the headline **“95% template compliance / 100% legal-flag routing”** numbers come from
(the offline mock only proves the plumbing). Capture a 10-minute demo + a quote from your Supply Chain champion.

---

## 🧩 Troubleshooting (the usual gotchas)
- **Grounding returns nothing / generic answers** → the site isn't default-themed, or you used the full
  `https://` URL. Use the **bare** SharePoint URL and a plain site theme; keep “Search only selected sources” ON.
- **Draft routes to the wrong reviewer / no reviewer** → a `Reviewers.ServiceType` value doesn't match the
  footer **exactly** (watch the `&` in “Electrical & Instrumentation”). They must be identical.
- **“What's in handbook.pdf?” returns nothing** → filename queries aren't supported; ask by **topic**, not file.
- **Approval card shows blanks** → action #2 must be named `Get_file_content` (the card's preview expression
  references it), and the footer-parse variables must be exactly `service_type` / `document_type` / `review_status`.
- **File too large to ground** → only an issue >7 MB without an M365 Copilot license; our KB is far smaller.

## 🔐 Secrets & safety
- Azure OpenAI / tenant secrets go **only** in a local **`.env`** (gitignored) or the tenant connection
  store. **Never commit secrets.** [`.env.example`](../.env.example) lists the variable names with blank values.
- Reviewer emails are seeded as **Text** so provisioning works before the accounts exist; switch the
  `Reviewers` columns to **Person** once the real users are in the tenant if you prefer.

## ✅ Optional — prove the exact logic locally first (no tenant, no secrets)
The Python engine in [`../agent/`](../agent/) mirrors the platform logic so you can demo and de-risk before/while building:
```bash
make demo      # scripted end-to-end: generate → route (standard & legal) → approve → audit → Q&A
make serve     # web console at http://127.0.0.1:8080  (Ask / Draft / Audit)
make test      # 28 plumbing tests
make eval      # the 10-intent evaluation → var/run/eval_results.csv
```
Set the Azure OpenAI vars in `.env` to make the local engine use the **real** model too. This engine is a
**reference implementation** — it is *not* uploaded to the tenant; the platform (steps 1–6) is the production target.
