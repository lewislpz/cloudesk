# Proposed Integration And Contract Testing

## Purpose And Status

This document defines planned verification at ClouDesk's persistence, HTTP, event,
object, identity, infrastructure, and deployment boundaries. It is not evidence that
those environments or suites exist. The strategy keeps local integration
reproducible while reserving real AWS and Kubernetes verification for isolated
sandbox or production-shaped staging.

## Integration Topology

The default integration environment composes the real Go binary and migrations with:

- a PostgreSQL Testcontainer at the supported production major, runtime/migrator
  roles, forced RLS where planned, and isolated databases per parallel suite;
- a faithful SQS-compatible endpoint for lease, long-poll, redrive, duplicate, and
  DLQ behavior; an in-memory queue is unit-test only;
- an S3-compatible object store for presign, metadata, checksum, lifecycle-state, and
  orphan reconciliation, supplemented by disposable AWS S3 tests for IAM/policy
  behavior that emulation cannot prove;
- the local OIDC adapter with production-facing redirect/callback/session semantics
  and local-only signing keys;
- Redis only for the suites of an adopted named use case, with both enabled and
  disabled/unavailable modes; and
- email/document provider test adapters with controllable accepted, throttled,
  permanent-failure, timeout, and ambiguous-outcome responses.

Each dependency has a readiness condition and bounded startup timeout. Suites wait on
observable readiness, not sleeps. Containers are pinned by digest or exact version,
use synthetic data, expose no public port beyond the test host, and are always
addressed through environment-specific allowlists.

## Boundary Matrix

| Boundary | What the integration suite proves | Negative/failure cases | CI placement and release signal |
| --- | --- | --- | --- |
| HTTP to application | Middleware order, schema mapping, session/CSRF, tenant context, permission, idempotency and error envelope | Invalid/revoked auth, wrong tenant/parent, stale version, cancellation, timeout, oversized/unknown input | Affected PR; every declared response and denial must pass |
| Application to PostgreSQL | Transactions, constraints, RLS, locks, versions, cursor queries, audit/outbox atomicity | Cross-tenant reads/writes/FKs, missing RLS context, rollback, pool reuse, deadlock, ambiguous commit | Affected PR/full nightly; zero isolation or integrity escapes |
| Outbox to SQS | Lease, per-destination partial success, retry and publication acknowledgement | Publisher crash before/after acceptance, IAM denial, delayed broker, expired lease | Nightly/release candidate; no committed event lost |
| SQS to consumer | Envelope validation, inbox/effect atomicity, visibility and DLQ | Duplicate/out-of-order/poison/mismatched tenant, crash around commit/delete, replay outside dedupe policy | Nightly/release candidate; one durable effect and safe quarantine |
| Files to S3 | Pending metadata, exact presign constraints, completion verification, scan/delete state | Foreign owner, wrong key/type/size/checksum, expired/reused URL, missing object, orphan/version cleanup | Affected PR plus AWS sandbox; no unauthorized usable capability |
| Identity provider | OIDC protocol mapping and application session lifecycle | State/nonce/issuer/audience/time/signature mismatch, refresh outage, revocation | M1 PR and staging; fail closed without token leakage |
| Optional Redis | Named cache/rate-limit behavior and fallback | Timeout, failover, stale/foreign key, eviction, cold restart | Suite required only when adopted; correctness survives loss |
| External provider | Durable intent, provider idempotency, normalized error and reconciliation | `429`, `500`, timeout after send, malformed response, secret leakage | Nightly/staging; no source rollback or duplicate external effect |

## OpenAPI And Generated-Client Contract

OpenAPI 3.1 is the single transport source. A clean contract job:

1. parses, resolves, lints, and validates the bundled specification and all examples;
2. enforces stable unique `operationId`, organization-prefixed protected routes,
   shared error responses, security/CSRF declarations, bounded pagination,
   idempotency headers, preconditions, nullability, and closed schemas;
3. generates strict Go server types/interfaces and the TypeScript fetch client with
   pinned tools, formats them, and fails on a worktree diff;
4. compiles representative Go handlers and frontend consumers and exercises money,
   timestamps, nullable/optional fields, cursors, ETags, async `202`, and all error
   examples in both runtimes;
5. runs runtime response validation in integration and rejects undeclared status,
   header, or body shapes; and
6. compares against the target branch with a pinned semantic diff tool such as
   `oasdiff`.

Fixtures prove that field/operation removal, newly required input, narrowed value,
status or authorization change, operation ID rename, and unsafe enum growth fail.
An intentional incompatible change requires the documented new-major and consumer
migration process; suppressing a diff rule without equivalent review is prohibited.

No separate Pact-style consumer contract is needed for the initial web/API pair:
validated OpenAPI plus generated-client compilation and executable examples form the
contract. A later independent consumer may justify consumer-driven contracts without
replacing OpenAPI.

## Database And Migration Integration

Migrations are tested from empty and from every supported previous release schema.
For an expand-and-contract change, the suite executes:

1. expand migration, then old and new application reads/writes against the expanded
   schema;
2. throttled backfill with deterministic ranges, interruption, restart from recorded
   watermark, duplicate invocation, and row/invariant reconciliation;
3. read switch and stop-old-write validation under concurrent traffic;
4. application rollback while the expanded schema remains; and
5. contraction only in a later compatibility window after queue/DLQ replay and
   rollback evidence expires.

Negative cases include lock/statement timeout, invalid leftover concurrent index,
constraint validation on bad historical data, RLS/policy omission on a new tenant
table, composite FK omission, incompatible generated `sqlc`, migration run by a
runtime role, two migration jobs, and partial/backfill failure. Destructive migrations
require representative-size staging evidence and restore/roll-forward readiness; a
passing empty-database migration is insufficient.

Schema conformance tests inventory every tenant table for non-null `organization_id`,
tenant uniqueness, composite foreign keys, force-enabled RLS where required, and no
runtime owner/`BYPASSRLS`. Query contract tests search/review suspicious ID-only SQL,
then execute two-tenant negative cases with the actual role.

## Event And Async Contracts

Event schemas and representative fixtures are versioned. Producers and consumers
validate envelope version, event type/version, mandatory server-written
`organization_id`, event/aggregate identity, correlation/causation, bounded payload,
and absence of secrets, URLs, or large artifacts.

Compatibility tests run old and new consumers against the maximum retained/replayable
event versions. Duplicate fixtures preserve `event_id`; compensating/recomputation
fixtures use a new ID and causation metadata. Tests prove partial fan-out through one
delivery per destination, one inbox effect per consumer/tenant/event, metadata-hash
mismatch quarantine, unsupported-version quarantine, and controlled canary redrive
without deleting inbox history.

## Infrastructure, Manifest, And Security Contracts

| Area | Pull-request gates | Sandbox/staging proof | Production signal |
| --- | --- | --- | --- |
| Terraform | `terraform fmt -check -recursive`, `validate`, lock-file check, `tflint`, selected Checkov/policy rules, `terraform test`, speculative plan | Disposable account creates network/IAM/storage/EKS prerequisites; negative wrong account/Region, wildcard IAM, public/unencrypted data, missing backup/deletion protection; bounded teardown | Reviewed exact plan; actual state/KMS/public-block/OIDC/CloudTrail/IAM denial and recovery evidence |
| Helm | `helm lint`, values JSON schema, deterministic `helm template`, image digest/secret-reference rules | Server-side dry-run against the staging Kubernetes version and controller set | Same chart/version and environment values revision promoted |
| Kubernetes | `kubeconform` or selected schema validator, deprecated-API check, policy-as-code for restricted pod security, probes, resources, service account, network policy, HPA/PDB/topology | Apply to isolated namespace; readiness, rollout, service routing, Pod Identity and default-deny tests | No policy exception without owner/expiry; production-shaped staging evidence current |
| Containers/dependencies | Reproducible build, non-root/read-only/capability policy, SBOM, secret/SAST/dependency/image scan | Runtime user/filesystem/health and workload-specific network/IAM denial | Candidate digest passes severity/SLA policy and is the promoted digest |
| AWS controls | Static Terraform policy | Actual private bucket/RDS/SQS, encryption, TLS, exact origin/SG/route, workload role, and denied unrelated action | Control evidence linked to exact account/root/revision; no static key |

Scanner findings are triaged by reachability, exploitability, asset, and policy; they
are not ignored because another scanner is green. Active penetration or cloud tests
run only against an explicitly scoped authorized target. Fork/untrusted CI receives
no AWS, provider, production, or state credentials.

Terraform owns AWS primitives, GitOps owns Kubernetes desired state, and the AWS Load
Balancer Controller owns the ALB generated from Ingress. Integration tests reject
duplicate ownership rather than attempting to reconcile two controllers.

## Fixtures, Isolation, And Cleanup

Suite IDs include run/worker identity but never real tenant data. Resources carry a
test marker and TTL where supported. A cleanup operation resolves and verifies the
exact test account, Region, prefix, database, bucket, and queue before acting; failed
cleanup creates an owned finding rather than broadening its target.

Parallel suites receive separate databases/schemas, queue names, object prefixes,
provider accounts, and test principals. Cross-suite shared state is limited to
read-only images/tool caches. Fixture setup records authoritative IDs and checks that
foreign-tenant rows actually exist before running a concealed-`404` assertion.

## Pipeline Placement And Promotion Gates

- **Pull request:** affected Testcontainers, OpenAPI generation/diff, migrations,
  event fixtures, Terraform/Helm/Kubernetes static and policy checks. Failures block
  merge.
- **Main/nightly:** complete adapter topology, crash windows, old/new migration and
  event compatibility, security corpus, Redis absent/present mode if adopted. A
  failure blocks the candidate branch.
- **Disposable sandbox:** cloud service semantics, IAM denial, networking, encryption,
  backup configuration, and teardown. Required before the affected infrastructure
  can enter staging.
- **Release staging:** same immutable images/migration/chart with real managed-service
  classes, production-shaped routing and workload identity, deployment smoke, rollback,
  capacity, and selected fault tests. Required before production promotion.
- **Production:** current exact-plan and immutable-artifact evidence plus bounded
  post-deploy smoke. Passing emulators alone never proves production cloud controls.
