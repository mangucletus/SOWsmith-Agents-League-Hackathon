"""WS-4 (Bid Evaluation & Award) — a thin slice that reuses the WS-1 substrate.

After a bid package (SOW/RFP) goes out, bidders respond. This module NORMALIZES the
responses to a common structure, COMPARES them deterministically (price, schedule,
exclusions, non-standard terms) and produces an explainable AWARD RECOMMENDATION memo.

Design (matches the team's stance and the source brief):
  * The comparison/ranking is DETERMINISTIC analytics — **$0 tokens, no hallucination, fully
    explainable**. In production an LLM only normalizes messy bidder formats and writes the memo
    prose; the ranking math stays deterministic here.
  * The agent NEVER awards. It drafts, ranks and flags; a human (Supply Chain manager / PM,
    Finance above threshold) approves — reusing the same approval + audit substrate as WS-1.
    (Brief: "AI never awards a bid… Buyers, QC and managers retain decision authority.")
  * Non-standard commercial/legal terms in the recommended bid reuse safety.matched_legal_terms()
    and route the award to Legal/Contracts — the same content-driven routing as WS-1.
"""
from __future__ import annotations

import re
import statistics
from dataclasses import dataclass, field

from .footer import LEGAL, STANDARD
from .safety import matched_legal_terms

# Awards above this total also require Finance sign-off (brief: "Finance signs off above threshold").
FINANCE_THRESHOLD = 250_000.0
# If the top two priced bids are within this fraction, suggest a Best and Final Offer (BAFO) round.
BAFO_WINDOW = 0.05


@dataclass
class BidSubmission:
    bidder: str
    total_price: float | None              # USD; None = no-bid / incomplete
    schedule_days: int | None = None
    exclusions: list[str] = field(default_factory=list)
    terms: str = ""                        # free-text commercial/legal terms
    notes: str = ""


@dataclass
class BidRow:
    bidder: str
    total_price: float | None
    schedule_days: int | None
    n_exclusions: int
    legal_flags: list[str]
    compliant: bool


@dataclass
class AwardRecommendation:
    service_type: str
    document_type: str
    rows: list[BidRow]
    recommended: str | None
    reasons: list[str]
    risks: list[str]
    review_status: str
    legal_reasons: list[str]
    comparables: list[str] = field(default_factory=list)
    finance_signoff: bool = False    # award total exceeds the Finance threshold
    bafo_suggested: bool = False     # top two bids are close — consider a BAFO round


def _num(v) -> float | None:
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = re.sub(r"[^0-9.]", "", str(v))
    return float(s) if s else None


def _int(v) -> int | None:
    n = _num(v)
    return int(n) if n is not None else None


def normalize(raw: list[dict]) -> list[BidSubmission]:
    """Tolerant parse of bidder submissions (in production the LLM does this from messy text)."""
    out: list[BidSubmission] = []
    for r in raw:
        out.append(BidSubmission(
            bidder=str(r.get("bidder") or r.get("name") or "Unknown bidder"),
            total_price=_num(r.get("total_price") if r.get("total_price") is not None
                             else (r.get("price") if r.get("price") is not None else r.get("total"))),
            schedule_days=_int(r.get("schedule_days") if r.get("schedule_days") is not None else r.get("schedule")),
            exclusions=list(r.get("exclusions") or []),
            terms=str(r.get("terms") or ""),
            notes=str(r.get("notes") or ""),
        ))
    return out


def evaluate_bids(submissions: list[BidSubmission], *, service_type: str,
                  document_type: str = "SOW", kb=None) -> AwardRecommendation:
    rows = [BidRow(bidder=s.bidder, total_price=s.total_price, schedule_days=s.schedule_days,
                   n_exclusions=len(s.exclusions),
                   legal_flags=(matched_legal_terms(s.terms) if s.terms else []),
                   compliant=s.total_price is not None) for s in submissions]

    priced = [s for s in submissions if s.total_price is not None]
    reasons: list[str] = []
    risks: list[str] = []
    recommended: str | None = None
    review_status = STANDARD
    legal_reasons: list[str] = []
    finance_signoff = False
    bafo_suggested = False

    if not priced:
        risks.append("No priced/compliant bids received — cannot recommend an award.")
    else:
        cand = min(priced, key=lambda s: s.total_price)  # lowest compliant total
        recommended = cand.bidder
        reasons.append(f"Lowest compliant total: ${cand.total_price:,.0f}.")
        others = sorted(s.total_price for s in priced if s is not cand)
        if others:
            delta = (others[0] - cand.total_price) / cand.total_price * 100
            reasons.append(f"Next lowest is ${others[0]:,.0f} (+{delta:.0f}%).")
        if cand.schedule_days:
            reasons.append(f"Proposed schedule: {cand.schedule_days} days.")

        legal_reasons = matched_legal_terms(cand.terms) if cand.terms else []
        if legal_reasons:
            review_status = LEGAL
            risks.append("Recommended bid carries non-standard commercial/legal terms "
                         f"({', '.join(legal_reasons)}) — award routes to Legal/Contracts.")

        med = statistics.median([s.total_price for s in priced])
        if cand.total_price < 0.75 * med:
            risks.append(f"Recommended bid is {(1 - cand.total_price / med) * 100:.0f}% below the median "
                         "— verify the bidder understood full scope before award.")

        peer_min = min((len(s.exclusions) for s in priced if s is not cand), default=len(cand.exclusions))
        if len(cand.exclusions) > peer_min:
            risks.append("Recommended bid excludes more scope than a competing bid "
                         f"(excludes: {', '.join(cand.exclusions) or 'n/a'}) — confirm coverage.")

        if cand.total_price > FINANCE_THRESHOLD:
            finance_signoff = True
            risks.append(f"Award total exceeds ${FINANCE_THRESHOLD:,.0f} — **Finance sign-off required** "
                         "in addition to Supply Chain / PM approval.")

        prices = sorted(s.total_price for s in priced)
        if len(prices) >= 2 and (prices[1] - prices[0]) <= BAFO_WINDOW * prices[0]:
            bafo_suggested = True
            reasons.append(f"Top two bids are within {(prices[1] - prices[0]) / prices[0] * 100:.0f}% "
                           "— consider a Best and Final Offer (BAFO) round before awarding.")

    comparables: list[str] = []
    if kb is not None:
        try:
            comparables = [d.title for _, d in kb.search_reference(f"{service_type} statement of work", k=2)]
        except Exception:
            comparables = []

    return AwardRecommendation(service_type=service_type, document_type=document_type, rows=rows,
                               recommended=recommended, reasons=reasons, risks=risks,
                               review_status=review_status, legal_reasons=legal_reasons,
                               comparables=comparables, finance_signoff=finance_signoff,
                               bafo_suggested=bafo_suggested)


def draft_notices(rec: AwardRecommendation) -> list[tuple[str, str, str]]:
    """Draft award / regret notices for human review before sending (the WS-4 'award notification
    agent', here producing DRAFTS only). Returns (bidder, kind, text) tuples."""
    out: list[tuple[str, str, str]] = []
    if not rec.recommended:
        return out
    legal_note = (" Final commercial terms are subject to Legal/Contracts review."
                  if rec.review_status == LEGAL else "")
    out.append((rec.recommended, "AWARD",
        f"Dear {rec.recommended},\n\nFollowing evaluation of bids for the {rec.service_type} "
        f"{rec.document_type}, SOWsmith intends to award this work to your firm, subject to final "
        f"approvals (Supply Chain, Project Manager"
        + (", and Finance" if rec.finance_signoff else "") + ") and execution of contract documents."
        + legal_note + "\n\nWe will be in touch with next steps.\n\nRegards,\nSOWsmith Supply Chain"))
    for r in rec.rows:
        if r.compliant and r.bidder != rec.recommended:
            out.append((r.bidder, "REGRET",
                f"Dear {r.bidder},\n\nThank you for your proposal for the {rec.service_type} "
                f"{rec.document_type}. After careful evaluation, SOWsmith has elected to proceed with "
                "another bidder on this occasion. We value your participation and encourage you to bid "
                "on future opportunities.\n\nRegards,\nSOWsmith Supply Chain"))
    return out


def render_memo(rec: AwardRecommendation) -> str:
    def money(v):
        return f"${v:,.0f}" if v is not None else "— (no bid)"

    lines = [f"# Bid Evaluation & Award Recommendation — {rec.service_type} ({rec.document_type})", ""]
    lines += ["## Comparison", "",
              "| Bidder | Total (USD) | Schedule | Exclusions | Non-standard terms | Status |",
              "|---|---|---|---|---|---|"]
    for r in rec.rows:
        flags = ", ".join(r.legal_flags) if r.legal_flags else "—"
        sched = f"{r.schedule_days} days" if r.schedule_days else "—"
        status = "compliant" if r.compliant else "INCOMPLETE"
        lines.append(f"| {r.bidder} | {money(r.total_price)} | {sched} | {r.n_exclusions} | {flags} | {status} |")

    lines += ["", "## Recommendation (pending human approval)", ""]
    lines.append(f"**Recommended for award:** {rec.recommended}" if rec.recommended
                 else "**No award recommended** — no compliant bids.")
    for r in rec.reasons:
        lines.append(f"- {r}")

    lines += ["", "## Risks & flags", ""]
    lines += [f"- {r}" for r in rec.risks] or ["- None identified by the automated checks."]

    lines += ["", "## Review routing", "",
              f"REVIEW STATUS: {rec.review_status}"
              + (f"  — flagged: {', '.join(rec.legal_reasons)}" if rec.legal_reasons else "")]

    approvers = ["Supply Chain manager", "Project Manager"]
    if rec.review_status == LEGAL:
        approvers.append("Legal/Contracts")
    if rec.finance_signoff:
        approvers.append("Finance")
    lines += ["", "## Approvals required (human-in-the-loop)", "",
              "- " + " · ".join(approvers),
              "- The agent recommends and flags; **a person awards** (never auto-awarded)."]
    if rec.bafo_suggested:
        lines.append("- Consider a **Best and Final Offer (BAFO)** round — the top bids are close.")

    if rec.comparables:
        lines += ["", "## Comparable past bids (context)", ""]
        lines += [f"- {t}" for t in rec.comparables]

    notices = draft_notices(rec)
    if notices:
        lines += ["", "## Draft notifications (review before sending)", ""]
        for bidder, kind, text in notices:
            lines += [f"**{kind} — {bidder}**", "", "> " + text.replace("\n", "\n> "), ""]

    lines += ["---",
              "NOTE: This is an AI-assisted RECOMMENDATION generated by deterministic analysis "
              "(no invented numbers). SOWsmith does not auto-award — a buyer recommends, the Supply "
              "Chain manager / PM approve, and Finance signs off above threshold."]
    return "\n".join(lines) + "\n"


# A built-in sample so `bidpkg evaluate` and the demo run out-of-the-box (3 bids for a Pipeline SOW).
SAMPLE_BIDS = [
    {"bidder": "Permian Pipeline LLC", "total_price": 1250000, "schedule_days": 45,
     "exclusions": ["permits"], "terms": "Standard SOWsmith terms accepted."},
    {"bidder": "Lone Star Pipeliners", "total_price": 1180000, "schedule_days": 50,
     "exclusions": ["permits", "site restoration"],
     "terms": "Requests net-90 payment terms and a liquidated damages cap."},
    {"bidder": "West Texas Welding & Construction", "total_price": 1420000, "schedule_days": 40,
     "exclusions": ["permits"], "terms": "Standard SOWsmith terms accepted."},
]
