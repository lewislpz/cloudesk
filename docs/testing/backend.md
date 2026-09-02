# Proposed Backend Testing Strategy

## Purpose And Status

This document defines planned verification for the Go API, modular domain packages,
PostgreSQL repositories, outbox publisher, and workers. It specializes the
[quality strategy](strategy.md) and the seams in the
[Go backend architecture](../architecture/backend.md). No Go tests or production
code currently exist.

## Go Test Layers

| Layer | Primary purpose | Dependencies | Typical signal |
| --- | --- | --- | --- |
| Domain unit | State machines, money, time, permissions, normalization, retry classification | Go `testing`, table/property builders, deterministic clock | Fast PR gate; all critical rule branches pass |
| Application/use-case | Authorization, transaction ownership, outbox/audit/idempotency orchestration | Small hand-written fakes for consumer-owned ports | PR gate; exact call/outcome and rollback intent |
| HTTP | Generated strict handler, middleware ordering, validation, headers, status/error mapping, cancellation | `httptest`, local session/CSRF fixture, fake use case or real DB when semantics require it | PR gate; declared OpenAPI response only |
| Repository/database | SQL, constraints, RLS, locks, transactions, migrations, query plans | Real PostgreSQL Testcontainer, `pgx`, `sqlc`, actual runtime roles | Affected PR and full nightly; integrity/isolation proof |
| Worker/process | Envelope validation, inbox/outbox, leases, visibility, shutdown, provider intent | PostgreSQL plus faithful SQS-compatible adapter; controlled crash points | Merge/nightly and release candidate |
| Race/fuzz | Goroutine ownership, shared state, parser robustness | `go test -race`, native fuzzing with checked-in regression corpus | Affected PR/routine nightly; zero races/panics |

Mocks of `pgx`, generated `sqlc` internals, AWS SDK request builders, or private
handler functions are not the principal confidence layer. Unit tests isolate a narrow
port; adapter behavior is proven at its real boundary.

## Domain And Application Unit Coverage

At minimum, table or property tests cover:

- invoice line arithmetic in minor units/bounded decimals, tax and discount order,
  currency consistency, total snapshots, transition graph, number allocation inputs,
  and issued/void immutability;
- timer start/stop/manual correction rules, positive duration, UTC instants, DST
  presentation inputs, billable rate resolution, and locked/invoiced entry rejection;
- organization membership status, canonical permission mapping, owner-only changes,
  last-owner preservation, invitation expiry/single use, and no self-escalation;
- project/task/comment lifecycle, restricted-project predicates, archive behavior,
  safe comment handling, and optimistic version conflicts;
- cursor/filter normalization, request fingerprints, event compatibility,
  retry-safe classification, backoff limits, and poison-message classification;
- application orchestration that checks current authorization before idempotency
  replay, places business/audit/outbox/replay state in one transaction, and never
  performs S3, SQS, OIDC, Redis, or email I/O inside it.

Fakes record semantic operations, not internal call sequences unrelated to the
contract. Transaction fakes must model commit versus rollback explicitly and cannot
claim to prove database atomicity.

## HTTP Tests With `httptest`

Handlers are exercised through the generated router/middleware stack. The matrix for
every protected operation includes valid session, missing/expired/revoked session,
invalid CSRF on unsafe methods, no membership, suspended membership, missing
permission, foreign tenant/resource/parent, malformed and oversized input, unknown
fields, cancellation, and the declared success/domain failure.

Shared assertions verify:

- effective `X-Request-ID`, safe error envelope, route-template logging, no sensitive
  response/log detail, and only OpenAPI-declared status/body/header combinations;
- `404` concealment for absent membership or a resource in another organization,
  `403` only for a member lacking an action, and comparable response shape;
- required `Idempotency-Key`, `If-Match`, `ETag`, `Retry-After`, CSRF, and content-type
  behavior;
- request deadline and disconnect propagation to the use case, with no false `500`
  for ordinary cancellation;
- body/parameter/filter/sort/cursor bounds and no interpolation of caller-selected
  identifiers;
- `/health/live` independence from remote services and route-specific readiness
  behavior described in [reliability](reliability.md).

For idempotent commands, HTTP tests verify replay status/body and a fresh request ID,
safe allowlisted replay headers, `Idempotency-Replayed: true`, fingerprint conflict,
in-progress conflict, current authorization before replay, and no automatic mutation
retry with a new key.

## PostgreSQL And Repository Tests

Testcontainers starts a supported PostgreSQL major with production extensions and
settings that affect semantics. Migrations run from empty before repositories are
compiled/exercised. The suite connects with `clouddesk_api`, worker, dispatcher, and
migrator-equivalent test roles as appropriate; table-owner credentials are limited to
setup.

Every tenant repository proves:

- reads, writes, deletes, lists, aggregates, cursors, and joins require the explicit
  organization and reject foreign IDs or mixed-tenant parent/child relations;
- tenant composite foreign keys, uniqueness, lifecycle, temporal, numeric,
  immutable-history, and append-only audit constraints fail closed;
- RLS `USING` and `WITH CHECK` deny missing/wrong context, and alternating tenants and
  users on reused pool connections cannot inherit stale `SET LOCAL` values;
- empty, maximum-page, equal-sort-key, tampered/cross-tenant cursor, insert-between-
  pages, and unchanged-dataset pagination cases have the documented behavior;
- cancellation, statement/lock timeout, deadlock/serialization handling, transaction
  rollback, ambiguous-outcome resolution, and pool exhaustion remain bounded;
- advertised query shapes have representative `EXPLAIN (ANALYZE, BUFFERS)` evidence
  and tenant-leading bounded access rather than unbounded `OFFSET` or N+1 reads.

The database is isolated per parallel test group. Rollback wrappers may accelerate
ordinary repository cases, but concurrency, advisory-lock, commit, pool-reuse,
publisher lease, and crash tests use independent committed connections.

## Explicit Concurrency And Negative Matrix

| Scenario | Stimulus | Required durable outcome |
| --- | --- | --- |
| Global active timer | Same user concurrently starts timers in the same and two different organizations | One active row globally; one success/replay as applicable; losers receive the documented conflict; no foreign detail leaks |
| Timer stop | Concurrent same-key and different-key stops, cancellation before/after commit | One stopped duration and audit/outbox fact; same key replays; no doubled time |
| Invoice draft | Concurrent requests allocate the same time entry to different drafts | At most one allocation; losing transaction is a safe conflict with no partial lines |
| Invoice issue | Concurrent editors/issues with same and stale versions, same/different keys | One number and immutable snapshot; deterministic lock order; one audit/outbox effect; replay or precondition/conflict as documented |
| Idempotency | Same tuple/same fingerprint, same tuple/different fingerprint, winner cancellation/crash, membership loss before replay | One committed business effect; safe replay, `409`, rollback/retry, or current auth denial respectively |
| Last owner | Concurrent removal/downgrade of final active owners | At least one active owner remains; rejected attempt is audited when policy requires |
| Outbox publisher | Two claimers, expired lease, partial batch acceptance, crash before/after broker acceptance | No lost destination; only lease owner marks success; duplicates remain safe |
| Consumer | Duplicate/out-of-order message, crash before/after inbox commit and before delete | One tenant-scoped durable effect; unfinished input is redelivered; metadata mismatch quarantines |
| RLS pool | Alternate A/B/missing scope on the same physical connections | Only current scope is visible/writable; missing scope returns no tenant rows |
| Migration/backfill | Concurrent old/new binaries and resumable ranges | Both versions operate on expanded schema; no skipped/duplicated rows; contraction remains deferred |

Run the relevant packages with `go test -race -count=1`; repeat concurrency cases with
seed capture to expose scheduling issues without using unbounded repetition as proof.

## Worker, Shutdown, And Backpressure Tests

Worker tests control message visibility and crash points rather than sleeping through
real lease intervals. They cover malformed/unsupported/tenant-mismatched events,
duplicate and future aggregate versions, bounded retry classification, visibility
extension, DLQ/quarantine handoff, controlled redrive, provider idempotency tokens,
and external unknown-outcome reconciliation.

Process-level tests start the API, publisher, or worker binary with disposable
dependencies, send work, then issue `SIGTERM`. Assertions require readiness to drop
before intake stops, tracked goroutines to join, completed work to be acknowledged,
unfinished work to remain recoverable, telemetry flush to remain bounded, and exit to
respect the configured grace. Saturating a worker pool must pause polling before
goroutines, memory, provider calls, or database connections grow without bound.

## Fixtures And Test Helpers

- Builders require explicit IDs, tenant, principal, clock, currency, and lifecycle
  state; defaults are limited to non-security display data.
- SQL fixture loaders use public repository/setup contracts or narrowly reviewed
  helpers and verify constraints after setup. They do not disable RLS globally.
- Local OIDC/session helpers sign with checked-in non-production keys and can produce
  wrong issuer/audience/nonce/time, revoked sessions, rotation overlap, and invalid
  CSRF material without logging raw tokens.
- Event builders separate trusted envelope tenant fields from deliberately mismatched
  payload fields and preserve event IDs across duplicate/replay cases.
- Fault seams are explicit test adapters or process termination points; production
  code does not contain unguarded sleep/panic flags.

## CI Placement And Release Signal

| Stage | Backend checks | Blocking signal |
| --- | --- | --- |
| Pull request | Format, `go vet`, unit/application, affected `httptest`, affected PostgreSQL/Testcontainer, OpenAPI generation, migration fresh/upgrade smoke, targeted race/fuzz corpus | Any required failure, race, generated drift, tenant/integrity defect, or unexplained flake blocks merge |
| Main/nightly | All packages with race detector, complete repository/RLS/worker/process suite, previous-release upgrade, fuzz/property corpus | Regression blocks the current release candidate and receives an owner |
| Release candidate | Immutable binaries against production-shaped staging: migration, smoke, concurrent timer/invoice/idempotency, backlog, shutdown and selected fault tests | Exact invariants, bounded resources, and truthful async state must pass |
| Production readiness | Current RDS failover/restore, runtime-role tenant evidence, capacity and security review | No open critical/high correctness, tenant, financial, migration, or recoverability gap |

The release signal is behavioral. A high line-coverage result cannot waive a missing
foreign-tenant, concurrent-commit, migration, or crash-window test.
