# `agent/` — Bid Package Agent (runnable reference engine)

A Python mirror of the production agent + Support Layer + approval routing, so the whole POC logic
can be **run, tested and demoed without a Microsoft 365 tenant**. The production agent is built in
Copilot Studio (`../copilot-studio/`) and Power Automate (`../approval-workflow/`); this engine
encodes the same behaviour.

## Layout
```
src/bid_package_agent/
  config.py         env-driven config (.env optional; Azure OpenAI optional)
  textextract.py    DOCX/PDF/PPTX/XLSX → text
  retrieval.py      tiny TF-IDF index (stands in for Copilot Studio semantic search)
  knowledge_base.py loads Approved-Exemplars / Reference-Library / Reviewers; routing source of truth
  prompts.py        the canonical SOW/RFP system prompt (mirrored to copilot-studio/system-prompt.txt)
  llm.py            AzureOpenAILLM + deterministic MockLLM
  generator.py      Flow B (WS-1) — grounded SOW/RFP draft + footer
  validator.py      deterministic ($0-token) QA pass on a draft (invented numbers, speculation, structure)
  qa.py             Flow A — RAG bid-document Q&A with citations
  footer.py         the version-footer contract (parse/build; SERVICE TYPE + DOCUMENT TYPE)
  safety.py         contracts-trigger + improper-request rules; matched_legal_terms() = explainable "why"
  bid_eval.py       WS-4 (Bid Evaluation & Award) — deterministic bid comparison + explainable award rec
                    (Finance-threshold sign-off, BAFO suggestion, draft award/regret notices)
  ocr.py            OCR ingestion slice — digital-first text extraction + optional OCR fallback
  approval.py       reviewer lookup + standard/Legal-Contracts branch + file moves (Power Automate mirror)
  audit.py          AuditLog writer
  pipeline.py       end-to-end orchestration (generate → save → route → decide → audit; + evaluate_award)
  cli.py            kb | ask | draft | evaluate | ingest | demo | eval | serve | audit
  webapp/server.py  stdlib JSON API + static server for ../../frontend/web-console
tests/              pytest plumbing tests
```

## Run
```bash
python -m pytest -q                                          # from repo root
PYTHONPATH=src python -m bid_package_agent.cli demo          # from this folder
PYTHONPATH=src python -m bid_package_agent.cli draft --type "Pipeline Construction" --doc SOW \
  --context "Install a 6-mile 12-inch gas pipeline near Midland: weld, lower-in, hydrotest." --decision Approve
PYTHONPATH=src python -m bid_package_agent.cli evaluate --type "Pipeline Construction" --doc SOW  # WS-4 award rec
```

## Backends
Offline **mock** by default (deterministic; validates plumbing). Set `AZURE_OPENAI_ENDPOINT` +
`AZURE_OPENAI_API_KEY` in a `.env` (gitignored) to use real GPT-4 generation.
