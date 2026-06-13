"""Bid Package Generator (SOW/RFP) — Supply Chain bid-package POC, reference implementation.

This package is a *runnable reference implementation* of the POC's logic so the pattern
can be proven, tested and demoed without a live Microsoft 365 tenant. It mirrors what the
production POC does on the platform:

  * Flow B (generation) -> Copilot Studio Topic 1 + Azure OpenAI generative answers
  * Flow A (Q&A)        -> Copilot Studio Topic 2 + RAG over the Reference-Library
  * Approval routing    -> the Power Automate flow (footer parse, reviewer lookup,
                           legal/standard branch, move file, AuditLog)

What this is NOT: it does not deploy the Copilot Studio agent or the Power Automate flow —
those are configured on the tenant (see docs/ and platform/). See the README boundary table.
"""

__version__ = "0.1.0"
