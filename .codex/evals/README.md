# Workflow Evals

These fixtures describe process regressions the workflow package must prevent. Run `bash .codex/scripts/validate-workflows.sh` for deterministic checks. Use the cases as prompts when pressure-testing behavioral changes.

Each case defines:

- setup and prompt
- expected decisions
- forbidden behavior
- evidence required for a pass

Add a failing case before changing a skill or workflow rule.

Evaluation results are runtime artifacts. `verify-control-plane.sh` writes them to a
temporary location so a copied `.codex/` package does not carry project history.
