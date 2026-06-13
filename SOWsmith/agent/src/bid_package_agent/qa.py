"""Flow A — Bid-document Q&A. Mirrors Copilot Studio Topic 2: RAG over the Reference-Library
(prior bid packages + the clause library), returning a grounded answer with citations."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .config import Config
from .knowledge_base import KnowledgeBase
from .llm import get_llm
from .retrieval import tokenize

_QA_SYSTEM = (
    "You are the Bid-Document Q&A assistant for {client}. Answer ONLY from the provided "
    "context passages, which come from approved prior bid packages and the clause library. "
    "Be concise and plain. If the answer is not in the context, say you don't have that "
    "information and suggest the most relevant document. Always cite the source titles you used."
)


@dataclass
class Citation:
    title: str
    filename: str
    score: float


@dataclass
class Answer:
    question: str
    answer: str
    grounded: bool
    citations: list[Citation] = field(default_factory=list)


def _best_sentences(text: str, question: str, limit: int = 3) -> list[str]:
    qtok = set(tokenize(question))
    sents = re.split(r"(?<=[.!?])\s+|\n", text)
    scored = []
    for s in sents:
        s = s.strip()
        if len(s) < 25:
            continue
        overlap = len(qtok & set(tokenize(s)))
        if overlap:
            scored.append((overlap, s))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [s for _, s in scored[:limit]]


def answer_question(kb: KnowledgeBase, cfg: Config, question: str, *, k: int = 3, llm=None) -> Answer:
    hits = kb.search_reference(question, k=k)
    hits = [(s, d) for s, d in hits if s > 0.0]
    citations = [Citation(d.title, d.filename, round(s, 3)) for s, d in hits]
    if not hits:
        return Answer(question, "I don't have that information in the published bid-document set. "
                                "Please check with the Estimating or Contracts team, or the current "
                                "project documents.", grounded=False)

    if cfg.use_azure:
        llm = llm or get_llm(cfg)
        context = "\n\n".join(
            f"[{i+1}] {d.title} ({d.filename})\n{d.text[:1500]}" for i, (_, d) in enumerate(hits))
        ans = llm.generate(
            _QA_SYSTEM.format(client=cfg.client_name),
            f"Question: {question}\n\nContext:\n{context}\n\nAnswer with citations.",
        )
        return Answer(question, ans, grounded=True, citations=citations)

    # Offline mock: stitch the most relevant sentences from the top document(s).
    top_doc = hits[0][1]
    sents = _best_sentences(top_doc.text, question) or _best_sentences(hits[0][1].text, top_doc.title)
    body = " ".join(sents) if sents else top_doc.text[:400]
    cited = ", ".join(c.title for c in citations[:2])
    answer = f"{body}\n\n(Source: {cited}.)"
    return Answer(question, answer, grounded=True, citations=citations)
