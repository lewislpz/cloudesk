---
description: Testing workflow for building a test matrix and executing a TDD loop.
---

# Test Workflow

Use this workflow to add or improve coverage with explicit RED-GREEN-REFACTOR
discipline.

## Setup

Create or reuse `.orchestrator/plans/<timestamp>-test-<slug>/` with:

- `status.md`
- `test-matrix.md`
- `implementation.md`

Create `status.md` from `.codex/templates/status.md` with `workflow: test`,
`status: in_progress`, and an explicit risk level.

If the repository is under Git and the user explicitly wants a branch, create one.
Otherwise stay on the current branch.

## Phase 1: Test Matrix

Analyze the requirement, changed module, or regression before writing tests.

Write `test-matrix.md`:

```markdown
# Test Matrix: <name>

## Requirements Under Test
- <observable behavior>

## Scenarios
### Happy Paths
- Given <state>, when <action>, then <result>

### Edge Cases And Failures
- Given <invalid or boundary state>, when <action>, then <error or fallback>

## Test Levels
- Unit: <pure logic and isolated services>
- Integration: <database, API, filesystem, browser, or framework boundary>
- E2E: <only when the flow cannot be trusted through lower levels>

## Verification Commands
- `<focused command>`
- `<broader command if needed>`
```

## Phase 2: Infrastructure Review

Check what already exists:

- current test framework and project-native commands
- factories, fixtures, mocks, builders, or test helpers
- coverage tooling if present
- conventions for naming, assertions, and setup/teardown
- external systems that must be mocked or stubbed

Reuse existing patterns before adding new helpers or dependencies. If a dependency
is needed, justify it in `implementation.md` and update docs when the repository
tracks testing standards.

## Phase 3: TDD Loop

For each scenario:

1. Write or update the failing test.
2. Run the focused command and confirm the failure is meaningful.
3. Implement the smallest production change that makes it pass.
4. Refactor only after the test is green.
5. Rerun the focused check and any affected neighboring tests.
6. Update `implementation.md` with RED, GREEN, and REFACTOR evidence.
7. Create a checkpoint with `.codex/scripts/checkpoint.sh`.

If the test already passes before implementation, explain whether it is an
existing covered behavior, a weak test, or a scenario that belongs in a different
level.

## Phase 4: Quality Gate

- Run the narrowest reliable suite that covers the changed behavior.
- Execute technical gates with `.codex/scripts/run-gate.sh`.
- Record non-technical gates with `.codex/scripts/record-gate.sh`.
- Collect coverage if the repo already supports it.
- Update docs if testing standards or observable behavior changed.
- Bind verified Git or file state before completion when required by risk.

## Final Response

Report pass/fail status, commands run, coverage if available, bugs fixed during the
cycle, and remaining gaps.

## Rules

- Never skip the failing-test phase unless the task is explicitly about repairing broken tests.
- Mock external systems in unit and integration tests.
- Prefer behavior assertions over implementation-coupled assertions.
- Classify failures before retrying and stop after three materially different failed repair attempts.
- Do not commit or push unless the user explicitly asks for delivery.
