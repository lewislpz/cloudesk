# Executable Control Plane Rules

The semantic control plane is the authority for workflow state and evidence.

## Mandatory Commands

- Validate with `bash .codex/scripts/validate-plan.sh <workspace>`.
- Change state only with `bash .codex/scripts/transition-workspace.sh`.
- Execute technical gates with `bash .codex/scripts/run-gate.sh`.
- Record review and approval gates with `bash .codex/scripts/record-gate.sh`.
- Create a checkpoint after every completed or blocked task with `bash .codex/scripts/checkpoint.sh`.
- Bind Git state before final verification with `bash .codex/scripts/bind-workspace.sh`.
- When Git is unavailable, bind verified files with `bash .codex/scripts/bind-files.sh`.
- Run all control-plane checks with `bash .codex/scripts/verify-control-plane.sh`.

## Evidence Rules

- Claims in prose do not satisfy gates.
- Every gate requires at least one existing evidence file stored inside the workspace.
- Technical gates require an executed command, exit code, output log, and evidence hash.
- Review gates require a concrete actor and existing evidence.
- High-risk independent review must use an actor different from the implementation actor.
- Changed or missing evidence invalidates the receipt.
- A changed Git revision invalidates completion evidence.
- Changed working-tree content invalidates a Git binding even when `HEAD` is unchanged.
- A changed file binding invalidates completion evidence outside Git.
- Empty bindings and missing binding roots are invalid.

## Assurance Boundaries

- Executable validation is the only `enforced` assurance.
- Actor names in transitions and gate receipts are `attested`; this package does not
  authenticate a human or agent identity by itself.
- `user_approval` means the caller attests that the user approved the action. A host
  integration that requires cryptographic or UI-backed provenance must supply and
  preserve that receipt outside this portable package.
- Workflow sequencing claims without receipts, such as RED-GREEN order or exact
  checkpoint timing, are `advisory`.

## State Rules

- Never edit the `status` or `approved_by` frontmatter fields directly.
- Use only valid transitions enforced by the control plane.
- Completion requires closed tasks and all risk-dependent gates.
- Delivery requires a completed workspace that still validates.
- Semantic mutations use atomic writes and a per-workspace lock.
