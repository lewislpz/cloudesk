---
description: Manual release workflow for committing, merging to main, and pushing only on explicit user request.
---

# Ship Workflow

Use this workflow only when the user explicitly asks to merge or release.

## Preconditions

- the workspace must be a Git repository
- the current branch must not be a primary branch configured in `.codex/config.json`
- the user must confirm the commit message if one was not supplied
- build or test verification must pass before any merge step
- the active workspace must declare `status: completed`
- high-risk delivery requires independent review and explicit user approval

Apply this delivery procedure to the completed implementation workspace. Do not
change its `workflow` field to `ship`; successful delivery changes only its state to
`delivered`.

## Steps

1. Check branch and working tree state.
2. Run the relevant validation commands.
3. Confirm docs drift is resolved.
4. Confirm the active workspace passes `.codex/scripts/validate-plan.sh` and its risk gate.
5. Commit outstanding changes with a Conventional Commit message.
6. Update the selected configured primary branch from the configured remote.
7. Merge the current branch into that primary branch using the repository's agreed strategy.
8. Push the primary branch.
9. Optionally delete the feature branch if the user wants cleanup.
10. Transition the workspace to `delivered` after successful push.

## Failure Conditions

Abort and report if:
- the repo is not under Git
- the current branch is already a configured primary branch
- validation fails
- merge conflicts occur
- push fails

## Final Response

Report the merge result, commit message, push result, and any rollback guidance that fits the repo strategy.

## Rules

- Never run this workflow automatically.
- Never force-push.
- Do not delete branches unless the user asked for cleanup.
