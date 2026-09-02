# Proposed Metrics And Dashboard Contract

## Purpose And Status

This document defines planned ClouDesk metric names, labels, recording rules, and
dashboards. It is not an implemented catalog. Metrics provide aggregate behavior and
SLO accounting; logs and traces provide bounded diagnostic detail. Objective formulas
are defined in [SLIs and SLOs](sli-slo.md), while alert routing is defined in
[alerting](alerting.md).

## Naming And Label Policy

Application metrics use Prometheus naming conventions with base units and a
`clouddesk_` prefix for domain-owned instruments. Standard OTel/HTTP/runtime metrics
may retain their semantic-convention names after one reviewed normalization at the
collector. Counters end in `_total`; durations are seconds; sizes are bytes; queue
ages are seconds; monetary amounts are not exported as unbounded per-invoice labels.

Allowed labels come from bounded vocabularies: `service`, `environment`, route
template, method, status class, stable error code class, domain operation, queue,
worker/job class, outcome, event type/version, provider class, and database operation
class. A new label requires a measured upper bound and series-cost estimate.

Never label a metric with organization/user/resource/request/event/trace/message/pod
UID, invoice number, S3 key, raw path/query, SQL text, email/domain, client-provided
value, or exception message. `organization_id` is available only in restricted logs
or traces where policy permits. Per-tenant fairness uses bounded top-N analysis from
protected logs or a separately governed aggregate pipeline, not an unbounded label.

## Web And API RED Metrics

| Signal | Proposed instrument | Required dimensions and interpretation |
| --- | --- | --- |
| Request rate | `http_server_request_duration_seconds_count` or normalized equivalent | service, environment, method, route template, status class; excludes probes/static assets from SLO views |
| Duration | `http_server_request_duration_seconds` histogram | Explicit buckets around 50 ms, 100 ms, 300 ms, 1 s, 3 s, and timeout bounds; tune with data |
| Errors | Derive from request counter plus stable outcome/error class; optionally `clouddesk_http_failures_total` | `5xx`, internal timeout/cancellation ownership, capacity rejection, and unexpected contract failures; do not count all `4xx` as service errors |
| In flight | `http_server_active_requests` | service and route class, not raw route when series cost is high |
| Load shedding | `clouddesk_http_rejections_total` | reason class `tenant_quota`, `rate_limit`, `db_budget`, `server_capacity`; policy quota and service overload remain distinguishable |
| Browser journeys | `clouddesk_web_journey_total` and duration histogram | bounded journey (`login`, `project_list`, `timer`, `invoice_issue`, `file_upload`) and outcome; no tenant/resource identifiers |
| Web performance | allowlisted Web Vital histograms | release, environment, route group, device class only when privacy/cardinality review accepts it |

Histograms use explicit reviewed buckets or native histograms only after backend cost
and compatibility are tested. p95/p99 are computed from aggregated histograms, never
by averaging client-side percentiles.

## Domain And Correctness Metrics

Domain counters are emitted after the authoritative transaction outcome is known.
They do not contain financial amounts or customer dimensions.

| Area | Proposed metrics |
| --- | --- |
| Identity/tenancy | `clouddesk_authentication_total{outcome,reason}`, `clouddesk_authorization_total{operation,outcome}`, `clouddesk_tenant_scope_rejections_total{boundary}` |
| Projects/tasks | `clouddesk_projects_created_total{outcome}`, `clouddesk_task_transitions_total{from_state,to_state,outcome}` with bounded states |
| Time tracking | `clouddesk_timer_commands_total{operation,outcome}`, `clouddesk_active_timer_conflicts_total` |
| Invoicing | `clouddesk_invoice_commands_total{operation,outcome}`, `clouddesk_invoice_generation_duration_seconds{outcome}`, `clouddesk_invoice_pdf_intents_total{outcome}` |
| Files | `clouddesk_file_lifecycle_transitions_total{from_state,to_state,outcome}`, `clouddesk_presign_requests_total{operation,outcome}` |
| Notifications | `clouddesk_notification_intents_total{channel,outcome}`, `clouddesk_notification_terminal_duration_seconds{channel,outcome}` |
| Audit | `clouddesk_required_audit_writes_total{operation,outcome}`; any failed required write is a correctness event |
| Idempotency/inbox | `clouddesk_idempotency_requests_total{operation,outcome}`, `clouddesk_inbox_events_total{consumer,outcome}` where outcome includes new/duplicate/mismatch |

Business reporting such as revenue, utilization, and client profitability remains an
authorized product query, not an observability metric exposed to platform operators.

## Outbox, Queue, And Worker Metrics

The application exports durable-state metrics from PostgreSQL and worker metrics;
AWS native SQS metrics are ingested alongside them. Depth alone is insufficient.

| Boundary | Required signals |
| --- | --- |
| Outbox | due/pending/blocked delivery count, oldest unpublished age, claim rate, claim lease expiry, publish attempts/outcomes, batch size, publish duration, and cleanup lag |
| SQS source queue | visible and not-visible count, oldest visible message age, send/receive/delete rates, empty receive rate, approximate delayed messages, and AWS throttling/errors |
| Worker | ready replicas, configured/active concurrency, pool utilization, poll pause reason, processing duration/outcome, successful durable effects per second, visibility extension/failure, retries by class, shutdown abandoned/completed work |
| DLQ | visible messages, oldest age, arrivals/redrives, replay canary outcome, and quarantined integrity failures; payloads never become labels |
| External intent | pending/processing/retryable/permanent/ambiguous counts, oldest pending age, provider latency/error/throttle, and terminal completion duration |

`ApproximateNumberOfMessages*` is operationally approximate. SLOs should prefer
application-observed event/intent timestamps and committed terminal state when that
produces a more accurate user outcome. Alerts use depth, age, arrival/service rate,
and downstream capacity together, consistent with [scaling](scaling.md).

## PostgreSQL And Pool Metrics

| Layer | Required signals |
| --- | --- |
| pgx per process/class | configured max, acquired, idle, constructing, acquire count, acquire wait duration, cancelled acquire, connection lifetime/closure, query/transaction duration and outcome |
| RDS | connections and maximum headroom, CPU, freeable memory, read/write latency and IOPS/throughput, storage/free space, transaction/log pressure where available, replication/failover events, restart/maintenance, network, and burst balance for applicable storage |
| PostgreSQL engine | transaction rate, locks/waits, deadlocks, long transactions, statement timeout, temporary files, checkpoints/WAL, cache hit context, vacuum/analyze age, dead tuples/bloat indicators, and `pg_stat_statements` normalized query performance |
| Data safety | backup/PITR status and age, restore-test age/result, schema migration status, outbox/inbox cleanup age, audit write failures |

Query labels use a reviewed normalized query name/fingerprint, never SQL text or bind
values. RDS enhanced monitoring/performance tooling access is restricted because it
may expose identifiers or query fragments. The aggregate connection-budget formulas
in [scaling](scaling.md) are visualized for current and maximum replicas.

## EKS, AWS, And Telemetry Pipeline

At minimum collect ready/desired/unavailable replicas, restarts, OOM kills, CPU
usage/throttling, memory working set, pending/unschedulable pods by bounded reason,
node readiness and pressure, allocatable/requested resources, pod IP/subnet headroom,
HPA current/desired/limited conditions, node-autoscaler errors and launch latency,
topology distribution, ALB target health/latency/status, WAF blocks, NAT/endpoint
errors, and AWS quota headroom.

The observability plane measures itself: accepted/refused/dropped logs/spans/metric
points, receiver/exporter errors, queue capacity/utilization/oldest item, retry count,
gateway memory/CPU, scrape/remote-write lag, backend ingestion/query errors, active
series and bytes/spans/logs per service, synthetic canary age, and estimated cost.
Missing telemetry is data, not a green zero.

## Dashboard Set

Every panel identifies source, unit, aggregation, freshness, environment, owner, and
runbook. Deployment and incident annotations use immutable release/change IDs.

1. **Service and SLO overview:** current 30-day compliance, remaining budget,
   multi-window burn, valid-event volume, missing-data indicator, and critical journey
   outcomes by service.
2. **Web and API RED:** rate, status/error class, p50/p95/p99, in-flight, rejection,
   browser journey/Web Vitals, release comparison, and slow route templates.
3. **Async durability:** outbox oldest/count/blocked, SQS depth/age, arrival versus
   successful service rate, worker concurrency, inbox duplicate/mismatch, external
   intent age, DLQ, and projected clearance time.
4. **PostgreSQL capacity:** RDS health, connections against the 70% application
   budget, pool waits by workload, slow normalized queries, locks/deadlocks,
   transactions, storage/WAL/vacuum, failover, backup and restore status.
5. **EKS and capacity:** replicas/readiness, resources/throttling/OOM, pending pods,
   nodes/IPs/AZ skew, HPA/autoscaler state, ALB targets, deployment health, and cost.
6. **Dependency degradation:** Redis (if adopted), S3, SQS, OIDC/JWK, email provider,
   circuit/backoff state, quotas, retries, and user-visible pending/failure outcomes.
7. **Telemetry health and cost:** SDK/collector/backend drops, queues, export latency,
   canary freshness, active series/cardinality, ingestion volume, retention, and cost
   budget.
8. **Backup and DR evidence:** last successful backup/PITR window, object/state/image
   recovery coverage, drill age/duration, measured RPO/RTO, and unresolved recovery
   gaps.

Dashboards link from summary to detail and then to sanitized logs/traces using
request/trace/event IDs. Variables allow environment, service, release, route class,
queue, and error code; they never expose organization/customer names.

## Recording Rules And Verification

Recording rules materialize SLI numerators/denominators, error ratios, latency bucket
ratios, queue completion latency, backlog clearance, DB connection headroom, and
telemetry loss. Rules are version-controlled and unit-tested with synthetic time
series for success, no traffic, missing data, counter reset, deployment label change,
and failure windows.

Before production, a controlled load test must prove metric overhead, histogram
accuracy, bounded series growth, AWS/application correlation, and dashboard refresh.
Inject representative errors, queue backlog, RDS pool saturation, pod loss, collector
outage, and backup failure. An alert or dashboard is not accepted until an operator
can reach the right diagnosis and runbook without querying customer content.

