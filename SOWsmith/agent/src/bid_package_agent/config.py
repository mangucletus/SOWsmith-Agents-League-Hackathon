"""Environment-driven configuration. No secrets are hard-coded; everything comes from
env vars (optionally loaded from a gitignored .env). If Azure OpenAI is not configured,
the engine falls back to the deterministic offline mock."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _repo_root() -> Path:
    """Walk up from this file to the repo root (dir holding pyproject.toml/.git)."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pyproject.toml").is_file() or (parent / ".git").exists():
            return parent
    # fallback: agent/src/bid_package_agent/config.py -> repo root is four parents up
    return here.parents[3]


def _load_dotenv(root: Path) -> None:
    """Minimal .env loader (no python-dotenv dependency). Does not overwrite real env."""
    env = root / ".env"
    if not env.is_file():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip().strip('"').strip("'")
        os.environ.setdefault(key, val)


@dataclass(frozen=True)
class Config:
    repo_root: Path
    kb_root: Path
    out_root: Path
    client_name: str
    azure_endpoint: str | None
    azure_key: str | None
    azure_deployment: str
    azure_api_version: str

    @property
    def use_azure(self) -> bool:
        return bool(self.azure_endpoint and self.azure_key)

    @property
    def exemplars_dir(self) -> Path:
        return self.kb_root / "Approved-Exemplars"

    @property
    def reference_dir(self) -> Path:
        return self.kb_root / "Reference-Library"

    @property
    def reviewers_xlsx(self) -> Path:
        return self.kb_root / "Lists" / "Reviewers.xlsx"

    @property
    def drafts_dir(self) -> Path:
        return self.out_root / "Drafts"

    @property
    def approved_dir(self) -> Path:
        return self.out_root / "Approved"

    @property
    def rejected_dir(self) -> Path:
        return self.out_root / "Rejected"

    @property
    def evaluations_dir(self) -> Path:
        return self.out_root / "Evaluations"

    @property
    def audit_csv(self) -> Path:
        return self.out_root / "AuditLog.csv"


def load_config() -> Config:
    root = _repo_root()
    _load_dotenv(root)
    kb = Path(os.environ.get("BIDPKG_KB_ROOT")
              or (root / "knowledge-base" / "sharepoint-online-knowledge-base"))
    out = Path(os.environ.get("BIDPKG_OUT_ROOT") or (root / "var" / "run"))
    return Config(
        repo_root=root,
        kb_root=kb,
        out_root=out,
        client_name=os.environ.get("BIDPKG_CLIENT_NAME", "SOWsmith"),
        azure_endpoint=(os.environ.get("AZURE_OPENAI_ENDPOINT") or "").strip() or None,
        azure_key=(os.environ.get("AZURE_OPENAI_API_KEY") or "").strip() or None,
        azure_deployment=os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
        azure_api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21"),
    )
