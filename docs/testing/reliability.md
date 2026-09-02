# Proposed Reliability, Chaos, And Recovery Testing

## Purpose And Status

This document turns the [resilience architecture](../architecture/resilience.md) and
[disaster recovery objectives](../architecture/disaster-recovery.md) into planned
experiments. It covers crash safety, readiness, graceful termination, failover,
backlog, restore, and regional rebuild. No experiment has run, so the proposed RPO of
5–15 minutes and in-region RTO of 30–60 minutes remain objectives, not guarantees.

## Experiment Contract And Safety

Every experiment records owner, target allowlist, hypothesis, steady-state signals,
injected fault, expected user impact, data-loss expectation, expected recovery and
time, alert/runbook expectation, abort thresholds, rollback, invariant queries, and
sanitized evidence. It first runs at process/integration level, then isolated staging,
then production-shaped staging. Production chaos is exceptional and is never the
first execution.

Abort immediately on tenant disclosure, financial/timer corruption, lost committed
intent, backup damage, security-control loss, unexpected blast radius, unavailable
rollback, or sustained SLO/database/cost guardrail breach. Recovery traffic obeys the
same pool, retry, provider, and queue budgets as steady state.

## Fault And Chaos Matrix

| Experiment | Hypothesis and expected impact | Recovery/no-loss boundary | Evidence and alert expectation |
| --- | --- | --- | --- |
| Kill API pod/process | Ready replicas continue; uncommitted request fails and a lost committed response is replayable | PostgreSQL transaction/idempotency record; no partial state | Error/latency, readiness/target removal, restart, replay; availability alert only if objective breached |
| Kill publisher around SQS send | Lease reclaims unsent work; acceptance ambiguity may duplicate but not lose | Outbox delivery plus consumer inbox | Oldest outbox age, expired lease, duplicate count; lag/publish alerts fire and recover |
| Kill worker before/after inbox commit/delete | Uncommitted work redelivers; committed effect is not repeated | Inbox/effect transaction and SQS visibility | Receive count, one effect, restart/queue age; worker/age alert behaves as runbook states |
| Send `SIGTERM` under load | Readiness drops before intake; completed work finishes; unfinished work is recoverable within grace | Tracked goroutines, transaction/message acknowledgement rules | Probe transition, in-flight/exit time, undeleted work, telemetry flush |
| Exhaust worker/DB pools | Backpressure pauses polling/admission before unbounded growth | Fixed pools/semaphores, HPA maxima and RDS connection budget | Pool wait, rejections, queue age, memory/goroutines; saturation alert is actionable |
| Redis outage/failover | Optional cache misses/degrades; abuse-sensitive controls reject conservatively; no truth is lost | PostgreSQL authority and endpoint-specific fallback | Redis breaker/errors, fallback rate, DB load, safe `429/503`; no readiness restart storm |
| SQS broker denial/delay | Business commands commit outbox and remain pending; workers/publisher back off | PostgreSQL outbox is durable handoff | Publish/poll errors, outbox/queue oldest age, bounded retries and IAM/dependency alert |
| Email/S3/provider `500`, throttle or timeout | Source fact remains committed; durable intent becomes pending/retryable/reconciled, never false success | Delivery/generation intent plus stable provider key/deterministic object | Breaker, attempt/age/status, user-visible state, provider alert without secret payload |
| Queue backlog/poison redrive | Essential traffic remains within budget; valid canary drains; poison re-quarantines | Bounded pools, DLQ, preserved event ID/inbox | Drain rate/age, DB/provider saturation, DLQ and stop-on-renewed-error alert |
| Network latency/partition | Deadlines/cancellation stop retry amplification and isolate affected dependency | Bounded time/attempt/concurrency; no fail-open auth or tenant check | Timeout/error classification, goroutines/pools, breaker/retry budget and burn alert |
| Drain EKS node | Other replicas continue and pods reschedule without PDB deadlock | Stateless pods, SQS redelivery, topology/capacity | Unavailable/pending pods, reschedule time, service/queue impact, node alert |
| Remove one-AZ capacity | Surviving zones serve declared reduced capacity; RDS may fail over; correctness remains | Three-AZ placement, survivor headroom, managed data durability | AZ targets/topology, error/latency, RDS/queue age, capacity alert and measured recovery |
| Trigger RDS Multi-AZ failover | Open transactions fail safely; pools reconnect with jitter; reads retry safely; mutations resolve ambiguity by key/state | RDS durability, PostgreSQL idempotency/resource state, unacknowledged messages | Failover event, readiness, pool reconnect/wait, `503`, exact invariant queries and recovery time |

Controller-specific exercises stop the AWS Load Balancer Controller, Argo CD, HPA
metrics, and node autoscaler independently. Existing traffic/workloads should continue
where designed; reconciliation or scaling pauses; baseline capacity prevents
scale-to-zero; alerts and recovery from pinned Terraform/GitOps state are verified.

## Health And Rollout Verification

- `/health/live` proves only a responsive supervisor/event loop; PostgreSQL, Redis,
  SQS, S3, OIDC, email, backlog, and normal saturation failures must not restart-loop
  the process.
- API readiness proves initialization, non-draining state, and bounded required
  PostgreSQL progress. Optional dependencies remain excluded. Worker/publisher
  readiness means safe willingness to poll/claim, not an empty queue.
- Startup rejects invalid configuration/schema compatibility within a bounded window
  and never runs migrations from every pod.
- Rolling deployment tests use mixed old/new API, schema, event, and consumer versions,
  `maxUnavailable: 0` for critical web/API, readiness/min-ready behavior, and digest
  rollback while expanded schema remains compatible.
- PDB/topology tests prove both one voluntary disruption and schedulability/recovery;
  a PDB that blocks node/cluster maintenance fails the gate.

## Restore And Disaster-Recovery Matrix

| Recovery source | Exercise | Required validation |
| --- | --- | --- |
| RDS backups/PITR | Restore a selected point into isolated RDS and time it | Schema/migrations, tenant counts/isolation, memberships, active timers, invoice totals/numbers/immutability, audit/outbox/inbox/idempotency invariants and app smoke |
| S3 versions/lifecycle | Recover representative ready, deleted/versioned, invoice PDF and report objects | Metadata/object/checksum match, quarantine and deletion ledger reapplied, no public/foreign access |
| Terraform state | Restore a verified version/copy to an isolated key, then refresh-only/normal plan | Lineage/serial/encryption, expected inventory, no unintended create/delete/replacement |
| GitOps/EKS | Rebuild cluster/add-ons/namespaces/workloads from Terraform, Git, Helm and secret references | Private access, workload identity/IAM denial, probes, ingress, policies, drift and rollout |
| ECR/artifacts | Pull every deployed/rollback digest into recovery environment | Digest/provenance/scan match; no dependency on mutable `latest` |
| Secrets/KMS | Recreate/restore references and exercise rotation overlap | Workloads receive only owned secret; logs/state reveal none; old credential revokes safely |
| Events | Reconcile restored outbox with SQS/DLQ/inbox retention | No lost accepted intent, duplicate effects, cross-tenant replay, or replay beyond safe dedupe without procedure |

Restore is successful only after application-level reads and invariant checks, not
when AWS reports the resource available. The exercise records backup point, achieved
RPO/RTO, DNS/connection recovery, data gaps, runbook corrections, and cleanup. At
least quarterly after production begins, restore RDS plus representative S3 and
platform state. Run an annual regional-disaster tabletop and an isolated regional
rebuild before claiming a regional RTO.

## CI Placement And Production Gate

- **Pull request/integration:** deterministic crash points, probe semantics, shutdown,
  retries, inbox/outbox, and restore tooling validation.
- **Nightly/scheduled:** pool saturation, provider faults, backlog and controlled DLQ
  canaries in isolated environments.
- **Release candidate/material platform change:** kill pod/worker, rolling rollback,
  node drain, selected dependency denial/latency, backlog recovery, RDS failover and
  current restore evidence in production-shaped staging.
- **Recurring operations:** quarterly restore/game day and annual regional tabletop;
  every finding updates tests, alerts, runbooks, capacity, and readiness evidence.

Promotion blocks when expected data-loss is not zero for a committed invariant,
recovery exceeds the approved objective without disposition, readiness/liveness acts
incorrectly, alerts or runbooks fail, rollback is unavailable, restore integrity is
uncertain, or evidence is stale for the changed failure boundary.
