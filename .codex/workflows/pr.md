---
description: Manual delivery workflow for committing, pushing a feature branch, and producing a pull request link.
---

# PR Workflow

Use this workflow only when the user explicitly asks for a PR-style delivery step.

## Preconditions

- the workspace must be a Git repository
- the current branch must not be one of the primary branches configured in `.codex/config.json`
- the configured Git remote should exist
- the user must confirm the commit message if one was not supplied
- the active workspace must declare `status: completed`
- medium- and high-risk gates must be satisfied

Apply this delivery procedure to the completed implementation workspace. Do not
change its `workflow` field to `pr`.

## Steps

1. Check branch and working tree state.
2. Run a relevant build or test command when the repository has one.
3. Confirm docs drift is resolved for changed APIs, schemas, or dependencies.
4. Confirm the active workspace passes `.codex/scripts/validate-plan.sh`.
5. Stage and commit using a Conventional Commit message.
6. Push the current branch to the configured remote.
7. Build a GitHub compare URL when the remote format allows it.
8. Revalidate the workspace after delivery actions.

## Failure Conditions

Abort and report if:
- the repo is not under Git
- the branch is a configured primary branch
- build verification fails
- push fails
- no remote is configured

## Final Response

Report the branch, commit message, push result, and PR link when available.

## Rules

- Never run this workflow automatically.
- Never force-push.
- If the repository does not support one of these steps, stop and say exactly why.
