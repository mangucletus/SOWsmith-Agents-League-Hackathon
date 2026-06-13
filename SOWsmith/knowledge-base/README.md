# `knowledge-base/` — SharePoint knowledge base

The content the agent grounds on (the **Knowledge Base** in the architecture diagram).

| Path | What |
|---|---|
| `sharepoint-online-knowledge-base/` | The actual KB to upload to SharePoint. Its own [`README.md`](sharepoint-online-knowledge-base/README.md) is the authoritative guide (two-library scoping, file-type matrix, upload checklist). |
| `generator/_build_knowledge_base.py` | Rebuilds the entire KB deterministically (~30 files). |

## Regenerate the KB
```bash
python knowledge-base/generator/_build_knowledge_base.py
```

## Structure (inside `sharepoint-online-knowledge-base/`)
- **`Approved-Exemplars/`** — 5 gold-standard SOWs → feeds the **generator** (Flow B).
- **`Reference-Library/`** — broad corpus of prior bid packages + the clause library (DOCX/PDF/PPTX/XLSX) → feeds **Q&A** (Flow A).
- **`Templates/`** — blank SOW/RFP template, Standard Bid Clause Library, Bidder Response Form.
- **`Lists/`** — `Reviewers.xlsx`, `AuditLog.xlsx` → import as SharePoint **lists**.
- **`Drafts/` `Approved/` `Rejected/`** — output libraries (start empty).

Upload it with `../infrastructure/sharepoint/Provision-SharePoint.ps1` (or the m365 CLI script).
Only **DOCX/PDF/PPTX/XLSX** live in the grounding libraries — the file types Copilot Studio indexes.
