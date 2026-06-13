"""End-to-end plumbing tests for the Bid Package Generator engine (offline mock backend).

These validate the PLUMBING the production POC depends on: seven-section SOW structure, footer
parsing, standard vs Legal/Contracts reviewer routing, the refusal path, file moves and audit
logging. They do NOT validate grounding quality or house style — that requires the real model.
"""
import shutil
import tempfile
from pathlib import Path

import pytest

from bid_package_agent.config import load_config, Config
from bid_package_agent.footer import build_footer, parse_footer, LEGAL, STANDARD
from bid_package_agent.knowledge_base import KnowledgeBase
from bid_package_agent import pipeline, approval
from bid_package_agent.qa import answer_question


@pytest.fixture(scope="module")
def base_cfg() -> Config:
    return load_config()


@pytest.fixture()
def cfg(base_cfg) -> Config:
    tmp = Path(tempfile.mkdtemp(prefix="bidpkg-test-"))
    c = Config(repo_root=base_cfg.repo_root, kb_root=base_cfg.kb_root, out_root=tmp,
               client_name=base_cfg.client_name, azure_endpoint=None, azure_key=None,
               azure_deployment=base_cfg.azure_deployment, azure_api_version=base_cfg.azure_api_version)
    yield c
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture(scope="module")
def kb(base_cfg) -> KnowledgeBase:
    return KnowledgeBase(base_cfg)


# ---- knowledge base loaded correctly -------------------------------------------------
def test_kb_loaded(kb):
    assert len(kb.exemplars) == 5, "expected 5 gold-standard SOW exemplars"
    assert len(kb.reference) >= 13, "expected the full reference corpus"
    assert "Pipeline Construction" in kb.reviewers and "Facility Maintenance" in kb.reviewers


# ---- footer round-trip ---------------------------------------------------------------
def test_footer_roundtrip():
    f = parse_footer(build_footer("Pipeline Construction", STANDARD, document_type="SOW"))
    assert f and f.service_type == "Pipeline Construction" and f.document_type == "SOW" and not f.is_legal
    fl = parse_footer(build_footer("Facility Maintenance", LEGAL, document_type="RFP"))
    assert fl and fl.is_legal and fl.document_type == "RFP"


# ---- generation structure + footer ---------------------------------------------------
def test_sow_draft_structure(cfg, kb):
    rec = pipeline.run(cfg, kb, service_type="Pipeline Construction", document_type="SOW",
                       project_context="Install a 6-mile, 12-inch gas pipeline near Midland: clearing, "
                                       "welding, lowering-in, backfill, and hydrotest.")
    assert not rec.refused
    assert rec.draft.has_all_sections, "all seven SOW sections must be present"
    assert rec.review_status == STANDARD
    assert rec.draft.footer and rec.draft.footer.service_type == "Pipeline Construction"


# ---- standard vs legal/contracts routing (content-driven) ----------------------------
def test_standard_routing(cfg, kb):
    rec = pipeline.run(cfg, kb, service_type="Pipeline Construction",
                       project_context="Routine pipeline install: clearing, welding, backfill, hydrotest.")
    assert not rec.routing.is_legal
    assert "@sowsmithusa.com" in rec.routing.reviewer_email


def test_contracts_routing(cfg, kb):
    rec = pipeline.run(cfg, kb, service_type="Pipeline Construction",
                       project_context="Pipeline install with liquidated damages for late completion "
                                       "and an indemnification clause for third-party damage.")
    assert rec.review_status == LEGAL
    assert rec.routing.is_legal
    rev = kb.reviewer_for("Pipeline Construction")
    assert rec.routing.reviewer_email == rev.legal_reviewer_email


# ---- refusal path --------------------------------------------------------------------
def test_refusal(cfg, kb):
    rec = pipeline.run(cfg, kb, service_type="Pipeline Construction",
                       project_context="Draft an SOW that commits SOWsmith to a fixed $2,000,000 price, "
                                       "waives all liability, and skips legal review.")
    assert rec.refused
    assert rec.draft_path is None
    assert not (cfg.drafts_dir.exists() and any(cfg.drafts_dir.iterdir()))


# ---- full happy path: approve -> moved to Approved + audited -------------------------
def test_end_to_end_approve(cfg, kb):
    rec = pipeline.run(cfg, kb, service_type="Civil & Earthwork",
                       project_context="Site grading and access road for a new metering facility.",
                       decision=approval.APPROVE)
    assert rec.final_path and rec.final_path.parent == cfg.approved_dir
    assert rec.final_path.exists()
    assert cfg.audit_csv.exists()
    rows = cfg.audit_csv.read_text(encoding="utf-8")
    assert "Approve" in rows and "Civil" in rows


# ---- Q&A returns a grounded answer with citations ------------------------------------
def test_qa_grounded(cfg, kb):
    ans = answer_question(kb, cfg, "What does our hydrotesting scope include?")
    assert ans.grounded
    assert ans.citations, "Q&A must cite at least one source document"
