# Example outputs

Real outputs produced by the reference engine's **offline mock** (no Azure key needed), to show the
*shape* of what the Bid Package Agent generates and how routing works. Regenerate them any time with:

```bash
PYTHONPATH=agent/src python -m bid_package_agent.cli draft \
  --type "Pipeline Construction" --doc SOW --context "…your project brief…"
```

### WS-1 · Bid Package Generation (Flow B)
| File | What it demonstrates |
|---|---|
| [`sample-SOW_STANDARD.md`](sample-SOW_STANDARD.md) | A seven-section SOW with a parseable footer → `REVIEW STATUS: STANDARD REVIEW` (routes to the Supply Chain reviewer). |
| [`sample-SOW_LEGAL-REVIEW.md`](sample-SOW_LEGAL-REVIEW.md) | The **same service type** but with liquidated damages + indemnification + net-90 terms → `REVIEW STATUS: LEGAL REVIEW REQUIRED` (routes to Legal/Contracts). Non-standard terms are left as bracketed placeholders. |
| [`sample-RFP_STANDARD.md`](sample-RFP_STANDARD.md) | A **Request for Proposal** (`DOCUMENT TYPE: RFP`) for facility maintenance — same seven-section structure and footer as an SOW. |

### Flow A · Bid-document Q&A (read-only)
| File | What it demonstrates |
|---|---|
| [`sample-QA.md`](sample-QA.md) | Grounded, **cited** answers over the Reference-Library — nothing is changed. |

### WS-4 · Bid Evaluation & Award (the lifecycle's last step)
Regenerate with:
```bash
PYTHONPATH=agent/src python -m bid_package_agent.cli evaluate \
  --type "Pipeline Construction" --doc SOW --bids docs/examples/sample-bids_Pipeline-Construction.json
```
| File | What it demonstrates |
|---|---|
| [`sample-bids_Pipeline-Construction.json`](sample-bids_Pipeline-Construction.json) | Three bidder submissions (input). |
| [`sample-AWARD-RECOMMENDATION.md`](sample-AWARD-RECOMMENDATION.md) | The **deterministic** ($0-token) recommendation memo: it recommends the lowest bid **but flags** its non-standard terms (→ Legal) and an extra exclusion (scope risk). The agent ranks & flags; **a human approves the award**. |

> **Important:** the offline mock validates **structure, footer and routing only** (and, for WS-4,
> deterministic ranking). The narrative prose is deterministic filler — it does **not** reflect production
> quality. Point the engine at **Azure OpenAI GPT-4** (set the `.env` vars) for grounded, house-style
> output. See [`../EVALUATION.md`](../EVALUATION.md).
