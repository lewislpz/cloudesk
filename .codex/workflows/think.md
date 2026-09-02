---
description: Read-only analysis workflow for investigation, design, and implementation planning.
---

# Think Workflow

Use this workflow when the user wants analysis, architecture, or a concrete plan
without product code changes.

## Outcome

Create a workspace in `.orchestrator/plans/<timestamp>-think-<slug>/` with:

- `status.md`
- `investigation.md`
- `design.md`
- `plan.md`

Create `status.md` from `.codex/templates/status.md` with `workflow: think`,
`status: draft`, `approved_by: pending`, and an explicit risk level.

## Phase 0: Setup

```bash
export PLAN_PATH=".orchestrator/plans/$(date +'%Y-%m-%d-%H-%M')-think-<slug>"
mkdir -p "$PLAN_PATH"
```

Do not create branches, commits, or product-code edits in this workflow.

## Phase 1: Investigation

Load source-of-truth context in this order:

1. Documentation candidates from `.codex/config.json`.
2. If candidates are missing or incomplete, local docs and README files.
3. Project configuration such as `package.json`, `pyproject.toml`, `pom.xml`,
   `Dockerfile`, compose files, or equivalent stack markers.
4. Relevant source modules and tests.

Do not require a specific docs index such as `docs/00-general-docs.md` unless the
repository actually provides it. Missing or stale documentation is a finding to
record, not a reason to invent context.

Write `investigation.md` with:

```markdown
# Investigation: <name>

## Summary
<one paragraph describing the request and why it matters>

## Current State
- Tech stack: <detected from docs/config/source>
- Relevant modules: <files or directories likely affected>
- Existing patterns: <architecture, naming, testing, data flow>
- Reuse opportunities: <existing code or contracts to extend>

## Requirements
- Functional: <observable behavior>
- Non-functional: <security, performance, reliability, UX, migration>

## Scope
- In scope: <what this plan will cover>
- Out of scope: <explicit exclusions>

## Risks And Edge Cases
- <risk>: <impact and mitigation>

## Recommendation
<recommended direction and reasoning>
```

## Phase 2: Design

Read `investigation.md`, then write `design.md` with the smallest viable design.
Separate hard-to-reverse decisions from local implementation details.

Use the sections that apply:

```markdown
# Design: <name>

## Architecture Impact
<how the change fits current boundaries>

## File And Module Boundaries
<files/modules to create, edit, or avoid>

## Contracts
<API routes, DTOs, schemas, events, CLI contracts, or none>

## Data Model
<entities, migrations, indexes, persistence effects, or none>

## UI And State
<component tree, state ownership, accessibility, responsive behavior, or none>

## Dependencies
<new dependencies with justification, or existing dependencies reused>

## Failure Behavior
<validation, errors, rollback, retries, and security posture>

## Testing Strategy
<unit, integration, e2e, static checks, or manual verification>
```

For frontend work, explicitly separate presentation, state, data fetching, and
accessibility concerns. For backend work, explicitly separate transport,
business rules, persistence, validation, and authorization.

## Phase 3: Plan

Write `plan.md` as an ordered checklist of atomic, independently verifiable tasks.

Each task must include:

- target file or module
- concrete action
- acceptance criteria
- verification command or check

Use this shape:

```markdown
# Plan: <name>

> Goal: <one-line outcome>
> Risk: <low|medium|high>

- [ ] Task task-N: <task name>
  - Target: `<path or module>`
  - Action: <specific change>
  - Acceptance: <observable result>
  - Verify: `<command>` or <manual check>
```

Keep tasks small enough that a future `forge` run can complete and verify one task
without understanding the whole plan. Put dependency-order foundations first, core
behavior second, and integration or polish last.

The top-level `Task <stable-id>:` checkbox is the only completion marker. Task
metadata is descriptive and must not use additional checkboxes. Existing plans
without canonical task markers remain supported by completion validation.

## Finalization

Before finishing:

1. Validate the workspace with `.codex/scripts/validate-plan.sh`.
2. Transition to `awaiting_approval` with `.codex/scripts/transition-workspace.sh`.
3. Leave `approved_by: pending` until the user explicitly approves execution.

## Final Response

Tell the user:

1. what you found
2. the recommended design
3. the execution plan path
4. that product code was not modified

## Rules

- Do not edit product code in this workflow.
- Writing under `.orchestrator/plans/` is allowed.
- Do not create branches, commits, pushes, releases, or destructive actions.
- Prefer repository evidence over assumptions and record documentation gaps.
