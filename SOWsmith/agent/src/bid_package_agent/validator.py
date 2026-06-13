"""Deterministic post-generation QA pass over a drafted bid package.

Runs with NO model call (zero token cost, no new hallucination surface) and catches the
failure modes the review flagged:
  * invented dollar amounts not present in the request (the no-invented-prices rule),
  * editorializing / speculative sentences about unfamiliar terms — the "Linus" failure,
    where the model invents a remark like "this looks like a person's name, confirm with
    the client" about a system/asset name it didn't recognize,
  * missing or renamed sections, and a missing/garbled version footer.

Findings are ADVISORY: they are surfaced to the human reviewer (and the audit log) to focus
the line-by-line read — they are not auto-rejections. This is the deterministic safety net
behind the probabilistic model.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .footer import parse_footer

# Phrases that signal the model is speculating / editorializing rather than stating scope.
_SPECULATION_RE = [re.compile(p, re.IGNORECASE) for p in [
    r"let the client confirm", r"confirm why", r"seems? to be", r"appears? to be",
    r"looks like (?:a|an)\b", r"presumably", r"\bI assume\b", r"might be a (?:person|name|typo)",
    r"strange name", r"unusual name", r"\bas an AI\b", r"I cannot be sure", r"is a person",
]]
_MONEY_RE = re.compile(r"\$\s?\d[\d,]*(?:\.\d+)?")
_SECTIONS = ["1. PROJECT OVERVIEW", "2. SCOPE OF WORK", "3. EXCLUSIONS & ASSUMPTIONS",
             "4. DELIVERABLES & SCHEDULE", "5. MATERIALS, EQUIPMENT & SITE CONDITIONS",
             "6. SAFETY, QUALITY & COMPLIANCE", "7. ACCEPTANCE & REFERENCES"]


@dataclass
class Finding:
    severity: str   # "warn" | "info"
    code: str
    message: str


def validate_draft(text: str, source: str = "") -> list[Finding]:
    findings: list[Finding] = []

    # 1) Structure — all seven sections present, in order.
    missing = [h for h in _SECTIONS if h not in text]
    if missing:
        findings.append(Finding("warn", "missing_sections",
            "Missing/renamed section(s): " + ", ".join(s.split(". ", 1)[-1] for s in missing) + "."))

    # 2) Footer present and parseable.
    if parse_footer(text) is None:
        findings.append(Finding("warn", "footer", "Version footer missing or unparseable."))

    # 3) No invented dollar amounts — every $ figure in the draft must appear in the request.
    src_money = {m.replace(" ", "") for m in _MONEY_RE.findall(source)}
    seen: set[str] = set()
    for m in _MONEY_RE.findall(text):
        key = m.replace(" ", "")
        if key not in src_money and key not in seen:
            seen.add(key)
            findings.append(Finding("warn", "invented_amount",
                f"Dollar amount {m.strip()!r} is in the draft but not in the request — verify it was not invented."))

    # 4) Editorializing / speculative sentences (the 'Linus' hallucination).
    for rx in _SPECULATION_RE:
        mt = rx.search(text)
        if mt:
            findings.append(Finding("warn", "speculation",
                f"Possible editorializing/hallucination near {mt.group(0)!r} — read this line carefully."))

    return findings


def summarize(findings: list[Finding]) -> str:
    if not findings:
        return "OK — no automated issues found (still requires human line-by-line review)."
    return " | ".join(f"[{f.code}] {f.message}" for f in findings)
