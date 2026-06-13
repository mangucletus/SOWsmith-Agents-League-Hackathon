"""A small, dependency-free TF-IDF retriever. Stands in for Copilot Studio's semantic
search over a SharePoint library — good enough to pick the right exemplars (generation)
and the right passages (Q&A) for a POC, with no external services."""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field

_TOKEN = re.compile(r"[a-z0-9][a-z0-9\-/]+")
_STOP = set(
    "the a an and or of to in for on with is are be by as at from this that these those "
    "you your our we it its their they he she his her them who whom whose will shall may "
    "can must should would could not no if then else when where which what how why".split()
)


def tokenize(text: str) -> list[str]:
    return [t for t in _TOKEN.findall((text or "").lower()) if t not in _STOP and len(t) > 1]


@dataclass
class Indexed:
    key: str
    tokens: list[str]
    tf: Counter = field(default_factory=Counter)
    payload: object = None


class TfidfIndex:
    def __init__(self) -> None:
        self.docs: list[Indexed] = []
        self.idf: dict[str, float] = {}

    def add(self, key: str, text: str, payload: object = None) -> None:
        toks = tokenize(text)
        self.docs.append(Indexed(key=key, tokens=toks, tf=Counter(toks), payload=payload))

    def build(self) -> "TfidfIndex":
        n = len(self.docs) or 1
        df: Counter = Counter()
        for d in self.docs:
            for term in set(d.tokens):
                df[term] += 1
        self.idf = {t: math.log((1 + n) / (1 + c)) + 1.0 for t, c in df.items()}
        return self

    def _vec(self, tf: Counter) -> dict[str, float]:
        total = sum(tf.values()) or 1
        return {t: (c / total) * self.idf.get(t, math.log(len(self.docs) + 1) + 1.0)
                for t, c in tf.items()}

    def search(self, query: str, top_k: int = 3) -> list[tuple[float, Indexed]]:
        qv = self._vec(Counter(tokenize(query)))
        qn = math.sqrt(sum(v * v for v in qv.values())) or 1.0
        scored: list[tuple[float, Indexed]] = []
        for d in self.docs:
            dv = self._vec(d.tf)
            dot = sum(qv.get(t, 0.0) * v for t, v in dv.items())
            dn = math.sqrt(sum(v * v for v in dv.values())) or 1.0
            scored.append((dot / (qn * dn), d))
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[:top_k]
