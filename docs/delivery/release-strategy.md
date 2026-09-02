# Proposed Release And Engineering Workflow

## Purpose And Status

This document defines ClouDesk branches, pull requests, reviews, versioning, release
ownership, rollback, and future progressive delivery. It is proposed because the
directory is not yet a Git repository and no release has occurred. Technical gates
are in [CI](ci.md), promotion in [CD](cd.md), and reconciliation in
[GitOps](gitops.md).

## Trunk-Based Workflow

Use protected, always-releasable `main` with short-lived branches such as
`feat/<issue>-<slug>`, `fix/<issue>-<slug>`, `docs/<issue>-<slug>`, and
`chore/<issue>-<slug>`. There is no long-lived `develop` or environment branch;
environment state lives in reviewed paths, not divergent code histories. Hotfixes
branch from current `main`, pass the same gates, and promote normally with expedited
review only when incident policy justifies it.

Pull requests are small, single-purpose, rebased/updated through a merge queue, and
squash-merged so the reviewed Conventional Commit title becomes the `main` commit.
Force pushes to `main`, merge commits, direct commits, and permanent bypass are
disabled. Feature flags may decouple deploy from release when they have an owner,
expiry, safe default, telemetry, and no authorization/migration bypass.

## Pull Request Contract

Every PR states the user/operational outcome, issue, scope, tests/evidence, contract
and documentation effects, security/tenant impact, migration classification,
observability, rollout and rollback/roll-forward plan. UI changes include accessible
state evidence; infrastructure changes include plan/cost/replacement effects; API
changes include generated-client and compatibility evidence.

Required checks are current against the merge result. Conversations are resolved and
the author cannot approve their own change. Review policy is:

| Change | Minimum approval |
| --- | --- |
| Ordinary scoped change | One non-author owning-team reviewer |
| OpenAPI/shared contract | Backend/API and frontend consumer owners |
| Database migration/query invariant | Database plus owning domain; security for RLS/tenant/privilege |
| Auth, tenant isolation, secrets, IAM, CI supply chain | Security plus owning backend/platform team |
| Terraform, Helm, Argo, production values | Platform; release owner for promotion; database/security by impact |
| Destructive, break-glass, or production high-risk change | Independent risk owner(s) and explicit authorized production approval |

`CODEOWNERS` maps these paths and branch rules require its approval. Automation may
open a promotion PR but cannot approve or merge its own production change.

## Conventional Commits And Versioning

Use Conventional Commits on squash titles: `feat`, `fix`, `perf`, `refactor`, `test`,
`build`, `ci`, `docs`, `chore`, and `revert`, with a stable domain/platform scope where
useful. Examples are `feat(invoices): add issue transition` and
`fix(delivery): preserve migration gate on rollback`. A breaking change uses `!` and
`BREAKING CHANGE:` plus the required ADR/consumer plan; the marker does not authorize
an incompatible `/api/v1` change.

ClouDesk begins with one SemVer product release train (`vMAJOR.MINOR.PATCH`) and signed
annotated release tags created only from protected `main` after the descriptor is
eligible. Release candidates may use `vX.Y.Z-rc.N`. Features drive minor, compatible
fixes patch, and intentional public incompatibility major versions. Images also carry
discoverability tags, but deployment uses digests. Helm/chart and migration metadata
record compatibility with the product version rather than pretending independently
deployed modules are microservices.

Release notes are generated from reviewed Conventional Commits and curated by the
release owner. They list user-visible changes, security notes without exploit secrets,
OpenAPI/deprecations, migration/backfill, configuration/feature flags, known issues,
and rollback constraints. A tag or changelog is not deployment evidence; environment
history records the signed descriptor and GitOps commit.

## Release Lifecycle And Rolling Rollback

1. Merge through protected CI; build, scan, attest, sign, and publish once.
2. Create the signed release descriptor and promote it to dev.
3. Promote the exact descriptor to staging after dev evidence.
4. Validate migrations, mixed-version rolling behavior, E2E/security/load signals,
   and prior-digest rollback in staging.
5. Approve the production desired-state PR and protected artifact-copy job by scope.
6. Let Argo CD reconcile the approved commit with rolling updates.
7. Observe errors, latency, saturation, critical domain checks, queue/outbox age,
   migration health, and alerts; then close or revert the release record.

The default rollback is a Git revert to the prior signed descriptor. The prior app
must remain compatible with the expanded schema, and ECR retains its digest. A
contraction, incompatible event, or irreversible provider effect has no automatic
rollback; it requires the pre-approved forward/restore plan. Emergency fixes use the
same immutable evidence and reconciliation path whenever Git is available.

## Ownership And Approval

| Role | Accountable for |
| --- | --- |
| Change author/domain owner | Correct behavior, tests, documentation, telemetry, and rollback proposal |
| CI/platform owner | Branch gates, action/runner pins, OIDC, build provenance, ECR, Helm/Argo operation |
| Database owner | Migration ordering, lock/backfill risk, schema compatibility and recovery evidence |
| Security owner | Supply-chain policy, IAM/secrets/tenant review, vulnerability exceptions |
| Release owner (rotating named role) | Candidate selection, evidence completeness, approvals, communications, observation and close/revert decision |
| Incident commander | Time-bounded emergency decision and reconciliation follow-through |

No single role both proposes and silently approves a high-risk production change.
Production approval authorizes the named descriptor/environment only; any changed
digest, migration, values, plan, or evidence invalidates it.

## Future Progressive Delivery

V1 uses ordinary rolling Deployments. Evaluate Argo Rollouts with ALB traffic shifting
only when all of the following are true:

- production has enough steady traffic for statistically useful short analysis;
- RED metrics, SLO burn, pod saturation, and critical domain indicators are reliable,
  low-latency, and tested against known bad releases;
- old/new versions and the expanded schema can coexist throughout analysis/abort;
- the team owns Rollouts controller, CRDs, ALB target/service topology, upgrades,
  security, dashboards, and incident runbooks; and
- staging proves abort, rollback, controller/metric-provider outage, and no-capacity
  behavior without data loss.

A trial may send 5% to canary, pause and analyze, then advance through reviewed steps
to 100%; percentages and duration come from traffic/error-budget evidence, not a
universal template. Analysis should combine HTTP error rate, p95/p99 latency, SLO burn,
restart/resource saturation, and a release-specific business guardrail. Missing or
stale metrics fail safe by pausing/aborting rather than promoting. Automated abort may
restore the previous application digest, never reverse a database contraction or
undo an external business effect.

Adoption requires a new/amended ADR and a measured benefit over rolling updates.
Blue/green and multi-region release orchestration remain deferred to explicit
availability, isolation, or rollback requirements.

## Emergency And Break-Glass Releases

An exploitable vulnerability or active outage may shorten review/observation, but does
not permit untracked mutable images, static credentials, direct unreviewed DDL, or
leaving live drift. The incident record names scope, approver, release descriptor,
expected effect, rollback trigger, and expiry. If a live Kubernetes change is essential,
follow the [break-glass reconciliation procedure](gitops.md#break-glass-and-reconciliation),
then encode or remove it in Git before closure.

## Evidence Of Readiness

Before production, prove branch protection and CODEOWNERS cannot be bypassed by normal
actors; Conventional Commit release notes/versioning are deterministic; one signed
descriptor promotes without rebuild; stale/wrong approvals fail; rolling rollback
works with expanded schema; retained ECR digests and GitOps history recover the last
known-good release; and release/incident owners can execute the runbook within the
agreed window.
