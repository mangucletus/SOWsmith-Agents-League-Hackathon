# Copilot Studio — Topics & trigger phrases

The agent (Bid Package Agent) has three topics. Build them in Copilot Studio
(`copilotstudio.microsoft.com`). The reference engine in `agent/` mirrors Topics 1 and 2.

> **Critical setting:** Settings → Generative AI → **turn "Use AI in conversation" OFF**.
> Generation is wired manually inside the topics so we control grounding and the prompt.

---

## Topic 1 — Draft a Bid Package  (Flow B, the generator)
**Trigger phrases**
- `draft a bid package`
- `create an SOW`
- `new SOW for …`
- `write an RFP`
- `draft a scope of work for …`

**Flow inside the topic**
1. **Question / Adaptive Card** — collect the inputs with
   [`../approval-workflow/adaptive-card-input.json`](../approval-workflow/adaptive-card-input.json):
   `service_type`, `document_type` (SOW/RFP), `project_context`, `special_requirements`. Store each in a variable.
2. **Create generative answers** node:
   - **Input:** the adaptive-card variables + `project_context`.
   - **Knowledge:** the SharePoint **`Approved-Exemplars` library ONLY** (see `knowledge-scoping.md`).
   - **Custom instructions:** paste [`system-prompt.txt`](system-prompt.txt) verbatim (replace `[CLIENT_NAME]`).
   - **Output:** store in a variable; turn **citations ON**.
3. **Save** the output as a `.docx` into the SharePoint **`Drafts`** library (a Power Automate flow
   or the SharePoint connector). Creating that file fires the approval flow (see `../approval-workflow/`).
4. **Regenerate-with-adjustments** path (optional): if the user types `make it more formal` or
   `add a liquidated-damages clause`, re-run the node with the extra instruction appended.

## Topic 2 — Bid-document Q&A  (Flow A, RAG, read-only)
**Trigger phrases**
- `what does our standard SOW say about …`
- `bid document question`
- `how do we usually scope …`
- `what's our clause for …`
- `look up a past bid package`

**Flow inside the topic**
1. **Create generative answers** node:
   - **Knowledge:** the SharePoint **`Reference-Library`** (the broad published set).
   - **Custom instructions:** answer only from context; cite sources; if not found, say so.
   - **Citations ON.** No file is written — this path is read-only.

## Topic 3 — Status / Help
**Trigger phrases**
- `status of my draft`
- `help`
- `what can you do`

Returns guidance and (optionally) looks up the user's drafts in the `Drafts`/`Approved` libraries.

---

## Deployment channel
Publish the agent to **Microsoft Teams**. With **Authenticate with Microsoft** (the default),
SharePoint grounding works for signed-in users without manual auth.
