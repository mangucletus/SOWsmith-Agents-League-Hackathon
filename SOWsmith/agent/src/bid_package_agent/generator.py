"""Flow B — draft generation. Mirrors Copilot Studio Topic 1 (Draft a Bid Package):
retrieve exemplars from Approved-Exemplars, build the system prompt + inputs, call the
model (Azure OpenAI or the offline mock), and parse the resulting footer."""
from __future__ import annotations

from dataclasses import dataclass, field

from .config import Config
from .footer import LEGAL, STANDARD, Footer, parse_footer
from .knowledge_base import KnowledgeBase
from .llm import get_llm
from .prompts import build_user_message, system_prompt
from .safety import REFUSAL_MESSAGE, is_unlawful, matched_legal_terms
from .validator import Finding, validate_draft

SOW_SECTIONS = ["1. PROJECT OVERVIEW", "2. SCOPE OF WORK", "3. EXCLUSIONS & ASSUMPTIONS",
                "4. DELIVERABLES & SCHEDULE", "5. MATERIALS, EQUIPMENT & SITE CONDITIONS",
                "6. SAFETY, QUALITY & COMPLIANCE", "7. ACCEPTANCE & REFERENCES"]


@dataclass
class DraftResult:
    refused: bool
    text: str
    service_type: str
    document_type: str
    review_status: str | None
    footer: Footer | None
    exemplars_used: list[str] = field(default_factory=list)
    refusal_reason: str | None = None
    legal_reasons: list[str] = field(default_factory=list)   # WHY it was flagged LEGAL (explainability)
    validation: list[Finding] = field(default_factory=list)  # deterministic QA findings (advisory)

    @property
    def sections_present(self) -> list[str]:
        return [h for h in SOW_SECTIONS if h in self.text]

    @property
    def has_all_sections(self) -> bool:
        return len(self.sections_present) == len(SOW_SECTIONS)


def generate_draft(kb: KnowledgeBase, cfg: Config, *, service_type: str, document_type: str = "SOW",
                   project_context: str, special_requirements: str = "", llm=None) -> DraftResult:
    llm = llm or get_llm(cfg)

    # Refuse outright (mirrors the prompt's WHEN TO REFUSE rule).
    if is_unlawful(project_context):
        return DraftResult(refused=True, text=REFUSAL_MESSAGE, service_type=service_type,
                           document_type=document_type, review_status=None, footer=None,
                           refusal_reason="improper request")

    exemplars = kb.exemplars_for(service_type, project_context)
    excerpts = "\n\n".join(f"--- {e.title} ---\n{e.text[:1500]}" for e in exemplars) \
        or "(no exemplars found in Approved-Exemplars)"
    # For bid packages the review tier depends on the CONTENT (are non-standard commercial /
    # legal terms present?), not the service type — the same service can be standard or
    # contracts-review. Content keywords drive it; a KB service type explicitly flagged
    # LEGAL also forces it.
    known_status = kb.review_status_for(service_type)
    legal_reasons = matched_legal_terms(service_type, project_context, special_requirements)
    is_legal = bool(legal_reasons) or (bool(known_status) and known_status.strip().upper() == LEGAL)

    text = llm.generate(
        system_prompt(cfg.client_name),
        build_user_message(service_type, document_type, project_context, special_requirements, excerpts),
        inputs={
            "service_type": service_type, "document_type": document_type,
            "project_context": project_context, "special_requirements": special_requirements,
            "exemplar_titles": [e.title for e in exemplars], "is_legal": is_legal,
            "is_unlawful": False, "client_name": cfg.client_name,
        },
    )

    # The real model may also refuse via the prompt's canned message.
    if text.strip().lower().startswith("i cannot draft this"):
        return DraftResult(refused=True, text=text, service_type=service_type,
                           document_type=document_type, review_status=None, footer=None,
                           exemplars_used=[e.filename for e in exemplars], refusal_reason="model refusal")

    ftr = parse_footer(text)
    review = ftr.review_status if ftr else (LEGAL if is_legal else STANDARD)
    validation = validate_draft(text, f"{project_context} {special_requirements}")
    return DraftResult(refused=False, text=text, service_type=service_type, document_type=document_type,
                       review_status=review, footer=ftr, exemplars_used=[e.filename for e in exemplars],
                       legal_reasons=legal_reasons, validation=validation)
