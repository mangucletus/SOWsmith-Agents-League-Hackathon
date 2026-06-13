# Build runbook (4 weeks)

The week-by-week plan, mapped to this repo. Problem framing and tooling rationale:
[`PROBLEM-AND-APPROACH.md`](PROBLEM-AND-APPROACH.md); the source brief this POC implements:
[`assets/source-brief/Supply Chain Department.pdf`](assets/source-brief/) (Workstream 1 — Bid Package Generation).

> Rule of thumb: each week has **one** primary deliverable. If you can't demo it by Friday,
> stop and replan rather than rolling work forward.

## Week 0 — Setup & discovery
- Confirm tenant access (Copilot Studio, SharePoint, Power Automate, Azure OpenAI).
- Pick **one** service type for the first end-to-end pass (recommended: **Pipeline Construction** or **Facility Maintenance**).
- Identify a standard reviewer + a legal reviewer; book a weekly review slot.
- Do the [`MANUAL-SETUP.md`](MANUAL-SETUP.md) steps 0–2 (site + provisioning).
- **Repo support:** `infrastructure/` provisions SharePoint; `knowledge-base/` is the content.

## Week 1 — Knowledge base & skeleton agent
- Curate the KB (already built here — 5 exemplars + broad reference set). *60% of quality is here.*
- Create the agent; **"Use AI in conversation" OFF**; add SharePoint knowledge (bare URL).
- Build Topic 1's Adaptive Card input; echo inputs back (don't wire generation yet).
- **Deliverable:** an agent in Teams that collects structured input.
- **Repo support:** `knowledge-base/`, `approval-workflow/adaptive-card-input.json`,
  `copilot-studio/topics-and-trigger-phrases.md`.

## Week 2 — Generation logic & prompt
- Add the Generative Answers node; scope to **Approved-Exemplars only**; paste
  `copilot-studio/system-prompt.txt`; citations ON.
- Build Topic 2 (Q&A) scoped to **Reference-Library**.
- Build the **eval set in Week 2, not Week 4** (it's already here — `bidpkg eval`).
- **Deliverable:** a working generator producing a structurally compliant SOW.
- **Repo support:** `copilot-studio/`, and the engine (`agent/`) to A/B the prompt locally.

## Week 3 — Power Automate workflow & polish
- Build the 10-action approval flow in Power Automate (`approval-workflow/flow-definition.md`),
  trigger on file creation in **Drafts**.
- Add error handling (retry, catch scope, 5-day timeout), and a "regenerate with adjustments" path.
- **Deliverable:** end-to-end — input → draft → reviewer notified → approval logged.
- **Repo support:** `approval-workflow/`, mirrored by `agent/.../{approval,pipeline,audit}.py`
  (`bidpkg demo` runs the same path locally).

## Week 4 — Test, measure, demo
- Run the 10-intent eval **through the live agent** ([`EVALUATION.md`](EVALUATION.md)); score it.
- Produce: the one-page architecture diagram (`docs/assets/Bid-Package-Generator_Architecture_Diagram.html`),
  a 10-minute demo video, a one-page write-up.
- Run it live with the Supply Chain champion; capture their quote.
- **Deliverable:** measured results + demo materials.

## Validate the logic any time (no tenant needed)
```bash
python -m pytest -q                                          # plumbing tests
PYTHONPATH=agent/src python -m bid_package_agent.cli demo     # scripted end-to-end
PYTHONPATH=agent/src python -m bid_package_agent.cli serve    # web console
```
