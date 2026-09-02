# Proposed Performance And Load Testing

## Purpose And Status

ClouDesk plans to use k6 for API and workflow load, with platform metrics supplying
database, queue, worker, and Kubernetes evidence. This document defines workload
shapes and release gates; it does not claim tested capacity or an SLO. Approved
budgets must be calibrated from representative staging data and recorded with the
candidate revision before production.

## Workload Model

Define an approved normal arrival rate `L`, representative tenant/data distribution,
and maximum supported concurrency from capacity planning. Avoid a single super-tenant
fixture: include many small tenants, several medium tenants, and one bounded heavy
tenant to expose fairness and tenant-leading query behavior.

| Profile | Shape | Purpose | Placement |
| --- | --- | --- | --- |
| Script smoke | Very small fixed load for minutes | Validate scripts, auth, checks, and result export | Pull request without a production claim |
| Normal | `L`, mixed reads/commands for at least 30 minutes | Establish latency, errors, resource use, and query baseline | Scheduled and every release candidate |
| Burst | Rapid ramp to the approved burst multiplier, short hold, controlled recovery | Admission, HPA lag, pool/provider protection | Release candidate/material scaling change |
| Sustained | Normal-to-high target for at least 60 minutes | Stable throughput and saturation limits | Release candidate |
| Soak | Representative `L` for 6–12 hours | Memory/goroutine/connection leaks, bloat, cache/telemetry cost | Scheduled and before initial production/material runtime change |
| Backlog recovery | Preload bounded outbox/queue backlog, then continue foreground traffic | Drain time, fairness and downstream budgets | Release candidate and worker/platform changes |

Durations and multipliers are initial test parameters, not service promises. Change
them only through a versioned capacity profile so results remain comparable.

## k6 Scenario Matrix

| Scenario | Load and invariant | Required observations |
| --- | --- | --- |
| Project/task listing | Mixed filters, equal sort keys, first/following cursors, large and small tenants | p50/p95/p99, throughput, no gaps/duplicates, query plans/time, rows scanned, pool wait |
| Concurrent timers | Many users start/stop normally; adversarial same-user requests use same/different keys across one and two organizations | Exactly one active timer per user, one stopped duration/audit/outbox effect, documented replay/conflict, no tenant leak |
| Invoice creation/issue | Parallel drafts, shared time-entry contention, same-key retries, stale versions, organization counter contention | One allocation/number/snapshot, correct totals, bounded lock wait/deadlocks, no duplicate event/PDF intent |
| Report summary/export | Bounded date ranges and dimensions; synchronous summaries plus async exports | Statement/query time, rows scanned, worker duration, result status, interactive latency isolation |
| Queue/outbox backlog | Backlog equal to an approved recovery horizon while normal commands continue | Oldest age/depth, publish/consume rate, DLQ/retry, DB connections, provider quota, time to drain |
| Auth/files/rate limits | Session validation, presign metadata, ordinary and abuse-sensitive quotas | Rejection correctness, Redis absent/failure mode if adopted, no unsafe fail-open |
| Mixed business traffic | Weighted login/read/task/timer/invoice/file/report journey | End-to-end capacity, tenant fairness, resource and cost envelope |

Workload setup and teardown are outside timed measurements. Every synthetic mutation
uses explicit test tenants and deterministic idempotency keys. Validation queries run
after the load to prove exact database, audit, outbox, inbox, and object invariants;
HTTP success rate alone is insufficient.

## Metrics And Threshold Model

Collect k6 throughput and p50/p95/p99 duration/error rate together with:

- API/web CPU, memory, GC, goroutines, throttling, restarts, request queueing and
  deadline/load-shed counts;
- PostgreSQL CPU/I/O, p95/p99 query time, rows, connections, pool wait, lock wait,
  deadlocks, transaction age, temp spill, autovacuum/bloat and storage growth;
- worker in-flight count/duration/failures, outbox count/oldest age, queue depth/oldest
  age, retries, visibility extension, DLQ and provider throttle rate;
- Redis latency/hit/eviction/degraded mode only if adopted; cache loss must not hide
  business correctness;
- pod/node pending time, HPA desired/actual replicas, node provisioning, AZ placement,
  network errors, and telemetry ingest/cardinality/cost.

Each candidate has numeric route-class latency/error, queue-age/drain, and resource
budgets derived from proposed SLOs and downstream capacity. Hard invariant thresholds
are always zero cross-tenant disclosures, duplicate financial/timer effects, lost
events, unbounded growth, or false completed status. Aggregate planned PostgreSQL
connections, including maximum replicas and operational reserve, remain below the
documented budget (initially about 70% of the RDS connection limit).

Soak acceptance requires stable post-warm-up trends: no monotonic goroutine, memory,
connection, queue, transaction-age, temp-file, or high-cardinality series growth;
cleanup/vacuum catches up; and telemetry cost remains inside its approved budget.

## Isolation, Safety, And Repeatability

Run material load only in production-shaped staging or an isolated performance
environment with synthetic data and explicit target allowlists. k6 refuses an
unapproved hostname/account and carries a run ID in test data. Abort automatically on
cross-tenant/integrity failure, sustained error/SLO burn, database protection limit,
runaway cost, or environment instability. Load never becomes the first failover or
chaos test; combine them only after both pass independently.

Record source/digest, OpenAPI/migration/chart/config revisions, environment topology,
data cardinality, workload profile, k6/tool version, thresholds, raw summary,
dashboards/traces, invariant queries, and cost estimate. Compare against a named
baseline rather than unrelated historical runs.

## Production Gate

PR validates scripts only. Scheduled runs detect regressions. A release candidate or
material query/pool/HPA/worker/platform change must pass normal, burst, sustained,
concurrent-timer, invoice, report, and backlog scenarios; initial go-live also needs a
soak. Promotion blocks on an approved budget miss, unexplained material regression,
resource leak, fairness failure, violated exact invariant, or missing evidence.

Production receives bounded synthetic smoke and real telemetry by default, not active
capacity or soak tests. Capacity claims are revised from measured evidence; k6 results
from a smaller or topologically different environment must be labeled and cannot
alone prove production capacity.
