# Domain Boundaries For Delegated Work

These boundaries apply when Codex intentionally adopts one of the specialized roles in `.codex/agents/`.

## Core Rule

A role should stay inside its owned slice unless the task explicitly requires a cross-boundary change.

## Role Ownership

### `architect`
- Owns: `docs/`, `.codex/`, architecture decisions, contracts, cross-cutting concerns
- Avoids: implementation-heavy edits unless the task is documentation or orchestration itself

### `backend`
- Owns: backend services, persistence, APIs, validation, backend tests
- Avoids: visual styling and frontend-only refactors

### `frontend`
- Owns: UI, client state, accessibility, design-system usage, frontend tests
- Avoids: persistence internals and server-only infrastructure changes

### `doc-planner`
- Owns: plans, ADR-like notes, documentation sync, workflow traceability
- Avoids: large implementation changes unless the task is documentation-first

## Practical Rule

If a task clearly spans multiple domains, split ownership explicitly instead of letting one role guess across the whole stack.

For delegated writes, record allowed and forbidden paths in `.codex/templates/delegation-contract.json` and validate returned changed paths with the control plane. Any required out-of-scope edit stops the task until a new contract is issued.
