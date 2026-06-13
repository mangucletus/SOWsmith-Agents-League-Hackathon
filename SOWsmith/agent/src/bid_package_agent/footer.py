"""Parse and build the version footer block.

The footer is the contract between the generator and the approval flow. In the production
POC, Power Automate (action 3) extracts SERVICE TYPE and REVIEW STATUS from this block with
indexOf()/substring(). Here we parse it with a regex — same fields, same meaning.

    ---
    VERSION: v0.1 DRAFT
    DATE: 2026-06-05
    SERVICE TYPE: Pipeline Construction
    DOCUMENT TYPE: SOW
    REVIEW STATUS: STANDARD REVIEW
    ---
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

STANDARD = "STANDARD REVIEW"
LEGAL = "LEGAL REVIEW REQUIRED"   # non-standard terms -> Legal / Contracts review

_FIELD = re.compile(r"^\s*([A-Z][A-Z ]+?):\s*(.+?)\s*$", re.MULTILINE)


@dataclass
class Footer:
    version: str
    date: str
    service_type: str
    document_type: str
    review_status: str

    @property
    def is_legal(self) -> bool:
        return self.review_status.strip().upper() == LEGAL


def build_footer(service_type: str, review_status: str, document_type: str = "SOW",
                 version: str = "v0.1 DRAFT", when: str | None = None) -> str:
    when = when or date.today().isoformat()
    return (
        "\n---\n"
        f"VERSION: {version}\n"
        f"DATE: {when}\n"
        f"SERVICE TYPE: {service_type}\n"
        f"DOCUMENT TYPE: {document_type}\n"
        f"REVIEW STATUS: {review_status}\n"
        "---\n"
    )


def parse_footer(text: str) -> Footer | None:
    """Return the Footer parsed from the version-block in the text, or None."""
    fields = {k.strip(): v.strip() for k, v in _FIELD.findall(text)}
    if "SERVICE TYPE" not in fields or "REVIEW STATUS" not in fields:
        return None
    return Footer(
        version=fields.get("VERSION", ""),
        date=fields.get("DATE", ""),
        service_type=fields["SERVICE TYPE"],
        document_type=fields.get("DOCUMENT TYPE", "SOW"),
        review_status=fields["REVIEW STATUS"],
    )
