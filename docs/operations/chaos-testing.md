# Proposed Chaos And Resilience Validation

## Purpose

Define safe, hypothesis-driven experiments that can validate ClouDesk failure and
recovery behavior without treating uncontrolled disruption as engineering evidence.

## Safety Contract

Chaos is controlled hypothesis testing, not random production failure. Begin with
unit/process/integration tests, then isolated staging with synthetic multi-tenant data.
Production experiments require mature alerts/runbooks, explicit change authority,
small blast radius, named abort control, incident/on-call awareness, and proven
rollback. Never inject cross-tenant access, destroy backups/state, expose secrets, or
perform unrecoverable deletion.

Every experiment records: hypothesis; steady-state SLI; scope; injection; expected
user impact and data loss (**normally none**); expected detection/alert; recovery path
and time; abort threshold; telemetry; result; and follow-up owner. Missing telemetry
fails the experiment rather than proving resilience.

## Planned Experiment Matrix

| Experiment | Hypothesis and expected impact/recovery | Required evidence |
| --- | --- | --- |
| Kill one API pod during uncommitted and committed idempotent requests | Ready replicas continue; no partial transaction; same key recovers committed outcome | availability/latency, readiness, DB state, idempotency replay, alert expectation |
| `SIGTERM` API/worker/publisher under load | Readiness/intake stops first; completed work commits/acks; unfinished work is redelivered within grace | drain time, open requests/jobs, telemetry flush bound, one durable effect |
| Kill publisher before send and after simulated SQS acceptance | Lease recovery publishes all committed events; ambiguous send may duplicate but inbox makes one effect | outbox age/leases, event ID, publish attempts, duplicate counter |
| Kill worker before/after inbox commit and before delete | Visibility redelivery recovers work; same event produces one tenant-scoped durable effect/intent | inbox rows, receive count, effect count, queue age |
| Queue backlog / poison message / delayed SQS | Bounded pools stop unbounded goroutines/DB use; poison reaches DLQ; healthy work drains within objective after repair | arrival/service rate, oldest age, pool/DB/provider, DLQ alert and canary replay |
| Deny SQS publish/poll | API keeps authoritative commit plus outbox; async states remain pending; bounded retry and alert | outbox growth/high-water, user status truth, recovery drain without storm |
| Redis outage (only if adopted) | Cache degrades to bounded DB; abuse-sensitive paths reject conservatively; no business loss | DB load, fallback/rejection, breaker, readiness unchanged |
| Email provider `500`/timeout/throttle | Source fact remains committed; durable intent retries within budget or ends visibly; no duplicate provider effect | attempt/age/status, idempotency token, breaker, alert |
| S3 latency/outage | Upload/PDF remains pending/unavailable, never falsely ready; metadata stays authoritative | presign/generation errors, object/metadata reconciliation, recovery |
| RDS Multi-AZ failover | Open transactions fail safely; readiness withdraws; pools reconnect with jitter; ambiguous writes reconcile; queues redeliver | AWS event, connection/pool/503, transaction/idempotency invariants, measured recovery |
| Exhaust pgx pool / slow query | Admission/polling slows before global exhaustion; API and workers retain allocated budgets | pool waits, rejections, latency, connections, cancellation/leak evidence |
| Drain node / kill node | PDB governs voluntary drain; other nodes serve; workers redeliver; replacement is schedulable | replicas/topology, requests, queue age, pod/IP/node launch timing |
| Partial AZ loss | surviving AZ capacity preserves correctness with declared degraded service; RDS may fail over; backlog drains safely | ALB targets, topology/capacity, SLO burn, RDS, queue drain, no data loss |
| Collector/gateway/backend outage | application remains available; bounded telemetry queues drop visibly; missing interval is unknown; canary recovers | exporter/drop/queue metrics from independent path, request/job outcomes, gap |
| Argo/HPA/node-autoscaler/metrics adapter outage | existing baseline continues; promotions/elasticity pause; no scale-to-zero; operator follows bounded manual path | replica/pending state, alerts, GitOps reconciliation after recovery |

Regional loss and logical corruption are recovery exercises, not casual live chaos;
run the [DR drill](disaster-recovery.md) with isolated restores.

## Load, Soak, And Fault Composition

Establish a k6 steady-state baseline before injection. Test normal, burst, sustained,
concurrent timers/invoices, reports and backlog separately before combining a single
fault with representative traffic. Measure throughput, p50/p95/p99, valid-request
error rate, SLO burn, CPU/memory/throttling, goroutines, pgx/RDS, lock/query latency,
queue age/service rate, provider limits, and telemetry cost/loss.

Soak tests run long enough to expose memory/connection/goroutine leaks, database
bloat/vacuum pressure, outbox/inbox cleanup lag, retry synchronization and telemetry
cost. Fault recovery continues until backlog and saturation return to baseline; an
experiment does not pass merely because the injection ended.

## Progression And Exit Criteria

Progress process test → local integration → isolated staging → production-shaped
staging → narrowly scoped production only when the previous level has current evidence.
Pass requires expected detection, bounded impact/recovery, no unexpected data loss or
cross-tenant effect, alerts/runbook that operators could use, and all cleanup complete.
Any surprise updates architecture, automated regression tests, runbooks and capacity
limits before repetition.
