# Proposed Resilience Architecture

## Purpose And Status

This document defines how the target ClouDesk runtime contains failures and recovers
without claiming that the system is already deployed. It covers the Go API, outbox
publisher, workers, PostgreSQL, SQS, optional Redis, external providers, Kubernetes
nodes, and one AWS Availability Zone.

Related decisions and contracts are [Amazon SQS](../decisions/ADR-007-amazon-sqs-messaging.md),
[bounded Redis usage](../decisions/ADR-012-bounded-redis-usage.md),
[rolling deployments](../decisions/ADR-019-rolling-deployments.md),
[asynchronous processing](async-processing.md), and
[disaster recovery](disaster-recovery.md).

## Reliability Posture

The production target is one AWS Region across multiple Availability Zones. It is
designed for process, pod, node, worker, dependency, and single-AZ failures. It is not
an initial multi-region design, and it cannot promise uninterrupted service during a
regional event or prolonged failure of the authoritative PostgreSQL database.

The core invariants are:

- acknowledge only committed work; never return false success after a known rollback;
- preserve accepted asynchronous intent in PostgreSQL before relying on SQS or a
  provider;
- put finite time, attempt, concurrency, memory, connection, and queueing budgets on
  every path;
- isolate interactive API capacity from outbox, documents, reports, and providers;
- cancel work that has lost its caller, lease, deadline, or safe ability to commit;
- degrade optional capabilities before failing authoritative business correctness;
- use liveness to repair a broken process, readiness to stop intake, and alerts to
  repair dependencies. Dependency outages must not trigger restart storms.

## End-To-End Deadlines And Timeouts

Timeouts are owned at the caller boundary and become smaller toward each dependency.
`context.Context` carries cancellation and deadlines through Go handlers, use cases,
pgx, AWS adapters, and worker operations. It is never stored on a service or replaced
with `context.Background()` on an active request/message path.

The following are starting configuration bounds, not SLOs or guarantees; load tests
and provider behavior must tune them without violating the parent deadline:

| Operation | Initial bound | Notes |
| --- | ---: | --- |
| Ordinary API request | 10 seconds overall | Below ingress idle limits; expensive exports return a durable `202` instead of holding the request. |
| PostgreSQL pool acquisition | 500 milliseconds | Fast overload signal; do not queue every request behind an exhausted pool. |
| Ordinary statement / short transaction | 2 / 5 seconds | A transaction gets one parent budget, not a fresh timeout per query. |
| Redis cache/rate-limit call | 100 milliseconds | At most one request-path attempt; apply endpoint-specific degraded behavior. |
| OIDC discovery/JWK refresh | 2 seconds | Previously cached, still-valid keys continue verification; key refresh never blocks all request workers indefinitely. |
| S3 presign or metadata request | 2 seconds | Upload/download bytes remain browser-to-S3; document worker calls use their job budget. |
| SQS publish API call | 5 seconds | Owned by the outbox publisher, never the source API transaction. |
| Email provider call | 15 seconds | Runs from a durable delivery intent with its own retry budget. |
| Worker attempt | 30 seconds to 10 minutes by queue | Always shorter than visibility plus commit/delete margin; see the async workload budgets. |
| Graceful termination | API 30 seconds; worker/publisher 60 seconds initially | Kubernetes grace exceeds application drain plus propagation/telemetry margin. Long jobs checkpoint or become visible again. |

HTTP server header-read, body-read, idle, and maximum-body limits are finite and
route-aware. A generic write timeout must not terminate an intentionally streamed
response; streaming requires a separate reviewed contract. Cancellation is checked
before committing a result, but once a database commit has succeeded its durable
truth is not undone because the client disconnected.

## Retry Ownership And Budgets

Retries occur only where the owner can classify the operation and its outcome. They
use exponential backoff with full jitter, respect trustworthy `Retry-After` values,
and stop on cancellation, a non-retryable error, attempt exhaustion, or total-age
budget. SDK defaults are explicitly configured so SDK, adapter, worker, ingress, and
client layers do not multiply one another's retries.

| Dependency/action | Retry policy | Safety rule |
| --- | --- | --- |
| PostgreSQL read before any mutation | At most 2 retries for a transient connection error within the request deadline | Only when no result/side effect was observed. |
| Short serializable transaction | At most 2 whole-transaction retries with jitter | The whole use case is retry-safe and constraints/idempotency remain the backstop. |
| Ambiguous or interrupted commit | No blind internal replay | Return an unavailable/unknown outcome; the client retries the same `Idempotency-Key`, which reveals a committed response or safely executes after rollback. |
| Redis | No request-path retry | Cache falls through; abuse-sensitive controls use conservative local/edge enforcement or reject safely. |
| Outbox to SQS | Bounded by the outbox delivery policy | Duplicate acceptance is safe; event ID and consumer inbox close the ambiguity window. |
| SQS consumer | Queue-specific receive budget; no nested whole-message loop | Delete only after durable acceptance/effect. Visibility delay implements backoff. |
| S3/provider mutation | Retry only with a conditional request, deterministic object key, or stable provider idempotency token | An unknown non-idempotent outcome goes to reconciliation, not blind replay. |
| Ordinary client-visible `4xx` | Never | Validation, authorization, precondition, and domain conflicts require a changed command or user action. |

Clients may retry transport failures, `429`, and documented retryable `503` responses
with bounded jitter. Sensitive mutation retries retain the same idempotency key. The
API does not ask a caller to create a new key after an unknown outcome.

## Circuit Breakers And Degradation

A circuit breaker is useful only for a remote, repeatedly failing dependency when
fast rejection preserves scarce capacity and a half-open probe can demonstrate
recovery. Initial candidates are the email provider, optional Redis, and remote JWK
refresh. Breakers are per dependency and operation class, use a rolling failure and
latency window, open for a bounded cool-down, admit a small number of half-open probes,
and emit state-transition metrics. Thresholds are set from load/fault testing rather
than copied globally.

There is no generic breaker around PostgreSQL, every repository method, or SQS
consumption. PostgreSQL safety comes from pool/statement deadlines, admission limits,
and readiness; outbox backoff naturally limits an SQS outage. A breaker must never
discard durable work or turn a required authorization/data-integrity check into a
fail-open path.

| Dependency unavailable | Safe degraded behavior | Never do |
| --- | --- | --- |
| PostgreSQL | API stops authoritative mutations/reads and becomes unready; workers stop taking DB-dependent work; liveness stays healthy | Serve stale process-memory business state, acknowledge messages, or restart-loop every pod. |
| Redis cache | Bypass to bounded PostgreSQL queries; reduce optional expensive reads if the DB budget is threatened | Treat cached data as authoritative or let cache miss traffic exhaust RDS. |
| Redis rate-limit store | WAF/edge and conservative local limits continue; reject an abuse-sensitive operation when safe enforcement is impossible | Fail open for login, invitation, export, or other high-abuse paths merely for availability. |
| SQS | API commits business state and outbox; async status remains pending; publisher backs off and backlog is alerted | Publish directly from the API, lose the outbox, or claim delivery completed. |
| S3 | Metadata and authorization remain in PostgreSQL; new presign/generation may return unavailable or retry; affected files remain pending/unavailable | Mark an upload/PDF ready before storage confirmation. |
| Email provider | Durable notification intent remains pending/failed with bounded retry; source invoice/task remains committed | Roll back the source fact or report email delivered on request acceptance. |
| OIDC control plane | Existing sessions validate with cached, unexpired keys while safe; login/refresh/key-rotation paths may be unavailable | Accept unverifiable tokens or extend expired credentials. |

## Bulkheads, Backpressure, And Load Shedding

Bulkheads are concrete capacity boundaries, not a framework abstraction:

- API, outbox publisher, lightweight workers, and document/report workers receive
  separate pgx pools or database roles with explicit per-replica maxima.
- The database budget reserves connections for migrations and operations, then divides
  the remainder across maximum planned replicas. HPA maximums and worker concurrency
  cannot make the sum exceed that budget.
- Notification provider calls, S3 work, PDF generation, and reporting each have a
  bounded semaphore. Their queues and DLQs are independent, so one workload cannot
  consume every worker slot.
- Every process uses bounded channels and supervised goroutines. SQS long polling
  pauses when no slot or downstream budget is available.
- API admission controls reject excess tenant/route work before expensive parsing or
  database acquisition. Quota/rate rejection uses `429`; transient server-capacity
  rejection uses `503` with a bounded `Retry-After` when accurate.
- Autoscaling uses request rate/latency and queue oldest-message age/depth, but maximum
  replicas remain capped by RDS, provider quotas, and available node capacity.

Saturation is not solved by opening more queues in memory. Pool wait time, active
connections, queue age, rejection rate, memory, CPU throttling, and provider quota are
observed together. When the broker is unavailable and outbox rows approach the
database high-water threshold, the system preserves invoice/timer correctness while
shedding optional exports, bulk notifications, and other non-critical async producers.

## Process Lifecycle And Graceful Shutdown

All Go binaries use one signal-derived root context and a supervisor that owns and
joins every goroutine. Kubernetes sends `SIGTERM`; a pre-stop/readiness transition
allows ingress or polling to drain before the process exits.

### API

1. Set readiness false, stop accepting new connections after ingress propagation,
   and keep liveness true.
2. Cancel queued but not-started work and call `http.Server.Shutdown` with the drain
   deadline.
3. Let in-flight handlers finish only while their original or shutdown deadline is
   valid. A completed commit remains authoritative even if the response cannot be
   delivered.
4. Flush bounded telemetry, close idle transports and the pgx pool, join supervisors,
   then exit. Force-close after the grace deadline and report an abnormal drain.

### SQS Workers

1. Set readiness false, cancel long polls, and stop receiving immediately.
2. Allow in-flight messages to finish within the smaller of their job deadline and
   termination grace; extend visibility only inside that window.
3. Delete messages whose durable effects/intents committed. Cancel and leave every
   unfinished message undeleted so it becomes visible for another replica.
4. Stop visibility heartbeats, flush bounded telemetry, close clients, and join all
   workers. A worker never deletes a message merely because shutdown began.

### Outbox Publisher

1. Set readiness false and stop claiming batches.
2. Finish already-started sends within the grace deadline and acknowledge only entries
   accepted by SQS while the local lease is still owned.
3. Leave unsent/unacknowledged deliveries leased; another publisher reclaims them
   after lease expiry. This may duplicate a timed-out send and is safe by design.
4. Release clients and join the supervisor.

Kubernetes `terminationGracePeriodSeconds` exceeds the application drain plus
readiness propagation and telemetry margin. A PodDisruptionBudget protects voluntary
disruption availability but does not prevent node or AZ loss. Rolling deployments
allow old/new API and consumer versions to overlap, so database, HTTP, and event
contracts remain backward compatible throughout the maximum replay window.

## Health Model

| Probe | What it proves | What it must not include | Failure action |
| --- | --- | --- | --- |
| `/health/live` | Event loop/supervisor is responsive and the process is not irrecoverably deadlocked | PostgreSQL, SQS, Redis, S3, OIDC, email, queue depth, or ordinary saturation | Kubernetes restarts only a broken process. |
| `/health/ready` for API | Initialization is complete, process is not draining, and a short PostgreSQL acquisition/check shows it can safely serve authoritative requests | Optional Redis, SQS, email, S3, or an arbitrary downstream aggregate health check | Remove from ALB/service endpoints; do not restart. |
| `/health/ready` for worker/publisher | Process is not draining, has local capacity, and its required intake plus PostgreSQL boundary is usable | Email/S3 provider availability when durable intent can be accepted; queue backlog by itself | Stop assigning/claiming new work and surface rollout/operations failure. |
| Startup probe | Configuration, schema compatibility, and local initialization completed within a bounded startup window | A license to run migrations from every replica or wait forever for optional dependencies | Delay liveness/readiness; fail permanently invalid configuration. |

A transiently full pool or non-empty backlog is a metric and backpressure signal, not
by itself a reason to make every replica unready. Readiness changes when the process
cannot safely make progress for a bounded confirmation window or is deliberately
draining. Probe endpoints are cheap, have strict timeouts, and return no dependency,
credential, topology, or tenant details.

## Failure Scenarios And Recovery

| Failure | Expected behavior and user impact | Recovery and no-loss boundary | Primary signals |
| --- | --- | --- | --- |
| API pod/process dies | In-flight uncommitted requests fail; ALB routes new traffic to ready replicas. A committed response lost in flight is recovered by HTTP idempotency. | Stateless replica replacement; PostgreSQL commit and idempotency record are authoritative. | Availability/error rate, pod restart, readiness, idempotency replays. |
| Outbox publisher dies | Source commands continue; publication lag increases. A send accepted before crash may be duplicated. | Leases expire and another replica reclaims; consumer inbox suppresses duplicate effects. | Oldest outbox age, expired claims, publish errors, blocked deliveries. |
| Worker dies during a message | That attempt stops; no committed effect means no acknowledgement. Crash after commit produces a harmless duplicate delivery. | SQS visibility expiry and inbox/effect transaction recover ownership. External work resumes from its durable intent. | Visibility age, receive count, duplicate count, worker restart, DLQ. |
| RDS instance/failover | Existing connections and open transactions may abort; API may return retryable unavailable responses and readiness becomes false. Workers leave messages unacknowledged; outbox remains in RDS. | RDS Multi-AZ promotes the standby behind the stable endpoint. Pools discard broken connections and reconnect with jitter. Transactions are retried only when outcome is known safe; ambiguous commands use the same idempotency key. | Connection errors, failover event, pool wait, readiness, API `503`, queue/outbox age. |
| Prolonged PostgreSQL outage | Authoritative reads/writes stop; async queues retain messages but workers stop intake. Optional static UI may remain, without stale claims of business truth. | Restore service/readiness, reconnect gradually, then drain queues under database budgets. DR handles unrecoverable data loss. | Database availability, all readiness, queue age, RPO/RTO runbook trigger. |
| Redis outage | Cache misses increase DB load; sensitive distributed rate-limit paths use conservative fallback or reject. No business data is lost. | Breaker/backoff prevents retry storm; recover cache lazily, never mass-warm against RDS. | Redis errors/breaker, cache hit rate, DB load, rate-limit fallback count. |
| SQS regional/service outage or IAM denial | API business commits continue with pending outbox rows. Workers cannot receive; async user states remain pending and backlog alerts rise. | Fix service/IAM; publisher resumes bounded claims, workers drain under concurrency caps. PostgreSQL outbox is the durable handoff. | Publish/poll errors, outbox age/count, queue age when visible, blocked rows. |
| Email/S3 dependency outage | Only the affected capability degrades; invoices/tasks remain committed. Delivery/generation state exposes pending or failed status. | Durable intents retry within budget; terminal/ambiguous outcomes reconcile or enter controlled replay. | Provider breaker, intent age, error code, S3 latency, failed status. |
| EKS node loss | Pods on the node terminate; in-flight requests/messages behave like process loss. Other-zone replicas continue if capacity remains. | Deployment/ReplicaSet reschedules stateless pods; SQS visibility and outbox/inbox recover work. Node autoscaling restores capacity. | Node not-ready, unavailable replicas, reschedule time, request/queue age. |
| One Availability Zone fails | Some ALB targets/nodes disappear; remaining zones serve reduced capacity. RDS may fail over; SQS and S3 remain managed regional dependencies. Latency/errors can briefly rise. | Critical workloads use multiple replicas with topology spread across at least three zones and enough remaining headroom; Multi-AZ RDS reconnects; queues absorb worker loss. | AZ target health, topology skew, RDS failover, capacity, error rate, queue age. |

Single-AZ survival depends on actually provisioning replicas and spare/rapidly
restorable capacity in other zones; topology constraints alone do not create capacity.
HPA and node provisioning are too slow for every sudden loss, so production sizing
must define acceptable N+1 headroom for the selected SLO. A regional outage follows
the separate disaster-recovery design and is not masked as automatic multi-region
failover.

## Failure Propagation Rules

- A source domain commit does not wait for PDF, reporting, SQS, Redis, or email. Their
  failure becomes explicit lag/pending state, not rollback of authoritative truth.
- A required authorization, tenant-scope, invoice invariant, or PostgreSQL commit
  never degrades open. Correctness failure stops the request/message.
- A worker does not acknowledge input after a downstream database rollback. It may
  acknowledge after atomically recording a durable external-effect intent.
- A retry storm is contained at the nearest owner with jitter, concurrency caps, and
  circuit/backoff. Errors are not synchronously fanned back through already committed
  business workflows.
- Recovery traffic is treated as load: outbox catch-up, DLQ redrive, cache misses, and
  pod rescheduling all obey the same database/provider budgets as steady state.

## Resilience Verification

Before production readiness, fault and process tests must prove observable hypotheses:

| Experiment | Expected evidence |
| --- | --- |
| Kill an API pod during uncommitted and committed idempotent requests | No partial transaction; same key recovers the committed outcome; remaining replicas continue. |
| Kill publisher before send and after simulated SQS acceptance | Lease recovery publishes every event; duplicate delivery produces one consumer effect. |
| Kill worker before inbox commit, after commit, and before SQS delete | Redelivery occurs; one tenant-scoped durable effect; no lost external intent. |
| Exhaust each worker pool and PostgreSQL allocation | Polling/admission slows before unbounded goroutines, memory, or DB connections appear. |
| Disable Redis | Cache bypass/fallback policy activates without business-state loss or a database retry storm. |
| Deny SQS or email/S3 access | Outbox/intents remain durable, retry is bounded, user-visible status is truthful, alerts identify IAM/dependency failure. |
| Trigger an RDS Multi-AZ failover | Open transactions fail safely, pools reconnect with jitter, readiness recovers, messages redeliver, and no false success/data loss is observed. |
| Drain a node and simulate one-AZ capacity loss | PDB/topology behavior is understood, remaining zones serve within declared reduced capacity, and queue backlog drains after replacement. |
| Redrive poison and duplicate DLQ canaries | Unsupported messages remain quarantined; valid events preserve IDs and inbox deduplication; replay stops on renewed error. |
| Send `SIGTERM` under API and worker load | Readiness drops first, intake stops, completed work is acknowledged, unfinished work becomes recoverable, and exit stays within grace. |

Each experiment records request/event IDs, data-loss expectation, recovery time,
error/latency and queue-age impact, alert firing/recovery, and any exhausted retry or
capacity budget. Passing a happy-path probe is not evidence that these failure
boundaries work.
