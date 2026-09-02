# /resume

## Use

Resume the latest work without restating everything.

## Recommended Expansion

```text
Resume the work using a workspace whose status.md declares status: approved, in_progress, or blocked.
Prefer this explicit PATH: <optional path>
If multiple candidates qualify and no PATH was provided, ask the user to choose; never select by recency alone.
Validate the selected workspace with .codex/scripts/validate-plan.sh before acting.
Use `python3 .codex/scripts/control.py select-workspace <plans-or-audits-root>` when exactly one eligible workspace is expected.
Determine whether the next step belongs to audit, think, forge, test, pr, or ship.
Open and read the appropriate workflow before acting, and use it as the operational source of truth.
Summarize the current state, the chosen workflow, and the next step before executing.
```
