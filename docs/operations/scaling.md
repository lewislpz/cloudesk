# Proposed Scaling And Capacity Operations

## Purpose And Status

This document turns ClouDesk scaling principles into a staged operating model for
web/API pods, asynchronous workers, PostgreSQL connections, and EKS nodes. Values are
initial hypotheses to validate in staging; they are not implemented settings,
benchmarks, SLO guarantees, or permission to scale past a dependency budget.

See [Kubernetes architecture](../infrastructure/kubernetes.md),
[architecture scalability](../architecture/scalability.md),
[resilience](../architecture/resilience.md), and
[PostgreSQL data design](../architecture/data-model.md).

## Governing Rules

- Optimize the measured constraint before adding replicas. Correct unbounded queries,
  N+1 access, missing tenant-leading indexes, payload size, retry multiplication, and
  unsafe concurrency first.
- Keep API/web stateless and scale them independently from queue workers.
- Protect PostgreSQL and providers with hard replica, connection, concurrency, and
  retry ceilings. HPA maximum is a capacity control, not a guessed large number.
- Scale interactive workloads from demand/saturation/latency and asynchronous
  workloads from backlog clearance and downstream headroom. CPU alone is insufficient.
- Preserve at least the production baseline during metrics/autoscaler failure; do not
  scale critical workloads to zero.
- Treat backlog recovery, pod restarts, node replacement, deployments, and an AZ loss
  as capacity events. Autoscaling is not fast enough to replace tested survivor
  headroom.

## Scale Units And Ownership

| Unit | What scaling changes | Owner | It must not silently change |
| --- | --- | --- | --- |
| Web pod | SSR/UI request capacity | Application/platform | API or database capacity |
| API pod | HTTP concurrency and pgx pool count | Application/platform | RDS total connection budget |
| Outbox publisher pod | Claim/publish throughput | Async owner | Database claim pressure or event ordering contract |
| Worker pod | Queue consumption concurrency | Queue/workload owner | Provider quota, DB allocation, visibility/retry policy |
| EKS node | Schedulable CPU, memory, pod/IP capacity | Platform | Workload replica intent |
| RDS instance/storage | Authoritative database capacity | Database/AWS owner | Query correctness or application admission limits |

HPA changes pods; a node autoscaler supplies room for pending pods. Neither proves that
RDS, SQS consumers, email, S3, subnet IPs, or AWS quotas can accept the extra load.

## Measurement Prerequisites

Autoscaling remains disabled or conservative until the following metrics are fresh,
bounded in cardinality, and tested during failure:

- web/API request rate, in-flight requests, p50/p95/p99 latency by route class,
  valid-request error ratio, deadline cancellation, CPU throttling, memory working set,
  restarts, and ready replicas;
- pgx pool maximum/acquired/idle, acquire wait count and duration, query/transaction
  latency, connection failures, RDS connections/CPU/IOPS/storage/locks/deadlocks;
- per queue: visible and in-flight messages, oldest-message age, receive/delete rate,
  processing duration, retry/visibility extension, DLQ arrivals, and successful drain
  rate;
- per worker: in-flight jobs, bounded pool utilization, CPU/memory, provider throttle
  and error rate, and durable effect completion latency;
- pending pods by reason, unschedulable duration, allocatable/requested node resources,
  pod-IP availability, node launch/ready time, evictions, Spot interruptions, and AZ
  distribution;
- SLO burn and critical journey signals. A green HPA metric with elevated user errors
  is not healthy capacity.

Tenant ID must not be a raw unbounded metric label. Detect noisy-neighbor behavior
through sampled/top-tenant operational analysis and privacy-safe aggregate buckets.

## Web And API HPA Policy

The initial HPA v2 policy uses stable resource utilization because it is available
without a custom metrics control plane, while operators correlate it with request and
database signals. CPU requests must be representative because utilization is measured
against them.

| Workload | Production minimum | Initial maximum | Scale-out evidence | Scale-in guard |
| --- | ---: | ---: | --- | --- |
| Web | 3 | Set by load test and node budget | Sustained CPU/request-concurrency saturation with rising p95/p99 or queueing | At least 10 minutes stable low demand; retain three-AZ baseline |
| API | 3 | Derived from RDS pool allocation and tested throughput | Sustained CPU or in-flight saturation plus p95/p99 pressure while DB/provider headroom remains | At least 10 minutes stable low demand; no elevated errors, DB waits, or SLO burn |

Begin with a 60-70% CPU utilization target and conservative scale-up behavior; tune it
from throttling and latency evidence. Memory is primarily a right-sizing/OOM signal,
not the only scale trigger. After representative traffic exists, a reviewed custom
metric such as target in-flight requests per ready pod may supplement CPU. Latency is
a decision/alert signal unless the metric pipeline and its causal relationship are
stable enough to control scaling; scaling on downstream latency during an RDS outage
would make the outage worse.

When DB acquire wait, RDS connections/CPU, a provider throttle, or error ratio crosses
its guardrail, freeze pod scale-out at the safe maximum and shed/defer expensive work.
API overload returns bounded `429` for quota/rate excess or retryable `503` for
temporary capacity, never an unbounded internal queue.

## Queue Worker Scaling Policy

Workers scale per queue/failure class. Queue depth alone is misleading because job
duration varies; oldest-message age shows user impact but is not proportional enough
to be the sole replica calculation. Use a backlog-clearance model:

```text
arrival_rate      = messages arriving per second over a stable window
service_rate      = successful messages per pod per second at safe concurrency
backlog           = visible messages eligible for processing
clearance_window  = seconds in which recoverable backlog should drain

desired_replicas = ceil((arrival_rate + backlog / clearance_window) / service_rate)
safe_replicas    = min(desired_replicas, DB limit, provider limit, node limit, configured max)
```

`service_rate` uses successful durable effects, not receives or attempts. Recalculate
it by worker/job class from load tests; document generation must not inherit the email
worker's rate. An HPA external metric adapter or KEDA-style SQS scaler may implement
the calculation later, but that controller is introduced only after its IAM, outage,
metric freshness, and fallback behavior are tested. Until then, use HPA CPU for
compute-bound document work and reviewed manual replica changes guided by queue age.

| Worker | Primary signal | Secondary guardrails | Production minimum and scale-in |
| --- | --- | --- | --- |
| Outbox publisher | Oldest unpublished delivery age and due rows | RDS lock/pool wait, SQS publish errors/throttle | Minimum 2 coordinated replicas; scale slowly and prove `SKIP LOCKED` claim efficiency |
| Notification | Backlog clearance and oldest-message age | Provider quota/throttle, DB allocation, DLQ rate | Minimum 2; scale in only after queue and in-flight work are stable below target |
| Document | Backlog clearance, job duration, CPU/memory | S3/RDS capacity, object-size class, node availability | Minimum 1-2 based on completion objective; one initial job slot per pod; never mix tiny and huge jobs blindly |
| Audit/reporting | Projection lag/oldest age | DB CPU/IO and query duration | Preserve audit freshness; isolate reporting or pause optional projections before harming interactive DB load |

Scale-out is deliberately faster than scale-in, but no faster than nodes and
downstreams can absorb. Use stabilization windows and policies that add a bounded
number/percentage of pods per interval. Scale-in waits through at least one longest
normal job window, stops polling first, and lets in-flight work finish or become
visible. Production durable workers do not scale to zero until cold-start latency,
metric failure, and replay behavior explicitly satisfy the workload objective.

## PostgreSQL Connection Budget

PostgreSQL connections are expected to be the first shared bottleneck. Let `C_db` be
the verified connection limit of the selected RDS instance/parameter group. ClouDesk
application pools together must remain at or below 70% of `C_db`; the rest is reserved
for RDS behavior, migrations, operations, incident access, failover recovery, and
measurement error.

```text
C_app = floor(0.70 * C_db)

API allocation                = floor(0.55 * C_app)
all worker allocations        = floor(0.25 * C_app)
outbox publisher allocation   = floor(0.10 * C_app)
unassigned app headroom       = C_app - the allocations above

max_replicas(workload) * pool_max_per_pod(workload) <= workload allocation
sum(all max replicas * all pool maxima) <= C_app
```

The percentages are an initial planning split, not a substitute for measuring real
queries. The unassigned application headroom is intentional and is not automatically
consumed by HPA. Web has no database pool. Each worker class gets a sub-allocation;
document/report backlog cannot borrow all API connections. Use low/zero minimum idle
connections, a 500 ms initial pool-acquire deadline, finite statement/transaction
deadlines, maximum connection lifetime with jitter, and pool saturation telemetry.

Example only: if a validated RDS limit were 200, `C_app` would be 140, with up to 77
for all API pods, 35 for all workers, 14 for all publishers, and 14 unassigned. An API
maximum of 7 replicas would therefore permit at most 11 connections per pod
(`7 * 11 = 77`). Choose integer maxima from the actual instance and load test; do not
copy this example to production configuration.

Every replica-bound change runs a static budget check using the rendered environment
values. If one workload needs more connections, first improve query/concurrency
behavior, then deliberately rebalance allocations. Introduce PgBouncer or RDS Proxy
only after measured connection churn or replica count justifies it and transaction-
local RLS/pgx behavior is proven safe.

## Node Capacity And Autoscaling

### Initial EKS stage

Maintain an on-demand EKS managed node group across three AZs for system controllers
and baseline application capacity. Its minimum supports CoreDNS, CNI, Argo CD, ALB
controller, telemetry, three web/API replicas, and at least one worker per critical
queue after one planned node disruption. Keep resource and pod-IP headroom; CPU alone
does not reveal VPC CNI IP exhaustion.

Cluster Autoscaler may manage this group's desired size between explicit minimum and
maximum limits. It cannot repair AWS account quotas, unavailable instance types, full
subnets, hard affinity, PDB deadlocks, or invalid requests. Alerts distinguish those
causes from normal launch latency.

### Karpenter evaluation

Karpenter becomes preferred for elastic application capacity only if evidence shows
one or more of:

- managed node-group launch latency causes sustained pending pods or queue objective
  violations;
- document/report workloads need materially different CPU/memory shapes;
- safe multi-instance-type bin packing yields meaningful cost/capacity improvement;
- burst and Spot interruption handling has been validated and has an owner.

Keep a stable on-demand managed group for the controllers needed to create and route
new capacity. If adopted, define separate NodePools for general on-demand workloads
and explicitly interruptible asynchronous workloads, constrain approved architectures
and instance families, cap total CPU/memory, spread zones, and test consolidation and
interruption. API/web minimum capacity, Argo CD, ALB controller, DNS, CNI, telemetry,
and Karpenter itself do not run exclusively on Spot. Never let Cluster Autoscaler and
Karpenter manage the same nodes.

## Scaling Decision Matrix

| Observed condition | First action | Scale action only when | Do not |
| --- | --- | --- | --- |
| API latency rises; CPU and DB waits are low | Trace routes, check downstream and request concurrency | More pods improve throughput in a load test and connection budget permits | Scale on latency caused by RDS/provider failure |
| API CPU is sustained and p95 rises | Check throttling, hot code, request bounds | Per-pod throughput is CPU-bound and nodes/RDS have headroom | Raise limits or replicas without profiling |
| DB pool waits rise | Find long/N+1 queries, transactions, connection leaks | Query fixes are exhausted and a deliberate DB/pool plan exists | Add API pods; they multiply pools |
| Queue depth rises but oldest age is healthy | Compare arrival/service rate and scheduled bursts | Clearance forecast will miss objective | React to one transient depth spike |
| Oldest queue age rises | Check poison messages, provider/RDS throttle, worker health | More safe concurrency increases durable completion | Scale through a provider quota or DB saturation |
| Worker CPU/memory is high | Classify job sizes, profile, right-size | Work is parallelizable and downstream safe | Use memory HPA as recovery from OOM |
| Pods are pending | Inspect events: resources, affinity, PDB, IPs, quotas, instance availability | The constraint is genuinely node capacity | Assume every pending pod needs another node |
| One tenant dominates | Enforce per-tenant admission/fairness and job limits | Shared capacity is still broadly saturated afterward | Solve noisy-neighbor behavior only with global scale |
| SLO burn with normal saturation | Investigate correctness/dependency errors first | Capacity is causal and verified | Treat autoscaling as incident diagnosis |

## Failure And Recovery Behavior

- **Metrics/custom adapter failure:** HPA holds the last/current replica posture under
  Kubernetes behavior; baseline replicas remain. Alert on metric age and use reviewed
  manual bounds. Never interpret missing data as zero demand.
- **HPA/controller failure:** running pods continue. Freeze promotions that require new
  capacity, confirm PDB/replica state, and change replicas manually only within DB/node
  budgets. Reconcile the temporary change through GitOps.
- **Node autoscaler or AWS capacity failure:** existing nodes serve baseline traffic;
  pods may remain pending. Shed/defer optional reports, cap API admission, and allow
  queues to absorb work. Do not evict healthy baseline capacity to chase a burst.
- **RDS failover:** stop scale-out, readiness removes unsafe intake, pools reconnect
  with lifetime jitter, and retries remain idempotency-safe. Recovery traffic uses the
  same connection budget; it does not open emergency unlimited pools.
- **SQS/provider outage:** outbox/queue age grows, worker polling backs off, and API
  synchronous truth remains committed. More workers cannot repair an unavailable
  dependency and are not added.
- **Node/AZ recovery:** replacement pods reconnect gradually. HPA and queue scalers
  honor stabilization and database/provider ceilings so backlog catch-up does not
  create a reconnect or retry storm.
- **Spot interruption:** affected async pods stop intake and release recoverable work;
  on-demand baseline remains. Repeated interruption shifts the NodePool or workload
  back to on-demand rather than violating queue objectives.

## Operator Workflow

1. State the violated user/queue objective and time window; capture current replicas,
   ready pods, HPA conditions, node capacity, RDS/pool state, queue age/rate, provider
   limits, error rate, and recent deployments.
2. Classify the constraint as application, database, provider, queue/job shape,
   scheduler/node/IP/quota, metrics/control plane, or noisy tenant.
3. Contain unsafe demand with admission limits, paused optional workers, provider
   concurrency caps, or rollout halt. Preserve authoritative correctness and durable
   work.
4. Apply the smallest reversible change within the precomputed connection, provider,
   node, and cost budgets. Record a time limit and expected metric response.
5. Verify user latency/errors, queue drain trajectory, DB waits, retries, saturation,
   and cost. Roll back if the causal signal does not improve or a guardrail worsens.
6. Reconcile manual emergency changes into GitOps or revert them; update load tests,
   limits, forecasts, dashboards, and the runbook with the evidence.

## Capacity Review And Production Gates

Review capacity before each production milestone, after material traffic/job changes,
after RDS/node type changes, and at least monthly once production exists. Forecast
normal, peak, backlog recovery, rolling deployment surge, node loss, and one-AZ loss.
Include AWS quota and cost headroom, not only Kubernetes utilization.

Production scaling is acceptable only when:

- representative load tests establish per-pod request/job service rates and resource
  profiles, including large-tenant and large-document cases;
- rendered HPA maxima and every pgx pool maximum pass the 70% global connection-budget
  check with a separate allocation for each workload;
- scale-up/scale-down stabilization, metrics outage, provider throttle, RDS failover,
  backlog recovery, node drain, pending-pod, and one-AZ scenarios are exercised;
- the minimum three-AZ baseline fits real nodes/subnets and survives a voluntary node
  disruption without relying on immediate autoscaling;
- alerts and dashboards identify saturation before user objectives fail and route to
  an owned runbook;
- a before/after record demonstrates that each autoscaling or Karpenter change improves
  the measured constraint without unacceptable reliability or cost regression.
