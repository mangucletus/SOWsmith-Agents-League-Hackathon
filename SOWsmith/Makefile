# Bid Package Generator (SOW/RFP) — developer convenience targets.
# The engine runs with no install via PYTHONPATH; `make install` is optional (editable + dev extras).
export PYTHONPATH := agent/src

# Use the project venv if present, else python3, else python. Override with `make PYTHON=... <target>`.
VENV_PY := $(shell [ -x .venv/bin/python ] && echo .venv/bin/python)
PYTHON  ?= $(if $(VENV_PY),$(VENV_PY),$(shell command -v python3 || echo python))

.DEFAULT_GOAL := help
.PHONY: help install test kb demo evaluate eval serve ask clean

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

install:  ## Install the engine (editable) + dev/test extras
	$(PYTHON) -m pip install -e ".[dev]"

test:  ## Run the test suite (45 plumbing tests)
	$(PYTHON) -m pytest -q

kb:  ## Regenerate the SharePoint knowledge base from the generator
	$(PYTHON) knowledge-base/generator/_build_knowledge_base.py

demo:  ## Run the scripted lifecycle demo (draft → route → approve → Q&A → WS-4 award)
	$(PYTHON) -m bid_package_agent.cli demo

evaluate:  ## WS-4: evaluate bidder responses -> award recommendation (built-in sample)
	$(PYTHON) -m bid_package_agent.cli evaluate --type "Pipeline Construction" --doc SOW

eval:  ## Run the 10-intent evaluation (writes var/run/eval_results.csv)
	$(PYTHON) -m bid_package_agent.cli eval

serve:  ## Start the local web console at http://127.0.0.1:8080
	$(PYTHON) -m bid_package_agent.cli serve

ask:  ## Ask a bid-document question, e.g. make ask Q="standard exclusions clause"
	$(PYTHON) -m bid_package_agent.cli ask "$(Q)"

clean:  ## Remove local runtime output (var/) and caches
	rm -rf var __pycache__ .pytest_cache
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
