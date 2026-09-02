# Risk-Based Quality Gates

Every non-trivial workspace must declare `risk: low|medium|high` in `status.md`.
Required and technical gates are configured in `.codex/config.json`; the defaults below
are the portable baseline.

## Low Risk

Examples: prose-only documentation, copy changes, local formatting.

Required gate:

- `consistency`: executed focused consistency command
- no unresolved scope violations

## Medium Risk

Examples: application logic, APIs, dependencies, schemas without destructive migration.

Required gate:

- `tests`: executed targeted tests or equivalent behavioral verification
- `review`: review evidence for changed contracts and boundaries
- documented remaining risks

## High Risk

Examples: authentication, authorization, secrets, destructive migrations, release automation, production delivery.

Required gate:

- `threat_model`: threat-model or failure-mode evidence
- `tests`: executed targeted verification
- `integration`: executed integration-level verification
- `independent_review`: review evidence from an actor that did not implement the change
- `user_approval`: explicit approval recorded by the user

Technical gates must be executed with `.codex/scripts/run-gate.sh`. Review and approval gates must be recorded with `.codex/scripts/record-gate.sh`.
Every gate receipt must reference at least one relative evidence file inside the workspace.

Review and approval actors are attestations in the portable control plane. They become
authenticated approvals only when a trusted host integration creates and binds the
receipt.

## Retry Classification

Before retrying, classify the failure:

- `deterministic`: change the implementation or test
- `environment`: report or repair the environment
- `permission`: request approval; do not retry unchanged
- `regression`: isolate and revert or fix the introduced behavior
- `requirements`: stop and resolve ambiguity

Three materially different repair attempts are the maximum for the same failure.
