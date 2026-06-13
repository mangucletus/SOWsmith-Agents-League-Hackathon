"""Audit log writer — mirrors Power Automate action 10 (Create item in AuditLog).
Writes to a local CSV so every run is traceable, exactly the fields the SharePoint
AuditLog list uses."""
from __future__ import annotations

import csv
from datetime import datetime, timezone

from .config import Config

FIELDS = ["DraftFileName", "Author", "Reviewer", "Action", "Timestamp", "ReviewStatus", "Comments"]


def append_audit(cfg: Config, *, draft_filename: str, author: str, reviewer: str,
                 action: str, review_status: str, comments: str = "") -> dict:
    cfg.audit_csv.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "DraftFileName": draft_filename,
        "Author": author,
        "Reviewer": reviewer,
        "Action": action,
        "Timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ReviewStatus": review_status,
        "Comments": comments,
    }
    is_new = not cfg.audit_csv.exists()
    with cfg.audit_csv.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if is_new:
            w.writeheader()
        w.writerow(row)
    return row


def read_audit(cfg: Config) -> list[dict]:
    if not cfg.audit_csv.exists():
        return []
    with cfg.audit_csv.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
