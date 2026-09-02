# Development Context

Use this context while implementing an approved plan.

## Behavior

- Move directly to code and verification.
- Keep changes atomic and easy to review.
- Stay inside the current task; avoid opportunistic refactors.
- Update the plan and implementation log as work lands.

## Preferred Tools

- `rg` and `find` for discovery
- `sed -n` and `git diff` for inspection
- the host-approved patch or editing mechanism for source changes
- shell redirection for generated outputs only when the host permits it
- project-native build and test commands for verification

## Constraints

- Follow the active `plan.md`.
- If a task grows beyond its scope, split it before continuing.
- If validation fails three times in a row, stop and surface the blocker.
