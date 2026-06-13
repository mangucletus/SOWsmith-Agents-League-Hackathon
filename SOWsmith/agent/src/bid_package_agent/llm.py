"""LLM backends.

* AzureOpenAILLM — real grounded generation against Azure OpenAI (GPT-4). Used only when
  AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_API_KEY are set. `openai` is imported lazily.
* MockLLM — a deterministic, offline generator. It produces a STRUCTURALLY valid seven-section
  SOW (and the correct refusal / legal-review behaviour) so the whole pipeline runs, is
  testable, and demos without secrets.

  IMPORTANT: the mock validates PLUMBING only — section structure, footer, review-status
  routing, refusal. It does NOT validate grounding quality, no-invented-numbers, or house
  style; those require the real model. Never report mock results as the headline "95% template
  compliance / 100% legal-flag routing" metric.
"""
from __future__ import annotations

import re
from datetime import date

from .footer import LEGAL, STANDARD, build_footer
from .safety import REFUSAL_MESSAGE


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", (text or "").strip())
    return [p.strip() for p in parts if p.strip()]


class MockLLM:
    name = "mock"

    def generate(self, system: str, user: str, inputs: dict | None = None) -> str:
        i = inputs or {}
        if i.get("is_unlawful"):
            return REFUSAL_MESSAGE

        stype = i.get("service_type", "General Services")
        dtype = i.get("document_type", "SOW")
        context = i.get("project_context", "")
        special = i.get("special_requirements") or ""
        is_legal = bool(i.get("is_legal"))
        ref_titles = i.get("exemplar_titles") or []
        client = i.get("client_name", "SOWsmith")

        sents = _sentences(context)
        # SCOPE OF WORK items from context clauses (kept generic; the mock never invents numbers)
        items = [f"The contractor shall: {s}" for s in sents]
        if not items:
            items = [f"The contractor shall perform the {stype} work as directed by {client}."]
        if is_legal:
            items.append("Commercial and legal terms are subject to Legal/Contracts review: "
                         "[NON-STANDARD TERMS - TO CONFIRM WITH LEGAL].")
        scope = "\n".join(f"{n}. {s}" for n, s in enumerate(items, 1))

        # OPEN QUESTIONS when the context is thin or terms are non-standard
        open_qs = []
        if len(context.split()) < 25:
            open_qs = [
                "What are the exact quantities, lengths or counts for this scope?",
                "What is the mobilization date and required schedule?",
                "Who supplies materials and major equipment?",
                "Which specifications or client standards apply?",
            ]
        if is_legal:
            open_qs.append("Which commercial/legal terms require Legal/Contracts sign-off?")
        open_block = ""
        if open_qs:
            open_block = "\nOPEN QUESTIONS\n" + "\n".join(f"- {q}" for q in open_qs[:5]) + "\n"

        refs = "\n".join(f"- {t}" for t in ref_titles) or "- (no exemplar titles supplied)"
        review = LEGAL if is_legal else STANDARD
        legal_note = (" Non-standard commercial/legal terms are left as placeholders pending "
                      "Legal/Contracts review." if is_legal else "")

        body = f"""1. PROJECT OVERVIEW
This {dtype} covers {stype} work for {client}.{legal_note}

2. SCOPE OF WORK
{scope}

3. EXCLUSIONS & ASSUMPTIONS
Work not expressly listed in the Scope of Work is excluded. The bid assumes normal site access, working hours and conditions unless stated otherwise.

4. DELIVERABLES & SCHEDULE
The contractor shall deliver the completed work per the agreed schedule: [MILESTONES & DURATIONS - TO CONFIRM].

5. MATERIALS, EQUIPMENT & SITE CONDITIONS
Materials and major equipment supply is as specified in project_context; site and access conditions are as provided. [TO CONFIRM where not supplied.]

6. SAFETY, QUALITY & COMPLIANCE
All work shall meet {client}'s safety-first requirements and applicable regulations (e.g. OSHA, DOT, PHMSA). Quality standards follow the referenced specifications.

7. ACCEPTANCE & REFERENCES
Acceptance is on completion and inspection per the referenced standards.
{refs}
{open_block}"""
        if special:
            body += f"\n(Note: special requirements considered — {special})\n"
        body += build_footer(stype, review, document_type=dtype, when=date.today().isoformat())
        return body


class AzureOpenAILLM:
    name = "azure-openai"

    def __init__(self, endpoint: str, api_key: str, deployment: str, api_version: str):
        from openai import AzureOpenAI  # lazy import — only when Azure is configured
        self.client = AzureOpenAI(azure_endpoint=endpoint, api_key=api_key, api_version=api_version)
        self.deployment = deployment

    def generate(self, system: str, user: str, inputs: dict | None = None) -> str:
        resp = self.client.chat.completions.create(
            model=self.deployment,
            temperature=0.2,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
        )
        return (resp.choices[0].message.content or "").strip()


def get_llm(cfg):
    if cfg.use_azure:
        return AzureOpenAILLM(cfg.azure_endpoint, cfg.azure_key,
                              cfg.azure_deployment, cfg.azure_api_version)
    return MockLLM()
