# Global Rules For Codex Work

These rules define the default operating model for `.codex/` across repositories.

## 1. Context Loading

- Load documentation candidates from `.codex/config.json`.
- If configured candidates are missing, use local docs, config files, and the source tree to reconstruct context.
- Treat missing or stale documentation as a risk to record, not as a reason to guess.

## 2. Planning And Logging

- For non-trivial work, create `.orchestrator/plans/YYYY-MM-DD-hh-mm-slug/`.
- Create `status.md` from `.codex/templates/status.md` and keep its state current.
- Change workspace state only through `.codex/scripts/transition-workspace.sh`.
- Keep `investigation.md`, `design.md`, `plan.md`, and `implementation.md` aligned with the actual work.
- Break implementation into atomic tasks that are independently verifiable.
- Log major decisions where the next session can recover without re-reading the whole codebase.

## 3. Git Safety

- Do not run `git commit`, `git push`, merge, or branch deletion unless the user explicitly requested a delivery step.
- When a delivery step is requested, use Conventional Commits.
- If the workspace is not a Git repository, skip Git-specific instructions and state that clearly.

## 4. Codex-Native Execution

- Prefer local tools that exist in this environment: `rg`, `find`, `sed`, `git diff`, `git status`, `apply_patch`, shell commands, and sub-agents when delegation helps.
- Do not reference external helper runners or hidden automation that is not present in the repository.
- Keep the critical path local. Delegate only bounded side work with clear ownership.
- Use `.codex/templates/delegation-contract.json` for delegated write tasks.

## 5. Engineering Standards

- Apply `.codex/rules/risk-gates.md` to non-trivial work.
- Apply `.codex/rules/control-plane.md`; prose claims never satisfy executable gates.
- Treat `.codex/config.json` as the project-specific adaptation boundary.
- Classify failures before retrying; do not repeat unchanged failed actions.
- Use an error budget of three materially different repair attempts for the same failure.
- Keep docs synchronized when the target repository maintains docs as part of the workflow.
- Write shared repository docs, prompts, workflows, and guidance in English only so Codex does not spend tokens translating operating instructions.
- Preserve separation between UI, domain logic, and data access.
- Never hardcode secrets; prefer environment variables and documented setup.
- Favor tests for critical business logic and regressions.

## 6. Knowledge Distillation

- When a non-obvious decision or fix is made, update the most relevant file in `.codex/skills/` or the active plan.
- Do not let important context live only in transient chat history.
- Add process regressions to `.codex/evals/cases/` before changing the responsible workflow or skill.
