"""Dependency-free JSON API + static file server for the web console.

Endpoints (all JSON unless noted):
  GET  /                     -> the console (frontend/web-console/index.html)
  GET  /<asset>              -> static asset from frontend/web-console
  GET  /api/health           -> { ok, backend, client }
  GET  /api/kb               -> exemplars, reference count, service types, reviewers
  POST /api/ask              -> { question } -> grounded answer + citations  (Flow A)
  POST /api/draft            -> draft inputs -> saved draft + routing          (Flow B)
  POST /api/review           -> { filename, decision, comments } -> file moved + audited
  POST /api/evaluate         -> { service_type, document_type, bids[] } -> award recommendation  (WS-4)
  GET  /api/audit            -> the audit log rows

Run:  PYTHONPATH=agent/src python -m bid_package_agent.cli serve   (then open http://127.0.0.1:8080)
"""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from ..config import Config
from ..knowledge_base import KnowledgeBase

_MIME = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
         ".js": "text/javascript; charset=utf-8", ".json": "application/json",
         ".svg": "image/svg+xml", ".ico": "image/x-icon"}


class Handler(BaseHTTPRequestHandler):
    cfg: Config = None        # set by serve()
    kb: KnowledgeBase = None
    web_dir: Path = None

    def log_message(self, *args):  # quieter console
        pass

    # ---- helpers ----
    def _send_json(self, obj, status=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        if not n:
            return {}
        try:
            return json.loads(self.rfile.read(n).decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return {}

    def _serve_static(self, path: str):
        rel = path.lstrip("/") or "index.html"
        target = (self.web_dir / rel).resolve()
        # path-traversal guard
        if self.web_dir not in target.parents and target != self.web_dir / rel:
            return self._send_json({"error": "not found"}, 404)
        if not target.is_file():
            return self._send_json({"error": "not found", "path": rel}, 404)
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", _MIME.get(target.suffix.lower(), "application/octet-stream"))
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    # ---- routes ----
    def do_GET(self):
        route = urlparse(self.path).path
        if route == "/api/health":
            return self._send_json({"ok": True,
                                    "backend": "azure-openai" if self.cfg.use_azure else "offline-mock",
                                    "client": self.cfg.client_name})
        if route == "/api/kb":
            return self._send_json({
                "exemplars": [{"service_type": d.service_type, "title": d.title, "filename": d.filename}
                              for d in self.kb.exemplars],
                "reference_count": len(self.kb.reference),
                "service_types": sorted(self.kb.reviewers.keys()),
                "reviewers": [{"service_type": r.service_type, "reviewer": r.reviewer_email,
                               "legal_reviewer": r.legal_reviewer_email}
                              for r in self.kb.reviewers.values()],
            })
        if route == "/api/audit":
            from ..audit import read_audit
            return self._send_json({"rows": read_audit(self.cfg)})
        return self._serve_static(route)

    def do_POST(self):
        route = urlparse(self.path).path
        data = self._read_json()
        try:
            if route == "/api/ask":
                from ..qa import answer_question
                ans = answer_question(self.kb, self.cfg, (data.get("question") or "").strip())
                return self._send_json({
                    "question": ans.question, "answer": ans.answer, "grounded": ans.grounded,
                    "citations": [{"title": c.title, "filename": c.filename, "score": c.score}
                                  for c in ans.citations]})
            if route == "/api/draft":
                from ..pipeline import run
                rec = run(self.cfg, self.kb,
                          service_type=(data.get("service_type") or "").strip(),
                          document_type=(data.get("document_type") or "SOW").strip() or "SOW",
                          project_context=(data.get("project_context") or "").strip(),
                          special_requirements=(data.get("special_requirements") or "").strip())
                if rec.refused:
                    return self._send_json({"refused": True, "text": rec.draft.text,
                                            "reason": rec.draft.refusal_reason})
                return self._send_json({
                    "refused": False, "text": rec.draft.text, "service_type": rec.service_type,
                    "document_type": rec.draft.document_type,
                    "review_status": rec.review_status, "is_legal": rec.routing.is_legal,
                    "reviewer": rec.routing.reviewer_email, "cc": rec.routing.cc_email,
                    "reviewer_found": rec.routing.reviewer_found,
                    "filename": rec.draft_path.name if rec.draft_path else None,
                    "sections_present": len(rec.draft.sections_present),
                    "open_questions": rec.open_questions,
                    "legal_reasons": rec.legal_reasons,
                    "validation": [{"severity": f.severity, "code": f.code, "message": f.message}
                                   for f in rec.validation]})
            if route == "/api/review":
                from ..pipeline import decide
                out = decide(self.cfg, self.kb, filename=(data.get("filename") or "").strip(),
                             decision=(data.get("decision") or "").strip(),
                             comments=(data.get("comments") or "").strip())
                return self._send_json(out)
            if route == "/api/evaluate":
                from ..pipeline import evaluate_award
                from ..bid_eval import normalize, render_memo
                arec = evaluate_award(
                    self.cfg, self.kb,
                    service_type=(data.get("service_type") or "Pipeline Construction").strip(),
                    document_type=(data.get("document_type") or "SOW").strip() or "SOW",
                    submissions=normalize(data.get("bids") or []))
                rec = arec.recommendation
                return self._send_json({
                    "service_type": rec.service_type, "document_type": rec.document_type,
                    "recommended": rec.recommended, "review_status": rec.review_status,
                    "legal_reasons": rec.legal_reasons, "reasons": rec.reasons, "risks": rec.risks,
                    "finance_signoff": rec.finance_signoff, "bafo_suggested": rec.bafo_suggested,
                    "approver": arec.routing.reviewer_email, "cc": arec.routing.cc_email,
                    "comparables": rec.comparables,
                    "rows": [{"bidder": r.bidder, "total_price": r.total_price,
                              "schedule_days": r.schedule_days, "n_exclusions": r.n_exclusions,
                              "legal_flags": r.legal_flags, "compliant": r.compliant}
                             for r in rec.rows],
                    "memo": render_memo(rec)})
        except FileNotFoundError as e:
            return self._send_json({"error": str(e)}, 404)
        except Exception as e:  # surface errors as JSON for the console
            return self._send_json({"error": f"{type(e).__name__}: {e}"}, 500)
        return self._send_json({"error": "unknown route"}, 404)


def make_server(cfg: Config, host: str = "127.0.0.1", port: int = 8080) -> ThreadingHTTPServer:
    """Build (but don't start) the server. Tests run this in a thread; `serve()` blocks on it."""
    Handler.cfg = cfg
    Handler.kb = KnowledgeBase(cfg)
    Handler.web_dir = (cfg.repo_root / "frontend" / "web-console").resolve()
    return ThreadingHTTPServer((host, port), Handler)


def serve(cfg: Config, host: str = "127.0.0.1", port: int = 8080) -> None:
    srv = make_server(cfg, host, port)
    backend = "Azure OpenAI" if cfg.use_azure else "OFFLINE MOCK"
    print(f"Bid Package Generator web console on http://{host}:{port}   (LLM backend: {backend})")
    print("Press Ctrl+C to stop.")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped.")
        srv.server_close()
