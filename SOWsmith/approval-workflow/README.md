# `approval-workflow/` — Power Automate approval routing

The backend that routes a generated draft to the right reviewer and records the outcome
(the **Power Automate** + **Stakeholders Review** boxes in the architecture diagram).

| File | Use |
|---|---|
| [`flow-definition.md`](flow-definition.md) | The 10-action flow, the legal/standard branch, error handling, and the footer contract |
| [`adaptive-card-input.json`](adaptive-card-input.json) | Card the agent uses in Teams to collect the bid-package request (Topic 1) |
| [`adaptive-card-review.json`](adaptive-card-review.json) | Card the reviewer receives in Teams to Approve / Request Changes / Reject |

Built in the Power Automate GUI on the tenant. The runnable mirror is
`agent/src/bid_package_agent/{approval,pipeline,audit}.py` — run `bidpkg demo` to see the
generate → route → approve → audit path execute locally.
