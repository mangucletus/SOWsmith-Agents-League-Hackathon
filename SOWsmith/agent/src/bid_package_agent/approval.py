"""Approval routing — mirrors the Power Automate flow (Part 5).

  * action 4  -> reviewer lookup in Reviewers (by service_type)
  * action 5  -> condition on REVIEW STATUS == LEGAL REVIEW REQUIRED
  * action 6a/6b -> pick legal vs standard reviewer
  * action 9a/9b/9c -> Approve / Request Changes / Reject move the file
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from .config import Config
from .footer import LEGAL
from .knowledge_base import KnowledgeBase

APPROVE = "Approve"
REQUEST_CHANGES = "Request Changes"
REJECT = "Reject"
DECISIONS = (APPROVE, REQUEST_CHANGES, REJECT)


@dataclass
class Routing:
    service_type: str
    review_status: str
    is_legal: bool
    reviewer_email: str
    cc_email: str | None
    reviewer_found: bool


def route(kb: KnowledgeBase, service_type: str, review_status: str) -> Routing:
    rev = kb.reviewer_for(service_type)
    is_legal = (review_status or "").strip().upper() == LEGAL
    if rev is None:
        return Routing(service_type, review_status, is_legal,
                       reviewer_email="(no reviewer configured for this service type)",
                       cc_email=None, reviewer_found=False)
    if is_legal:
        return Routing(service_type, review_status, True,
                       reviewer_email=rev.legal_reviewer_email,
                       cc_email=rev.reviewer_email or None, reviewer_found=True)
    return Routing(service_type, review_status, False,
                   reviewer_email=rev.reviewer_email, cc_email=None, reviewer_found=True)


def apply_decision(draft_path: Path, decision: str, cfg: Config) -> Path:
    """Move the draft per the reviewer's decision and return its new path."""
    draft_path = Path(draft_path)
    if decision == APPROVE:
        cfg.approved_dir.mkdir(parents=True, exist_ok=True)
        dest = cfg.approved_dir / draft_path.name
        shutil.move(str(draft_path), str(dest))
        return dest
    if decision == REJECT:
        cfg.rejected_dir.mkdir(parents=True, exist_ok=True)
        dest = cfg.rejected_dir / draft_path.name
        shutil.move(str(draft_path), str(dest))
        return dest
    # Request Changes -> stays in Drafts for the author to revise
    return draft_path
