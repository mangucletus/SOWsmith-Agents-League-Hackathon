"""Safety rails — mirror of the system prompt's SAFETY RAILS and REFUSE-OUTRIGHT rules.

In production these decisions are made by the model following the system prompt. Here we
also encode them as deterministic keyword rules so the OFFLINE MOCK can set the review
status correctly and so the refusal path is testable without a live model.

NOTE: these keyword rules are a *reference approximation* of the prompt's judgement, used
for the mock and for plumbing tests. The production agent relies on the model, not on this
keyword list, to make the call.
"""
from __future__ import annotations

import re

# A bid package touching any of these commercial/legal areas must be flagged
# LEGAL REVIEW REQUIRED (routed to Legal / Contracts). Used ONLY as a fallback for service
# types not present in the curated KB (the KB's own footers are the primary source of truth).
LEGAL_TRIGGER_TERMS = [
    "liquidated damage", "indemni", "hold harmless", "warranty", "warranties",
    "bond", "bonding", "retainage", "lien", "penalty", "penalties",
    "insurance limit", "liability", "termination for convenience", "flow-down", "flow down",
    "non-standard payment", "net 90", "net-90", "escalation clause", "bonus/penalty",
]
# Each term is matched at a WORD BOUNDARY at its start (so "lien" does NOT fire on "client"
# and "liability" does NOT fire on "reliability"), but with no trailing boundary so a stem
# still matches its forms ("indemni" -> "indemnity"/"indemnification"; "bond" -> "bonding").
_LEGAL_TRIGGER_RE = [re.compile(r"\b" + re.escape(t), re.IGNORECASE) for t in LEGAL_TRIGGER_TERMS]

# A request that is improper: fabricating prices/commercial commitments, waiving liability,
# or bypassing required review. The agent must refuse rather than draft.
UNLAWFUL_PATTERNS = [
    r"(invent|fabricate|make up|guess) .*(price|pricing|rate|cost|commercial term|amount)",
    r"commit\w* .*(to a )?(fixed|firm)? ?(price|amount|\$)",
    r"waiv\w* .*(all )?liabilit",
    r"bypass\w* .*(legal|contract|review|approval)",
    r"skip\w* .*(legal|contract|review|approval)",
    r"without .*(legal|contract|review|approval)",
]

REFUSAL_MESSAGE = (
    "I cannot draft this. The request asks me to invent commercial terms or bypass required "
    "review. Please supply the terms from Estimating/Contracts, or route this to Legal."
)


def is_unlawful(intent: str) -> bool:
    low = (intent or "").lower()
    return any(re.search(p, low) for p in UNLAWFUL_PATTERNS)


# Human-readable labels for the matcher stems (so the explanation reads cleanly to a reviewer).
_DISPLAY = {"indemni": "indemnification/indemnity", "liquidated damage": "liquidated damages",
            "bond": "bonding", "lien": "lien", "warranties": "warranty",
            "penalties": "penalty", "net 90": "net-90 terms", "net-90": "net-90 terms"}


def matched_legal_terms(*parts: str) -> list[str]:
    """The specific trigger terms that fire LEGAL REVIEW REQUIRED — the explainable 'why'
    behind the routing decision (surfaced to the reviewer and the audit log)."""
    blob = " ".join(p for p in parts if p)
    out: list[str] = []
    for term, rx in zip(LEGAL_TRIGGER_TERMS, _LEGAL_TRIGGER_RE):
        if rx.search(blob):
            label = _DISPLAY.get(term, term)
            if label not in out:
                out.append(label)
    return out


def needs_legal_review(*parts: str) -> bool:
    return bool(matched_legal_terms(*parts))
