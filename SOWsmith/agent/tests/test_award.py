"""WS-4 (Bid Evaluation & Award) thin-slice coverage. Deterministic, offline — no model needed."""
from bid_package_agent.bid_eval import (normalize, evaluate_bids, render_memo, draft_notices,
                                        SAMPLE_BIDS, FINANCE_THRESHOLD)
from bid_package_agent.footer import LEGAL, STANDARD


def test_recommends_lowest_compliant_bid():
    # Amounts kept below the Finance threshold and >5% apart so the clean path has NO flags.
    subs = normalize([
        {"bidder": "A", "total_price": 125000, "schedule_days": 45, "exclusions": ["permits"], "terms": "standard"},
        {"bidder": "B", "total_price": 118000, "schedule_days": 50, "exclusions": ["permits"], "terms": "standard"},
        {"bidder": "C", "total_price": 142000, "schedule_days": 40, "exclusions": ["permits"], "terms": "standard"},
    ])
    rec = evaluate_bids(subs, service_type="Pipeline Construction")
    assert rec.recommended == "B"            # lowest compliant total
    assert rec.review_status == STANDARD
    assert rec.legal_reasons == []
    assert rec.finance_signoff is False and rec.bafo_suggested is False
    assert rec.risks == []                   # all clean, equal exclusions, not an outlier, below threshold


def test_non_standard_terms_route_award_to_legal_with_reasons():
    subs = normalize([
        {"bidder": "A", "total_price": 1250000, "terms": "Standard terms accepted."},
        {"bidder": "B", "total_price": 1180000, "terms": "Requests net-90 payment terms and a liquidated damages cap."},
    ])
    rec = evaluate_bids(subs, service_type="Pipeline Construction")
    assert rec.recommended == "B"
    assert rec.review_status == LEGAL
    assert rec.legal_reasons                 # explainable: which terms triggered it
    assert any("liquidated damages" in t for t in rec.legal_reasons)


def test_no_compliant_bids_yields_no_recommendation():
    rec = evaluate_bids(normalize([{"bidder": "A", "total_price": None, "terms": ""}]),
                        service_type="Pipeline Construction")
    assert rec.recommended is None
    assert any("no priced" in r.lower() for r in rec.risks)


def test_outlier_low_bid_is_flagged_for_scope_check():
    subs = normalize([
        {"bidder": "A", "total_price": 1000000, "terms": "standard"},
        {"bidder": "B", "total_price": 2000000, "terms": "standard"},
        {"bidder": "C", "total_price": 2100000, "terms": "standard"},
    ])
    rec = evaluate_bids(subs, service_type="Pipeline Construction")
    assert rec.recommended == "A"
    assert any("below the median" in r for r in rec.risks)


def test_engine_never_invents_numbers_memo_only_uses_bid_prices():
    rec = evaluate_bids(normalize(SAMPLE_BIDS), service_type="Pipeline Construction")
    memo = render_memo(rec)
    assert "Award Recommendation" in memo and "REVIEW STATUS" in memo
    # every dollar figure in the memo must be one of the supplied bid totals (no invented amounts)
    import re
    # allowed = the supplied bid totals + the fixed Finance policy threshold (not an invented bid amount)
    supplied = {f"${b['total_price']:,.0f}" for b in SAMPLE_BIDS} | {f"${FINANCE_THRESHOLD:,.0f}"}
    for amt in re.findall(r"\$\d[\d,]*", memo):
        assert amt in supplied, f"memo contains a dollar amount not in any bid: {amt}"


def test_finance_signoff_above_threshold():
    big = evaluate_bids(normalize([{"bidder": "A", "total_price": FINANCE_THRESHOLD + 1, "terms": "standard"}]),
                        service_type="Pipeline Construction")
    small = evaluate_bids(normalize([{"bidder": "A", "total_price": FINANCE_THRESHOLD - 1, "terms": "standard"}]),
                          service_type="Facility Maintenance")
    assert big.finance_signoff is True and any("Finance" in r for r in big.risks)
    assert small.finance_signoff is False


def test_bafo_suggested_when_top_bids_are_close():
    rec = evaluate_bids(normalize([
        {"bidder": "A", "total_price": 100000, "terms": "standard"},
        {"bidder": "B", "total_price": 103000, "terms": "standard"},  # within 5%
    ]), service_type="Pipeline Construction")
    assert rec.bafo_suggested is True
    assert any("BAFO" in r for r in rec.reasons)


def test_draft_notices_award_and_regret():
    rec = evaluate_bids(normalize(SAMPLE_BIDS), service_type="Pipeline Construction")
    notices = draft_notices(rec)
    kinds = {kind for _, kind, _ in notices}
    assert "AWARD" in kinds and "REGRET" in kinds
    award = [n for n in notices if n[1] == "AWARD"][0]
    assert award[0] == rec.recommended            # award goes to the recommended bidder
    # the recommended SAMPLE bid is > the finance threshold, so the award note mentions Finance
    assert "Finance" in award[2]
