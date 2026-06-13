# Copilot Studio — knowledge scoping (the critical move)

Getting the knowledge scope right is what makes draft quality good. **Scope each topic to a
different SharePoint library.** Mixing them dilutes draft quality.

| Topic | Knowledge source | Why |
|---|---|---|
| Topic 1 · Draft a Bid Package | **`Approved-Exemplars` only** (3–5 gold-standard SOWs) | The generator copies house style + structure from a small, clean set |
| Topic 2 · Bid-document Q&A | **`Reference-Library`** (broad corpus of past bid documents + the clause library) | Q&A needs breadth across all prior bid packages |

## How to add SharePoint knowledge to a Generative Answers node
1. In the topic's **Create generative answers** node → **Data source** → **Add knowledge** →
   ensure **"Search only selected sources"** is ON → choose **SharePoint**.
2. Enter the library URL **without `https://`** (bare URL), e.g.
   `contoso.sharepoint.com/sites/POC-BidPackage/Approved-Exemplars`.
   Recognised URLs are on the `*.sharepoint.com` domain.
3. Give it a clear **name + description** (the description helps orchestration).

## Supported content & limits (verified against Microsoft Learn)
- **Indexed file types:** Word (DOC/DOCX), PowerPoint (PPT/PPTX), PDF. XLSX is indexed but the
  agent can't run code on it, so analytical answers may be weak — the KB mirrors spreadsheet
  facts into DOCX/PDF for that reason.
- **Not used:** classic ASPX pages, accordion-nav sites, heavily custom CSS, password-protected
  or sensitivity-labelled files, MP4.
- **File size for grounding:** **< 7 MB** without an M365 Copilot license; **< 200 MB** with a
  Copilot license + Work IQ in the same tenant.
- **Filename queries don't work:** the agent can't answer "what's in handbook.pdf?" — ask by topic.
- Use a **default-themed** SharePoint site (custom CSS / accordion nav break grounding).

## Which file format? (DOCX vs PDF) — keep DOCX, no conversion needed
**Word (DOC/DOCX), PowerPoint (PPT/PPTX) and PDF are all first-class, equally indexed** for Copilot
Studio's SharePoint grounding. **DOCX works perfectly — you do *not* need to convert to PDF.** What
matters for answer quality is a real **text layer**, not the format. Recommended use:

- **DOCX** for documents you edit and version — the exemplar SOWs, the clause library, the templates.
- **PDF** for fixed / published documents you don't edit — bidder instructions, final reference packs.
- **Avoid scanned / image-only PDFs** (no text layer): they index but can't be read. OCR them first
  (`bidpkg ingest`, or Azure AI Document Intelligence in production) — see [`../docs/ROADMAP.md`](../docs/ROADMAP.md) §3.
- **Don't rely on XLSX for analytical questions** — the agent can't run code on spreadsheets, so mirror
  the key numbers into a DOCX/PDF narrative (the KB already does this for the rate sheet).

This POC's knowledge base already uses exactly this mix (DOCX/PDF/PPTX/XLSX), so **no conversion is needed.**

Sources: Microsoft Learn — *Quotas and limits → SharePoint web app limits* and
*Use SharePoint content for generative answers* (verified June 2026).
