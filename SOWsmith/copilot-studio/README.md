# `copilot-studio/` — Agent platform configuration

Artifacts you paste/configure in **Microsoft Copilot Studio** to build the Bid Package Agent
(the **Bid Package Agent** + **Support Layer** in the architecture diagram).

| File | Use |
|---|---|
| [`system-prompt.txt`](system-prompt.txt) | Paste into the **Generative Answers → Custom Instructions** field for Topic 1. Replace `[CLIENT_NAME]`. (Generated from `agent/src/bid_package_agent/prompts.py` — keep in sync.) |
| [`topics-and-trigger-phrases.md`](topics-and-trigger-phrases.md) | The three topics, trigger phrases, and node wiring |
| [`knowledge-scoping.md`](knowledge-scoping.md) | How to scope each topic to the right SharePoint library + supported types/limits |

This is **manual GUI configuration** — it is not deployed by code. The runnable engine in
[`../agent/`](../agent/) mirrors this logic so you can prove and demo it before/while building on
the tenant. See [`../docs/BUILD-RUNBOOK.md`](../docs/BUILD-RUNBOOK.md) for the week-by-week steps.
