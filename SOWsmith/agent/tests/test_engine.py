"""Engine coverage beyond the spine: Q&A, footer edge cases, the full eval set, and the
two-step decide() path. Offline mock backend."""
import shutil
import tempfile
from pathlib import Path

import pytest

from bid_package_agent.config import Config, load_config
from bid_package_agent.footer import parse_footer, build_footer, LEGAL, STANDARD
from bid_package_agent.knowledge_base import KnowledgeBase
from bid_package_agent import pipeline, approval
from bid_package_agent.qa import answer_question
from bid_package_agent.evaluation import evaluate, INTENTS
from bid_package_agent.safety import needs_legal_review, matched_legal_terms
from bid_package_agent.validator import validate_draft


@pytest.fixture(scope="module")
def base_cfg() -> Config:
    return load_config()


def test_needs_legal_review_word_boundaries():
    # Regression guard: bare substring matching used to misfire on ordinary words.
    assert needs_legal_review("the client supplies all materials") is False   # 'lien' in 'client'
    assert needs_legal_review("pump reliability targets per spec") is False    # 'liability' in 'reliability'
    assert needs_legal_review("allow water to flow naturally downhill") is False
    # Real legal triggers, including 'indemnity' (the former false negative) and stems.
    assert needs_legal_review("includes an indemnity clause") is True
    assert needs_legal_review("indemnification for third-party damage") is True
    assert needs_legal_review("liquidated damages and a performance bond") is True
    assert needs_legal_review("retainage and hold harmless terms") is True


def test_matched_legal_terms_explainable():
    reasons = matched_legal_terms("liquidated damages and an indemnity clause")
    assert "liquidated damages" in reasons
    assert "indemnification/indemnity" in reasons          # friendly label, not the 'indemni' stem
    assert matched_legal_terms("routine valve servicing and painting") == []


def test_validator_flags_invented_amount_and_speculation():
    draft = (
        "1. PROJECT OVERVIEW\nThe system named Linus looks like a person's name, so let the "
        "client confirm why.\n2. SCOPE OF WORK\nInstall pipe for $4,500,000.\n"
        "3. EXCLUSIONS & ASSUMPTIONS\nx\n4. DELIVERABLES & SCHEDULE\nx\n"
        "5. MATERIALS, EQUIPMENT & SITE CONDITIONS\nx\n6. SAFETY, QUALITY & COMPLIANCE\nx\n"
        "7. ACCEPTANCE & REFERENCES\nx\n---\nVERSION: v0.1 DRAFT\nDATE: 2026-06-06\n"
        "SERVICE TYPE: Pipeline Construction\nDOCUMENT TYPE: SOW\nREVIEW STATUS: STANDARD REVIEW\n---"
    )
    codes = {f.code for f in validate_draft(draft, source="install a pipeline near Midland")}
    assert "invented_amount" in codes      # $4,500,000 is not in the request
    assert "speculation" in codes          # the 'Linus' editorializing


def test_validator_clean_engine_draft_has_no_findings(base_cfg):
    kb = KnowledgeBase(base_cfg)
    r = pipeline.run(base_cfg, kb, service_type="Pipeline Construction", document_type="SOW",
                     project_context="Install a 6-mile 12-inch gas pipeline near Midland: weld, "
                                     "lower-in, hydrotest.")
    assert r.validation == []
    assert r.legal_reasons == []


@pytest.fixture()
def cfg(base_cfg) -> Config:
    tmp = Path(tempfile.mkdtemp(prefix="bidpkg-eng-"))
    c = Config(repo_root=base_cfg.repo_root, kb_root=base_cfg.kb_root, out_root=tmp,
               client_name=base_cfg.client_name, azure_endpoint=None, azure_key=None,
               azure_deployment=base_cfg.azure_deployment, azure_api_version=base_cfg.azure_api_version)
    yield c
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture(scope="module")
def kb(base_cfg) -> KnowledgeBase:
    return KnowledgeBase(base_cfg)


def test_footer_edge_cases():
    assert parse_footer("no footer here") is None
    f = parse_footer("text\n" + build_footer("Coating & Insulation", STANDARD, document_type="SOW", version="v2.1"))
    assert f.service_type == "Coating & Insulation" and f.version == "v2.1"


def test_qa_no_match_is_honest(cfg, kb):
    ans = answer_question(kb, cfg, "what is the airspeed velocity of an unladen swallow?")
    assert not ans.grounded
    assert "don't have" in ans.answer.lower()


def test_qa_cites_relevant_doc(cfg, kb):
    ans = answer_question(kb, cfg, "what is in scope for a hydrotest?")
    assert ans.grounded and ans.citations
    assert any("Hydrotest" in c.title or "Pipeline" in c.title for c in ans.citations)


def test_review_status_is_content_driven(cfg, kb):
    # same service type -> standard for a clean scope, contracts for non-standard terms
    clean = pipeline.run(cfg, kb, service_type="Facility Maintenance",
                         project_context="Routine valve servicing and painting during a turnaround.")
    assert clean.review_status == STANDARD
    terms = pipeline.run(cfg, kb, service_type="Facility Maintenance",
                         project_context="Maintenance with a performance bond and indemnification clause.")
    assert terms.review_status == LEGAL


def test_decide_moves_and_audits(cfg, kb):
    rec = pipeline.run(cfg, kb, service_type="Electrical & Instrumentation",
                       project_context="Install and terminate instrument wiring; loop checks.")
    assert rec.draft_path.exists()
    out = pipeline.decide(cfg, kb, filename=rec.draft_path.name, decision=approval.APPROVE)
    assert out["final_library"] == "Approved"
    assert (cfg.approved_dir / rec.draft_path.name).exists()
    assert cfg.audit_csv.exists() and "Approve" in cfg.audit_csv.read_text()


@pytest.mark.parametrize("evil", [
    "../../../../etc/passwd", "../secret.md", "..\\..\\win.ini", "sub/dir.md", ".hidden", "", "..",
])
def test_decide_rejects_path_traversal(cfg, kb, evil):
    # a crafted filename must never read/move files outside the Drafts library
    with pytest.raises(FileNotFoundError):
        pipeline.decide(cfg, kb, filename=evil, decision=approval.APPROVE)


def test_full_eval_plumbing(cfg, kb):
    rows = evaluate(cfg, kb)
    assert len(rows) == len(INTENTS) == 10
    lawful = [r for r in rows if r.test_id != "T-10"]
    assert all(r.structure_ok and r.footer_ok and r.review_ok for r in lawful)
    refusal = next(r for r in rows if r.test_id == "T-10")
    assert refusal.refusal_ok  # the unlawful intent is refused
    # the three legal-trigger intents must be flagged LEGAL
    for tid in ("T-07", "T-08", "T-09"):
        assert next(r for r in rows if r.test_id == tid).review_ok
