# `frontend/` — User interface

The **Users · Chat Interface** layer of the architecture.

> In production the front-end is **Microsoft Teams** (the Copilot Studio agent is published there).
> `web-console/` is a local demo UI over the reference engine so you can see and show the agent
> working without the tenant.

## `web-console/`
A dependency-free single-page app (HTML/CSS/JS — no build step, no framework runtime). Served by the
engine's stdlib API.

```bash
# from the repo root
PYTHONPATH=agent/src python -m bid_package_agent.cli serve     # → http://127.0.0.1:8080
```

| File | Purpose |
|---|---|
| `index.html` | layout: sidebar + Ask / Draft / Audit panels |
| `styles.css` | styling (navy/amber/green, matching the architecture diagram) |
| `app.js` | logic; calls the JSON API (`/api/ask`, `/api/draft`, `/api/review`, `/api/audit`) |

Modes:
- **Ask** — Bid-document Q&A (Flow A): grounded answers with source citations.
- **Draft a bid package** — Flow B: form → generated SOW/RFP with review-status badge + reviewer, then
  Approve / Request changes / Reject controls (simulating the reviewer's Teams Adaptive Card).
- **Audit log** — the trail of generations and decisions.

Why not React/Vite? In a zero-build, offline, Python-managed environment a dependency-free SPA is the
fastest, most robust professional fit and is fully self-contained. Swapping in a React/Vite build later
is straightforward — the API contract stays the same.
