# Proposed Alerting And Incident Signals

## Purpose

Define which ClouDesk conditions should page, create a ticket, or remain dashboard
signals, together with their ownership and recovery expectations.

## Principles

Alerts are planned, not active. Page only for current user impact, imminent loss of a
durability/security invariant, or a recovery control requiring prompt human action.
Every page has an owner, severity, dashboard, concrete first action, runbook, tested
query, deduplication key, and recovery condition. Metrics without action become
dashboards or tickets.

## Routing And Severity

| Severity | Route | Examples |
| --- | --- | --- |
| SEV-1 | immediate primary + incident commander/security as applicable | cross-tenant access, lost/duplicated financial effect, unrecoverable write corruption, regional outage |
| SEV-2 | immediate service/platform on-call | fast/sustained SLO burn, blocked outbox, unavailable authoritative database, failed PITR protection |
| SEV-3 | working-hours ticket with deadline | slow burn, capacity forecast, restore drill overdue, telemetry cost/cardinality trend |

Group by environment/service/SLO or queue, suppress child symptoms during a declared
parent incident, and inhibit staging pages from production routing. Deployment,
migration, AWS event, and incident annotations are immutable identifiers. Silence
requires owner, reason, expiry, and alternate observation; a maintenance window does
not hide correctness or backup failure.

## Initial Alert Catalog

| Alert | Trigger shape | Route/runbook |
| --- | --- | --- |
| SLO burn | Multi-window rules in [SLI/SLO](sli-slo.md) with minimum volume | service on-call / high burn |
| Correctness or tenant isolation | any verified mismatch, audit-write failure, inbox metadata mismatch, duplicate financial effect | SEV-1 security/domain incident |
| Outbox blocked/old | any `BLOCKED`; oldest unpublished above 5 min with growth | async owner / queue backlog |
| DLQ/integrity | any new DLQ arrival; immediate for tenant/schema integrity | async/security / controlled replay |
| Queue user impact | oldest age breaches workload objective and service rate is below arrival, with downstream guardrails | worker owner / backlog |
| PostgreSQL unavailable/saturated | readiness/user errors plus RDS event, pool wait, or connection/CPU/storage guardrail | backend/database / RDS failover |
| Backup/PITR protection | automated backup failed, restorable window below policy, snapshot/state/object recovery evidence stale | platform / backup-restore |
| EKS capacity | critical replicas unavailable, AZ skew plus insufficient survivor capacity, prolonged unschedulable pods/IP exhaustion | platform / capacity |
| Dependency degradation | S3/SQS/OIDC/provider errors with user impact or durable intent age | owning service runbook |
| Telemetry blind spot | synthetic canary missing, collector drops/export queue high, SLI data stale | observability owner; do not restart applications |
| Cost/cardinality | forecast/ingestion/active series exceeds reviewed warning or hard budget | daytime observability/platform ticket |

Raw CPU, memory, queue depth, pod restart, and Redis errors do not page alone unless
they predict an imminent invariant or explain user-impacting burn.

## Rule Quality And Verification

Rules and notification templates are version-controlled. Unit tests cover normal,
failure, recovery, missing data, counter reset, no traffic, and label churn. Staging
drills prove fire time, deduplication, routing, dashboard links, runbook usefulness,
and automatic resolution. A quarterly review removes noisy/unowned alerts and checks
that every page resulted in action; target fewer actionable pages, not hidden failure.
