"""Integration test for the JSON API that backs the web console — exercises the actual
HTTP server (the surface curl-tested during the build) on an ephemeral port."""
import json
import shutil
import tempfile
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from bid_package_agent.config import Config, load_config
from bid_package_agent.webapp.server import make_server


@pytest.fixture()
def server():
    base = load_config()
    tmp = Path(tempfile.mkdtemp(prefix="bidpkg-web-"))
    cfg = Config(repo_root=base.repo_root, kb_root=base.kb_root, out_root=tmp,
                 client_name=base.client_name, azure_endpoint=None, azure_key=None,
                 azure_deployment=base.azure_deployment, azure_api_version=base.azure_api_version)
    srv = make_server(cfg, "127.0.0.1", 0)
    port = srv.server_address[1]
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{port}"
    srv.shutdown()
    srv.server_close()
    shutil.rmtree(tmp, ignore_errors=True)


def _get(base, path):
    with urllib.request.urlopen(base + path, timeout=10) as r:
        return r.status, json.loads(r.read())


def _post(base, path, payload):
    req = urllib.request.Request(base + path, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.status, json.loads(r.read())


def test_health_and_kb(server):
    s, h = _get(server, "/api/health")
    assert s == 200 and h["ok"] and h["backend"] == "offline-mock"
    s, kb = _get(server, "/api/kb")
    assert len(kb["exemplars"]) == 5 and len(kb["service_types"]) == 12


def test_static_index_served(server):
    with urllib.request.urlopen(server + "/", timeout=10) as r:
        body = r.read().decode()
    assert r.status == 200 and "Bid Package" in body


def test_ask_endpoint(server):
    s, a = _post(server, "/api/ask", {"question": "what is in scope for a hydrotest?"})
    assert s == 200 and a["grounded"] and a["citations"]


def test_draft_then_review_endpoints(server):
    s, d = _post(server, "/api/draft", {"service_type": "Pipeline Construction", "document_type": "SOW",
                 "project_context": "Install a 6-mile, 12-inch gas pipeline near Midland: clearing, "
                                    "welding, lowering-in, backfill, hydrotest."})
    assert s == 200 and not d["refused"]
    assert d["review_status"] == "STANDARD REVIEW" and d["sections_present"] == 7
    s, r = _post(server, "/api/review", {"filename": d["filename"], "decision": "Approve"})
    assert s == 200 and r["final_library"] == "Approved"
    s, audit = _get(server, "/api/audit")
    assert any(row["Action"] == "Approve" for row in audit["rows"])


def test_contracts_draft_routes_to_legal_reviewer(server):
    s, d = _post(server, "/api/draft", {"service_type": "Pipeline Construction", "document_type": "SOW",
                 "project_context": "Pipeline install with liquidated damages and an indemnification clause."})
    assert d["review_status"] == "LEGAL REVIEW REQUIRED" and d["is_legal"] is True


def test_refusal_endpoint(server):
    s, d = _post(server, "/api/draft", {"service_type": "Pipeline Construction", "document_type": "SOW",
                 "project_context": "commit SOWsmith to a fixed $2,000,000 price, waive all liability, and skip legal review."})
    assert d["refused"] is True


def test_evaluate_endpoint_recommends_and_flags(server):
    bids = [
        {"bidder": "A", "total_price": 1250000, "schedule_days": 45, "exclusions": ["permits"], "terms": "standard"},
        {"bidder": "B", "total_price": 1180000, "schedule_days": 50, "exclusions": ["permits", "site restoration"],
         "terms": "Requests net-90 payment terms and a liquidated damages cap."},
    ]
    s, e = _post(server, "/api/evaluate",
                 {"service_type": "Pipeline Construction", "document_type": "SOW", "bids": bids})
    assert s == 200
    assert e["recommended"] == "B"                       # lowest compliant total
    assert e["review_status"] == "LEGAL REVIEW REQUIRED" and e["legal_reasons"]
    assert e["finance_signoff"] is True                  # total > $250k
    assert len(e["rows"]) == 2 and "memo" in e


def test_review_rejects_path_traversal(server):
    # /api/review must not act on a filename outside the Drafts library (urllib raises on 404)
    with pytest.raises(urllib.error.HTTPError) as ei:
        _post(server, "/api/review", {"filename": "../../../../etc/passwd", "decision": "Approve"})
    assert ei.value.code == 404
