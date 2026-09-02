# Slash Prompts

This environment does not expose a native slash-command parser. Use this simple convention instead:

- each alias `/name` maps to a file at `.codex/prompts/name.md`
- each file contains the recommended prompt expansion that Codex should load when that alias is invoked
- if the prompt references `.codex/workflows/<name>.md`, Codex must open that workflow before acting and follow it as the operational source of truth
- the prompt activates the workflow; the workflow defines phases, constraints, deliverables, and limits
- you can invoke an alias by mentioning it in chat and asking Codex to use the saved prompt

Examples:

```text
Use /think to analyze this feature: Google login.
```

```text
Use /forge on the explicitly selected approved plan and do not commit.
```

```text
Use /resume to continue from the latest PLAN_PATH.
```

## Execution Rule

When an alias is invoked:

1. Codex must open `.codex/prompts/<alias>.md`.
2. If that file points to a workflow, Codex must open `.codex/workflows/<workflow>.md`.
3. Codex must execute the task by following that workflow, not merely mention it or treat it as an informal reference.

## Available Aliases

- `/think`: analysis and planning without product code changes
- `/forge`: plan-driven implementation
- `/test`: test matrix and TDD work
- `/audit`: read-only audit
- `/pr`: branch delivery with push and PR link, only when explicitly requested
- `/ship`: merge or release, only when explicitly requested
- `/resume`: continue an explicitly selected active plan or audit

## Practical Rule

If you later wire a real slash-command launcher, these files can stay the source of truth for both alias expansion and mandatory workflow loading.
