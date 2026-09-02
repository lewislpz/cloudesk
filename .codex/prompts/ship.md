# /ship

## Use

Run a merge or release step only on explicit request.

## Recommended Expansion

```text
When this prompt is invoked, open and read .codex/workflows/ship.md before acting.
Use that workflow as the source of truth for release steps and constraints.
Do not treat it as an optional reference: execute the release by following that workflow.
Commit message: <optional, in Conventional Commits format>
Strategy: <regular merge, squash, according to the repo>
Pre-validation: <tests, build, docs drift>
```
