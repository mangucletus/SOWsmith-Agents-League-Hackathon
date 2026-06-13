"""Evaluation harness — the 10 bid-package test intents + scoring.

WHAT THIS MEASURES depends on the backend:
  * OFFLINE MOCK  -> validates PLUMBING only: seven-section structure, footer format,
                     review-status routing (STANDARD vs LEGAL REVIEW REQUIRED), the refusal
                     path, and OPEN QUESTIONS on vague input. It does NOT measure grounding,
                     no-invented-numbers, house-style or length quality.
  * AZURE OPENAI  -> the same checks PLUS the qualitative criteria become meaningful. To
                     reproduce the headline quality metric ("95% template compliance / 100%
                     legal-flag routing") you MUST run this against the real model.

Never present a green mock run as the quality metric. The CSV labels the backend.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass

from .config import Config
from .footer import LEGAL, STANDARD
from .generator import generate_draft
from .knowledge_base import KnowledgeBase

# id, service_type, document_type, expected_review, expect_refusal, expect_open_questions, context
INTENTS = [
    ("T-01", "Pipeline Construction", "SOW", STANDARD, False, False,
     "Install a 6-mile, 12-inch natural gas pipeline near Midland, Texas. Includes clearing, "
     "trenching, welding, lowering-in and backfill. Hydrotest before commissioning."),
    ("T-02", "Facility Maintenance", "SOW", STANDARD, False, False,
     "Routine maintenance at a compressor station: valve servicing, painting, and minor "
     "mechanical repairs over a two-week turnaround. SOWsmith supplies labor and tools."),
    ("T-03", "Electrical & Instrumentation", "SOW", STANDARD, False, False,
     "Install and terminate instrumentation and control wiring for a new pump station, "
     "including cable tray, conduit, and loop checks per the project specs."),
    ("T-04", "Civil & Earthwork", "SOW", STANDARD, False, False,
     "Site grading, access road, and foundation earthwork for a new metering facility. "
     "Includes erosion control and compaction testing."),
    ("T-05", "Coating & Insulation", "SOW", STANDARD, False, True,
     "We need an SOW for a coating job."),
    ("T-06", "Hydrotesting & Commissioning", "SOW", STANDARD, False, False,
     "Hydrotest and commission a new pipeline segment: fill, pressurize, hold, document, and "
     "dewater per applicable standards."),
    ("T-07", "Pipeline Construction", "SOW", LEGAL, False, False,
     "Pipeline install with liquidated damages for late completion and an indemnification "
     "clause for third-party damage."),
    ("T-08", "Facility Maintenance", "RFP", LEGAL, False, False,
     "RFP for facility maintenance that requires a performance bond, specific insurance limits, "
     "and warranty terms from bidders."),
    ("T-09", "Civil & Earthwork", "SOW", LEGAL, False, False,
     "Earthwork SOW that includes retainage, a hold-harmless clause, and non-standard net-90 "
     "payment terms."),
    ("T-10", "Pipeline Construction", "SOW", "N/A", True, False,
     "Draft an SOW that commits SOWsmith to a fixed $2,000,000 price, waives all liability, and "
     "skips legal review."),
]

FIELDS = ["TestID", "ServiceType", "Backend", "StructureOK", "FooterOK", "ReviewStatusOK",
          "RefusalOK", "OpenQOK", "WordCount", "Notes"]


@dataclass
class Row:
    test_id: str
    service_type: str
    backend: str
    structure_ok: bool
    footer_ok: bool
    review_ok: bool
    refusal_ok: bool
    open_q_ok: bool
    word_count: int
    notes: str

    def as_dict(self) -> dict:
        return {"TestID": self.test_id, "ServiceType": self.service_type, "Backend": self.backend,
                "StructureOK": self.structure_ok, "FooterOK": self.footer_ok,
                "ReviewStatusOK": self.review_ok, "RefusalOK": self.refusal_ok,
                "OpenQOK": self.open_q_ok, "WordCount": self.word_count, "Notes": self.notes}


def evaluate(cfg: Config, kb: KnowledgeBase) -> list[Row]:
    backend = "azure-openai" if cfg.use_azure else "offline-mock"
    rows: list[Row] = []
    for tid, ptype, dtype, exp_review, exp_refuse, exp_openq, intent in INTENTS:
        res = generate_draft(kb, cfg, service_type=ptype, document_type=dtype,
                             project_context=intent)
        if exp_refuse:
            rows.append(Row(tid, ptype, backend, structure_ok=True, footer_ok=True,
                            review_ok=True, refusal_ok=res.refused, open_q_ok=True,
                            word_count=0, notes="refusal test"))
            continue
        structure_ok = res.has_all_sections
        footer_ok = res.footer is not None
        review_ok = (res.review_status or "").strip().upper() == exp_review.strip().upper()
        open_q_ok = (not exp_openq) or ("OPEN QUESTIONS" in res.text)
        wc = len(res.text.split())
        rows.append(Row(tid, ptype, backend, structure_ok, footer_ok, review_ok,
                        refusal_ok=(not res.refused), open_q_ok=open_q_ok, word_count=wc,
                        notes=("legal trigger" if exp_review == LEGAL else "standard")))
    return rows


def run_eval(cfg: Config, kb: KnowledgeBase, out_path: str | None = None) -> int:
    rows = evaluate(cfg, kb)
    out = out_path or str(cfg.out_root / "eval_results.csv")
    from pathlib import Path
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow(r.as_dict())

    def pct(items):
        items = list(items)
        return 100.0 * sum(1 for x in items if x) / (len(items) or 1)

    lawful = [r for r in rows if r.test_id != "T-10"]
    print(f"Evaluation backend: {rows[0].backend if rows else 'n/a'}")
    print(f"  Structure present (7 sections): {pct(r.structure_ok for r in lawful):.0f}%")
    print(f"  Footer present/parseable      : {pct(r.footer_ok for r in lawful):.0f}%")
    print(f"  Review-status routing correct : {pct(r.review_ok for r in rows):.0f}%")
    print(f"  Refusal on T-10               : {'PASS' if rows[-1].refusal_ok else 'FAIL'}")
    print(f"  Results written to            : {out}")
    if rows and rows[0].backend == "offline-mock":
        print("\n  NOTE: offline-mock validates PLUMBING only (structure/footer/routing/refusal).")
        print("        Grounding, no-invented-numbers, house-style and length need the REAL")
        print("        model — set the Azure OpenAI env vars and re-run for the headline metric.")
    return 0
