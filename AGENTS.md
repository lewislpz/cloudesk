# Agentic Development

<!-- codex-workflow:start -->
For non-trivial work in this repository:

1. Read `.codex/MANUAL.md` and `.codex/config.json`.
2. Follow `.codex/rules/global.md`, `.codex/rules/agent-security.md`, and `.codex/rules/control-plane.md`.
3. Select the matching procedure from `.codex/workflows/`.
4. Use `.orchestrator/` workspaces for resumable plans, audits, evidence, and checkpoints.
5. Apply risk gates from `.codex/rules/risk-gates.md`.
6. Never commit, push, merge, release, or perform destructive actions without explicit user authorization.
7. After modifying `.codex/`, run `bash .codex/scripts/verify-control-plane.sh`.

## Slash Alias Routing

This repository does not assume that the host has a native slash-command parser.
When a user message starts with `/name`, treat `/name` as a repository alias and
resolve it deterministically:

1. Extract the leading alias without the slash and preserve all trailing text as
   the user's input to that alias.
2. Open `.codex/prompts/<alias>.md`. Its instructions are mandatory, not optional
   background reading.
3. Open every `.codex/workflows/*.md` file referenced by the prompt and use the
   referenced workflow as the operational source of truth.
4. Load the manual, configuration, rules, templates, skills, and repository files
   required by that workflow before acting. Do not invent missing procedures.
5. If the user supplied only the alias, use the current repository as scope,
   inspect local evidence, and proceed with safe workflow defaults. Ask one concise
   question only when a required choice cannot be inferred safely; never wait for
   optional context that can be discovered locally.
6. Unknown aliases must not be guessed or executed. State that
   `.codex/prompts/<alias>.md` is missing and list the aliases available under
   `.codex/prompts/`.

Known aliases are `/think`, `/forge`, `/test`, `/audit`, `/pr`, `/ship`, and
`/resume`. The alias selects a workflow; it never overrides its safety boundaries.
In particular, do not make product-code changes during `/think` or `/audit`, do not
run `/forge` without an explicitly valid plan, and do not commit, push, merge, or
release unless the user explicitly invoked the corresponding delivery action.
<!-- codex-workflow:end -->
