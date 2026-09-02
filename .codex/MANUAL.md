# Codex Workflow Manual

This repository uses `.codex/` as a local operating system for Codex. These files are playbooks and role cards, not executable slash commands. Codex should follow them when the user explicitly asks for a workflow or when the task clearly matches one.

## Directory Map

- `agents/`: role briefs for architecture, planning, backend, and frontend work
- `rules/`: global constraints, delivery safety, and role boundaries
- `workflows/`: reusable operating procedures for analysis, implementation, testing, audit, PR, and ship
- `skills/`: focused reference packs for architecture, testing, code quality, and delegation
- `contexts/`: behavior overlays for research, implementation, and review
- `templates/`: canonical formats for plans, status, logs, and delegation
- `schemas/`: machine-readable contracts for workflow artifacts
- `scripts/`: dependency-free workflow validation
- `evals/`: reproducible process regression cases

## Project Configuration

`.codex/config.json` is the project adaptation boundary. Configure workspace roots,
documentation candidates, generated-file exclusions, Git conventions, and risk gates
there instead of editing the control-plane implementation.

Keep generic workflows and scripts product-neutral. Put stack-specific guidance in
optional skills and repository-specific instructions outside the reusable core.
Follow `.codex/PORTABILITY.md` when adopting the package in another repository.

After copying `.codex/` into a repository, run `bash .codex/scripts/bootstrap.sh`.
This installs the root activation instructions, creates workflow roots, checks
prerequisites, and validates the package without overwriting existing guidance.

## How To Invoke This In Codex

Use natural prompts that point at the workflow you want. Examples:

- `Use .codex/workflows/think.md to analyze and plan this feature.`
- `Follow .codex/workflows/forge.md and execute the explicitly selected approved plan.`
- `Run a read-only audit using .codex/workflows/audit.md.`
- `Use .codex/workflows/test.md to add coverage for this module.`
- `Follow .codex/workflows/pr.md to prepare a PR.`

The workflow files are instructions for Codex to interpret, not commands that a runner parses.

When a user invokes an alias from `.codex/prompts/`, Codex should:

1. open the matching prompt file in `.codex/prompts/`
2. follow any referenced workflow in `.codex/workflows/`
3. treat that workflow as the operational source of truth, not as an optional hint

## Preferred Flow

1. `audit`: read-only health check for an existing codebase
2. `think`: investigation, design, and plan without product code changes
3. `forge`: execute an approved plan and keep an implementation log
4. `test`: build or expand a test matrix with TDD discipline
5. `pr` or `ship`: only on explicit user request

For non-trivial work, store artifacts in `.orchestrator/`:

- `.orchestrator/plans/<timestamp>-<slug>/`
- `.orchestrator/audits/<timestamp>-audit/`

Each workspace must use `.codex/templates/status.md` and declare a stable ID, workflow, status, phase, risk, approval state, and timestamps. Use `.codex/scripts/validate-plan.sh <workspace>` before execution or resumption. Never edit state fields directly; use `.codex/scripts/transition-workspace.sh`.

List resumable workspaces with `bash .codex/scripts/list-workspaces.sh`.

## Source Of Truth

Load documentation candidates in the order declared by `.codex/config.json`. If none exist, fall back in this order:

1. `README.md` and repository docs
2. configuration files such as `package.json`, `pyproject.toml`, `pom.xml`, `Dockerfile`
3. the source tree and existing tests

If docs are missing or stale, record that gap in the plan and treat code plus config as provisional truth.

## Role Model

The files in `agents/` define reasoning lenses that Codex can use directly or via sub-agents:

- `architect`: system design, contracts, data model, security posture
- `doc-planner`: plan authoring, scope control, docs synchronization
- `backend`: business logic, validation, persistence, service boundaries
- `frontend`: UI, state, accessibility, visual consistency

## Skill System

Skills are portable operational entrypoints, not repository conventions. Apply the
precedence and progressive-disclosure rules in `.codex/skills/README.md`. Read the
matching `SKILL.md` first, inspect repository evidence, and load only references that
match the detected stack and current decision.

`python3 .codex/scripts/control_skill_validation.py` enforces concise entrypoints,
valid triggers, local reference integrity, and available-skill handoffs.

## SDD In Codex

This setup keeps the Sub-Agent Driven Development idea, but adapts it to Codex:

- keep the immediate blocking task in the main thread
- delegate only bounded side tasks to sub-agents
- pass an enforceable delegation contract based on `.codex/templates/delegation-contract.json`
- update `plan.md` and `implementation.md` after each completed task
- classify failures before retrying and abort after three materially different failed repair attempts

## Control Plane

- Select workspaces by explicit path and valid state, never by recency alone.
- `think` produces a draft or approval-ready plan; `forge` executes only an approved or already in-progress plan.
- Apply `.codex/rules/risk-gates.md` before completing implementation or delivery.
- Apply `.codex/rules/agent-security.md` whenever repository or external content can influence tool use.
- Store gate evidence inside its workspace and reference it with relative paths.
- Add a failing case under `.codex/evals/cases/` before changing a workflow or skill to prevent a process regression.
- Treat `.codex/rules/control-plane.md` as the authority for transitions, gate evidence, checkpoints, metrics, and Git binding.
- Run `bash .codex/scripts/verify-control-plane.sh` before considering workflow-package changes complete.

Rules use three assurance levels:

- `enforced`: a control-plane command or validator rejects violations
- `attested`: a named actor records evidence, but the local package cannot authenticate
  that actor independently
- `advisory`: Codex must follow the rule, but no executable receipt proves it

State transitions, artifact presence, required gates, evidence freshness, bindings,
and delegated path scopes are enforced. Review actors, user approval, TDD order,
checkpoint timing, and delivery intent are attestations or advisory unless a trusted
host integration supplies stronger provenance.

The control plane uses atomic writes and a per-workspace lock. Do not bypass its
commands with direct edits to semantic state or control receipts.

`verify-control-plane.sh` validates the package and active workspaces by default; a
successful default run does not attest to skipped historical workspaces. Maintenance
and CI should run `bash .codex/scripts/verify-control-plane.sh --all`. Use
`--workspace PATH` to validate one workspace explicitly before delivery.

## Workspace Lifecycle

The `workflow` field records the procedure that created the workspace and does not
change during its lifetime. `think` normally creates a planning workspace; `forge`
may execute a selected approved planning workspace or create a forge workspace when
no plan exists. `test` may use its own workspace for a test-focused slice. `pr` and
`ship` are delivery procedures applied to an already completed workspace; they do
not replace its `workflow` value. Successful ship delivery transitions that workspace
from `completed` to `delivered`.

## Git And Delivery

`pr` and `ship` are manual workflows. Codex should never commit, push, merge, or delete branches unless the user explicitly asks. If the workspace is not a Git repository, skip Git steps and continue with local analysis or implementation.
