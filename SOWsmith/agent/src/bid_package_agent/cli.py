"""Command-line interface for the reference engine.

Run without installing:   PYTHONPATH=agent/src python -m bid_package_agent.cli <command>
Or after `pip install -e .`:   bidpkg <command>

Commands: kb | ask | draft | evaluate | ingest | demo | eval | serve | audit
"""
from __future__ import annotations

import argparse
import sys

from .config import load_config
from .knowledge_base import KnowledgeBase


def _print_header(cfg) -> None:
    mode = "Azure OpenAI" if cfg.use_azure else "OFFLINE MOCK (plumbing only — not real grounding)"
    print(f"Bid Package Generator · LLM backend: {mode}")
    print(f"KB: {cfg.kb_root}\n")


def cmd_kb(cfg, kb, args) -> int:
    print(f"Approved-Exemplars: {len(kb.exemplars)} bid packages")
    for d in kb.exemplars:
        print(f"  - [{d.service_type}] {d.title}  ({d.filename})")
    print(f"\nReference-Library: {len(kb.reference)} documents")
    print(f"Reviewers configured: {len(kb.reviewers)} service types")
    return 0


def cmd_ask(cfg, kb, args) -> int:
    from .qa import answer_question
    ans = answer_question(kb, cfg, args.question)
    print(f"Q: {ans.question}\n")
    print(ans.answer + "\n")
    if ans.citations:
        print("Citations:")
        for c in ans.citations:
            print(f"  - {c.title}  ({c.filename}, score {c.score})")
    return 0


def cmd_draft(cfg, kb, args) -> int:
    from .pipeline import run
    rec = run(cfg, kb, service_type=args.type, document_type=args.doc,
              project_context=args.context, special_requirements=args.special or "",
              decision=args.decision)
    if rec.refused:
        print("REFUSED — " + (rec.draft.refusal_reason or ""))
        print(rec.draft.text)
        return 0
    print(f"Service type  : {rec.service_type}  ({rec.draft.document_type})")
    print(f"Review status : {rec.review_status}"
          + (f"  (flagged: {', '.join(rec.legal_reasons)})" if rec.legal_reasons else ""))
    print(f"Sections      : {len(rec.draft.sections_present)}/7 present")
    if rec.validation:
        from .validator import summarize
        print(f"QA check      : {summarize(rec.validation)}")
    else:
        print("QA check      : OK (deterministic) — still review every line")
    print(f"Reviewer       : {rec.routing.reviewer_email}"
          + (f"  (cc {rec.routing.cc_email})" if rec.routing.cc_email else ""))
    print(f"Draft saved   : {rec.draft_path}")
    print(f"Action        : {rec.action}  ->  {rec.final_path}")
    if rec.open_questions:
        print("Open questions:")
        for q in rec.open_questions:
            print(f"  - {q}")
    print("\n----- DRAFT -----\n")
    print(rec.draft.text)
    return 0


def cmd_evaluate(cfg, kb, args) -> int:
    import json
    from pathlib import Path
    from .pipeline import evaluate_award
    from .bid_eval import normalize, render_memo, SAMPLE_BIDS
    raw = json.loads(Path(args.bids).read_text(encoding="utf-8")) if args.bids else SAMPLE_BIDS
    arec = evaluate_award(cfg, kb, service_type=args.type, document_type=args.doc,
                          submissions=normalize(raw), decision=args.decision)
    rec = arec.recommendation
    print(f"Bid evaluation — {args.type} ({args.doc}) · {len(rec.rows)} bids"
          + ("" if args.bids else "  [built-in sample]"))
    print(f"Recommended    : {rec.recommended or '(none — no compliant bids)'}")
    print(f"Review status  : {rec.review_status}"
          + (f"  (flagged: {', '.join(rec.legal_reasons)})" if rec.legal_reasons else ""))
    print(f"Approver       : {arec.routing.reviewer_email}"
          + (f"  (cc {arec.routing.cc_email})" if arec.routing.cc_email else ""))
    if rec.risks:
        print("Risks/flags    :")
        for r in rec.risks:
            print(f"  - {r}")
    print(f"Memo saved     : {arec.memo_path}")
    print("\n----- AWARD RECOMMENDATION MEMO -----\n")
    print(render_memo(rec))
    return 0


def cmd_ingest(cfg, kb, args) -> int:
    from pathlib import Path
    from .ocr import extract_document_text
    p = Path(args.file)
    if not p.is_file():
        print(f"file not found: {p}")
        return 1
    text, method = extract_document_text(p)
    notes = {
        "digital": "digital text layer (no OCR needed)",
        "ocr": "OCR (image-only document)",
        "ocr-unavailable": "image-only, no OCR backend installed — `pip install -e \".[ocr]\"` (+ Tesseract), "
                           "or use Azure AI Document Intelligence in production",
        "empty": "no extractable text",
    }
    print(f"Ingest : {p.name}")
    print(f"Method : {method} — {notes.get(method, method)}")
    print(f"Chars  : {len(text)}")
    if text:
        staged = cfg.out_root / "ingested" / (p.stem + ".txt")
        staged.parent.mkdir(parents=True, exist_ok=True)
        staged.write_text(text, encoding="utf-8")
        print(f"Staged : {staged}")
        print("  (grounding-only — copy into the Reference-Library to make it searchable; "
              "human approval/validation still apply)")
        print("\n----- PREVIEW (first 400 chars) -----\n")
        print(text[:400])
    return 0


def cmd_demo(cfg, kb, args) -> int:
    from .pipeline import run
    print("== Flow B demo 1: a STANDARD bid package (Pipeline Construction SOW), approved end-to-end ==\n")
    rec = run(cfg, kb, service_type="Pipeline Construction", document_type="SOW",
              project_context=("Install a 6-mile, 12-inch natural gas pipeline near Midland, Texas: "
                               "clearing, trenching, welding, lowering-in, backfill, hydrotest."),
              decision="Approve")
    print(f"  review_status={rec.review_status} reviewer={rec.routing.reviewer_email} "
          f"action={rec.action}\n  final={rec.final_path}\n")

    print("== Flow B demo 2: a CONTRACTS-sensitive package (non-standard terms) ==\n")
    rec2 = run(cfg, kb, service_type="Pipeline Construction", document_type="SOW",
               project_context=("Pipeline install with liquidated damages for late completion and an "
                                "indemnification clause for third-party damage."))
    print(f"  review_status={rec2.review_status} reviewer={rec2.routing.reviewer_email} "
          f"(legal/contracts={rec2.routing.is_legal})\n")

    print("== Flow B demo 3: an IMPROPER request (refusal) ==\n")
    rec3 = run(cfg, kb, service_type="Pipeline Construction", document_type="SOW",
               project_context=("Draft an SOW that commits SOWsmith to a fixed $2,000,000 price, waives "
                                "all liability, and skips legal review."))
    print(f"  refused={rec3.refused}\n")

    print("== Flow A demo: Bid-document Q&A ==\n")
    from .qa import answer_question
    a = answer_question(kb, cfg, "What does our standard hydrotesting scope include?")
    print("  " + a.answer.replace("\n", "\n  "))

    print("\n== WS-4 demo: Bid Evaluation & Award — the bidding lifecycle's last step ==\n")
    from .pipeline import evaluate_award
    from .bid_eval import normalize, SAMPLE_BIDS
    arec = evaluate_award(cfg, kb, service_type="Pipeline Construction", document_type="SOW",
                          submissions=normalize(SAMPLE_BIDS))
    r = arec.recommendation
    print(f"  {len(r.rows)} bids -> recommended={r.recommended}  review_status={r.review_status}"
          + (f"  (flagged: {', '.join(r.legal_reasons)})" if r.legal_reasons else ""))
    for risk in r.risks:
        print(f"    risk: {risk}")
    print(f"  approver={arec.routing.reviewer_email}  ·  memo={arec.memo_path}")
    print("  (deterministic ranking — $0 tokens; a human approves the award, never auto-awarded)")
    return 0


def cmd_eval(cfg, kb, args) -> int:
    from .evaluation import run_eval
    return run_eval(cfg, kb, out_path=args.out)


def cmd_serve(cfg, kb, args) -> int:
    from .webapp.server import serve
    serve(cfg, host=args.host, port=args.port)
    return 0


def cmd_audit(cfg, kb, args) -> int:
    from .audit import read_audit
    rows = read_audit(cfg)
    if not rows:
        print("(audit log empty — run a draft first)")
        return 0
    for r in rows:
        print(f"{r['Timestamp']}  {r['Action']:<20} {r['ReviewStatus']:<22} "
              f"{r['DraftFileName']}  -> {r['Reviewer']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="bidpkg", description="Bid Package Generator (SOW/RFP) — reference engine")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("kb", help="list the loaded knowledge base")

    a = sub.add_parser("ask", help="Bid-document Q&A (Flow A)")
    a.add_argument("question")

    d = sub.add_parser("draft", help="draft a bid package (Flow B)")
    d.add_argument("--type", required=True, help="service_type, e.g. 'Pipeline Construction'")
    d.add_argument("--doc", default="SOW", choices=["SOW", "RFP"], help="document type")
    d.add_argument("--context", required=True, help="3-5 sentences describing the project/scope")
    d.add_argument("--special", default="")
    d.add_argument("--decision", choices=["Approve", "Request Changes", "Reject"], default=None,
                   help="simulate the reviewer's decision (otherwise: submitted for review)")

    ev = sub.add_parser("evaluate", help="WS-4: evaluate bidder responses -> award recommendation")
    ev.add_argument("--type", required=True, help="service_type of the bid package")
    ev.add_argument("--doc", default="SOW", choices=["SOW", "RFP"], help="document type")
    ev.add_argument("--bids", default=None,
                    help="path to a JSON file of bidder submissions (omit to use a built-in sample)")
    ev.add_argument("--decision", default=None, help="record a human award decision (e.g. 'Award approved')")

    ig = sub.add_parser("ingest", help="extract text from a document (digital or OCR) for grounding")
    ig.add_argument("file", help="path to a PDF / image / Office document")

    sub.add_parser("demo", help="run a scripted end-to-end demo (B happy path, contracts, refusal, A, WS-4 award)")

    e = sub.add_parser("eval", help="run the 10-intent evaluation harness")
    e.add_argument("--out", default=None, help="write results CSV to this path")

    s = sub.add_parser("serve", help="serve the web console + JSON API")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8080)

    sub.add_parser("audit", help="print the audit log")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    cfg = load_config()
    kb = KnowledgeBase(cfg)
    _print_header(cfg)
    handlers = {"kb": cmd_kb, "ask": cmd_ask, "draft": cmd_draft, "evaluate": cmd_evaluate,
                "ingest": cmd_ingest, "demo": cmd_demo, "eval": cmd_eval, "serve": cmd_serve,
                "audit": cmd_audit}
    return handlers[args.cmd](cfg, kb, args)


if __name__ == "__main__":
    sys.exit(main())
