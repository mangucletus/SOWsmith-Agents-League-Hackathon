"""End-to-end orchestration for Flow B: generate -> save draft -> route to reviewer ->
(optional reviewer decision) -> move file -> write AuditLog. This is the code mirror of
the full POC happy path (Copilot Studio generation + Power Automate approval)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from .approval import Routing, apply_decision, route
from .audit import append_audit
from .config import Config
from .footer import parse_footer
from .generator import DraftResult, generate_draft
from .knowledge_base import KnowledgeBase


def _slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-") or "BidPackage"


@dataclass
class RunRecord:
    refused: bool
    service_type: str
    review_status: str | None
    draft: DraftResult
    routing: Routing | None
    draft_path: Path | None
    final_path: Path | None
    action: str
    audit_row: dict | None = None
    open_questions: list[str] = field(default_factory=list)
    legal_reasons: list[str] = field(default_factory=list)
    validation: list = field(default_factory=list)


def run(cfg: Config, kb: KnowledgeBase, *, service_type: str, project_context: str,
        document_type: str = "SOW", special_requirements: str = "", decision: str | None = None,
        author: str = "poc.user@sowsmithusa.com", comments: str = "", llm=None) -> RunRecord:

    draft = generate_draft(kb, cfg, service_type=service_type, document_type=document_type,
                           project_context=project_context, special_requirements=special_requirements, llm=llm)

    if draft.refused:
        append_audit(cfg, draft_filename="(none)", author=author, reviewer="(none)",
                     action="Refused", review_status="N/A",
                     comments=draft.refusal_reason or "refused")
        return RunRecord(refused=True, service_type=service_type, review_status=None, draft=draft,
                         routing=None, draft_path=None, final_path=None, action="Refused")

    # Save the draft into the Drafts library (output store). Production writes DOCX to
    # SharePoint; the reference engine writes the same content + footer as Markdown.
    cfg.drafts_dir.mkdir(parents=True, exist_ok=True)
    # _slug() both fields: service_type and document_type are caller-supplied (the /api/draft
    # endpoint does not restrict document_type to SOW/RFP the way the CLI does), so neither may
    # introduce path separators / traversal into the Drafts filename.
    fname = f"{_slug(service_type)}_{_slug(draft.document_type)}_v0.1_DRAFT_{date.today().isoformat()}.md"
    draft_path = cfg.drafts_dir / fname
    draft_path.write_text(draft.text, encoding="utf-8")

    routing = route(kb, service_type, draft.review_status or "")

    final_path, action = draft_path, "Submitted for review"
    if decision:
        final_path = apply_decision(draft_path, decision, cfg)
        action = decision

    if comments:
        note = comments
    elif routing.is_legal:
        why = ", ".join(draft.legal_reasons)
        note = f"Routed to Legal/Contracts reviewer. Flagged because: {why}." if why \
            else "Routed to Legal/Contracts reviewer."
    else:
        note = "Routed to standard Supply Chain reviewer."
    if draft.validation:
        note += f" | QA flagged {len(draft.validation)} item(s) for line-by-line review."
    audit_row = append_audit(
        cfg, draft_filename=fname, author=author, reviewer=routing.reviewer_email,
        action=action, review_status=draft.review_status or "", comments=note,
    )

    open_qs = []
    if "OPEN QUESTIONS" in draft.text:
        tail = draft.text.split("OPEN QUESTIONS", 1)[1]
        open_qs = [ln.strip("- ").strip() for ln in tail.splitlines() if ln.strip().startswith("-")]

    return RunRecord(refused=False, service_type=service_type, review_status=draft.review_status,
                     draft=draft, routing=routing, draft_path=draft_path, final_path=final_path,
                     action=action, audit_row=audit_row, open_questions=open_qs,
                     legal_reasons=draft.legal_reasons, validation=draft.validation)


@dataclass
class AwardRecord:
    recommendation: "object"
    memo_path: Path
    routing: Routing
    audit_row: dict
    action: str


def evaluate_award(cfg: Config, kb: KnowledgeBase, *, service_type: str, submissions,
                   document_type: str = "SOW", decision: str | None = None,
                   author: str = "poc.user@sowsmithusa.com", comments: str = "") -> AwardRecord:
    """WS-4 thin slice: evaluate bidder submissions -> deterministic, explainable award
    recommendation -> memo + audit. Routes to Legal/Contracts when the recommended bid carries
    non-standard terms (reuses route()). Never auto-awards — `decision` records a human's call."""
    from .bid_eval import evaluate_bids, render_memo

    rec = evaluate_bids(submissions, service_type=service_type, document_type=document_type, kb=kb)
    cfg.evaluations_dir.mkdir(parents=True, exist_ok=True)
    fname = f"{_slug(service_type)}_{_slug(document_type)}_AWARD-REC_{date.today().isoformat()}.md"
    memo_path = cfg.evaluations_dir / fname
    memo_path.write_text(render_memo(rec), encoding="utf-8")

    routing = route(kb, service_type, rec.review_status)
    action = decision or "Award recommended"
    why = f" Flagged: {', '.join(rec.legal_reasons)}." if rec.legal_reasons else ""
    note = comments or (f"Recommend {rec.recommended}." + why if rec.recommended
                        else "No compliant bids — no award recommended.")
    audit_row = append_audit(cfg, draft_filename=fname, author=author, reviewer=routing.reviewer_email,
                             action=action, review_status=rec.review_status, comments=note)
    return AwardRecord(recommendation=rec, memo_path=memo_path, routing=routing,
                       audit_row=audit_row, action=action)


def decide(cfg: Config, kb: KnowledgeBase, *, filename: str, decision: str,
           comments: str = "", author: str = "poc.user@sowsmithusa.com") -> dict:
    """Apply a reviewer decision to a draft already saved in the Drafts library
    (mirrors the Power Automate Approve / Request Changes / Reject branches).

    `filename` is caller/user-supplied (the web /api/review endpoint), so it is treated as a
    bare file name only — reject any path separators / parent references and confirm the
    resolved path stays inside the Drafts library (prevents path traversal)."""
    name = (filename or "").strip()
    if (not name) or name.startswith(".") or "\\" in name or name != Path(name).name:
        raise FileNotFoundError(f"invalid draft filename: {filename!r}")
    draft_path = (cfg.drafts_dir / name).resolve()
    if draft_path.parent != cfg.drafts_dir.resolve():
        raise FileNotFoundError("draft not found in Drafts")
    if not draft_path.is_file():
        raise FileNotFoundError(f"draft not found in Drafts: {name}")
    ftr = parse_footer(draft_path.read_text(encoding="utf-8"))
    service_type = ftr.service_type if ftr else "Unknown"
    review_status = ftr.review_status if ftr else ""
    routing = route(kb, service_type, review_status)
    final_path = apply_decision(draft_path, decision, cfg)
    audit_row = append_audit(cfg, draft_filename=name, author=author,
                             reviewer=routing.reviewer_email, action=decision,
                             review_status=review_status, comments=comments)
    return {"action": decision, "service_type": service_type, "review_status": review_status,
            "reviewer": routing.reviewer_email, "final_path": str(final_path),
            "final_library": final_path.parent.name, "audit_row": audit_row}
