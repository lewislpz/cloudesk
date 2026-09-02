# Proposed Operations Runbooks

## Purpose

Define the minimum operator procedures for diagnosing, mitigating, recovering, and
learning from the highest-impact ClouDesk incidents.

## Common Contract

These are planned procedures; exact commands, consoles, roles and links are filled in
and exercised before production. Every runbook records incident ID, environment,
release/config changes, start/end, owner, evidence, customer impact, decisions and
follow-up. Use least-privilege, time-bounded access; never paste secrets, payloads,
Terraform state, presigned URLs, or customer data into incident channels.

For every incident: acknowledge and assign commander; verify user impact/SLO burn;
freeze risky changes; preserve correctness/durable work; mitigate with the smallest
reversible action; validate recovery from user and dependency signals; reconcile any
manual change into GitOps/Terraform; communicate; and write actionable learning.

## High SLO Burn

1. Open the SLO and RED dashboards; verify data freshness, numerator/denominator,
   route/journey, release, region/AZ and dependency correlation.
2. Stop or roll back the latest release/config only when timing and canary comparison
   support causality. Do not scale API into saturated RDS/provider capacity.
3. Contain: shed optional work, cap retries/concurrency, pause reports/redrive, or
   restore known-good digest within documented budgets.
4. Confirm burn falls in both windows, errors/latency recover and queues do not hide
   deferred impact. Continue until budget trajectory is safe.

## RDS Failure Or Failover

1. Confirm AWS RDS event/endpoint, pgx connection/pool waits, readiness, open
   transactions and idempotent-command outcomes. Keep liveness unchanged.
2. Stop deployments/migrations and API/worker scale-out; let pools reconnect with
   jitter. Workers leave uncommitted messages unacknowledged.
3. Do not blindly retry ambiguous commits. Reuse the same idempotency key or reconcile
   authoritative resource/idempotency state.
4. After recovery, slowly resume intake, observe connections/locks/queue age, sample
   critical invariants and record failover duration. If data is unavailable/corrupt,
   invoke DR rather than improvising restore.

## Outbox Backlog, Queue Age, Or DLQ

1. Compare oldest age, arrival/successful service rate, outbox status, SQS/IAM,
   worker readiness/concurrency, DB/provider headroom and poison/error classes.
2. Repair the cause before scaling. Cap/stop the producer or optional workload if
   outbox/DB protection thresholds approach; never delete durable rows/messages.
3. For DLQ, validate schema/version/tenant and inbox/provider idempotency on a minimal
   sanitized sample. Deploy data/code repair first.
4. Redrive a small canary preserving event ID; stop on renewed error or saturation,
   then increase within DB/provider budgets. Never delete inbox rows to force replay.

## Telemetry Blind Spot

1. Use independent AWS/EKS health to decide whether this is service or telemetry
   failure. Check synthetic canary, SDK drops, agents, gateways, queues/exporters,
   IAM/quota/backend health.
2. Restore collectors/backends within bounded buffers; do not restart healthy apps or
   make readiness depend on export.
3. Reduce optional debug/trace volume if capacity/cost caused loss, preserving SLI,
   security, backup and pipeline metrics. Mark incident intervals as unknown, never
   green, and document evidence gaps.

## Optional Redis Or External Provider Outage

Open the dependency/degradation dashboard; activate the documented cache bypass or
conservative abuse-control failure mode; protect RDS/provider quotas with breakers and
concurrency caps; retain durable intents/pending states; never claim delivery or lose
business truth. Recover gradually without mass cache warming or retry storms.

## Backup Restore / Disaster Declaration

Freeze writes/applies and preserve evidence; identify failure scope and last-known-good
point; follow [backups](backups.md) for isolated restore or
[disaster recovery](disaster-recovery.md) for rebuild; require independent integrity
validation and go/no-go before traffic. Record measured RPO/RTO, not configured values.

## Load And Resilience Validation Runbook

Use synthetic multi-tenant data in isolated staging. Define hypothesis, traffic/job
mix, duration, arrival rate, data sizes, expected SLO/saturation, abort thresholds,
owners and rollback. k6 scenarios cover normal, burst, sustained/soak, project/task
lists, concurrent timers, invoice creation, file authorization, reports and queue
backlog. Observe throughput, p50/p95/p99, errors, CPU/memory/throttling, pgx/RDS,
queue age/drain, provider limits, telemetry loss and cost.

Abort on correctness/tenant evidence, uncontrolled error budget burn, DB storage/
connection safety limit, runaway cost, or inability to restore. Afterward reconcile
created data, verify no leaked goroutines/connections/backlog/bloat, compare to the
baseline, and convert bottlenecks into owned changes. A maximum-throughput number
without failure/recovery evidence is not a production capacity result.
