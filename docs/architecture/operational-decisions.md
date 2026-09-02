# Mandatory Architecture Questions

## Purpose

This integration record answers the mandatory design questions directly and links to the documents that own the detail. Answers describe proposed ClouDesk behavior.

## Technology And Boundaries

| Question | Decision |
| --- | --- |
| Why Go? | Small stateless binaries, explicit concurrency/lifecycle, strong HTTP and PostgreSQL ecosystem, and clear operational behavior fit API/workers; see [ADR-001](../decisions/ADR-001-go-backend.md). |
| Why TypeScript in the frontend? | It gives typed consumer feedback and safe refactoring around a generated API contract, while runtime validation remains server-owned; see [ADR-002](../decisions/ADR-002-nextjs-typescript-frontend.md). |
| Why a modular monolith? | One team and many cross-domain transactions benefit from local boundaries without network failure modes; see [ADR-004](../decisions/ADR-004-modular-monolith-and-workers.md). |
| Why not microservices initially? | Independent deployability, ownership, and scaling do not yet outweigh consistency, local-development, and operations costs. |
| What could become services, and when? | Invoice/PDF processing, notifications, files, and reporting are candidates only after sustained independent scale, availability, workload isolation, ownership, or release pressure; see [scalability](scalability.md). |
| Why PostgreSQL? | Relational tenant ownership, financial constraints, transactions, mature indexing, and outbox atomicity; see [ADR-003](../decisions/ADR-003-postgresql-system-of-record.md). |
| Why sqlc and pgx? | Reviewed tenant-aware SQL stays visible while typed Go access and PostgreSQL-native transaction control reduce mapping errors; see [ADR-005](../decisions/ADR-005-sqlc-and-pgx.md). |
| Which messaging system and why? | Amazon SQS standard queues for managed durability, DLQs, long polling, AWS IAM, and low operational burden; NATS/RabbitMQ are rejected initially and Kafka has no need; see [ADR-007](../decisions/ADR-007-amazon-sqs-messaging.md). |

## Consistency And Concurrency

| Question | Decision |
| --- | --- |
| What remains synchronous? | Authorization, validation, state transitions, money calculation, timer start/stop, invoice issue commit, and any response requiring authoritative state. |
| What becomes asynchronous? | PDF generation, email, most notifications/audit projections, exports, aggregate refresh, malware scan, and external side effects. |
| Where are transactions required? | Aggregate mutations plus constraints, audit facts, idempotency result, and outbox event; invoice issue/number/lines/time links; timer concurrency; membership/role changes. Network calls never occur inside them. |
| Where is idempotency required? | Invoice creation/issue/send intents, timer start/stop, uploads completion, exports, invitations, provider callbacks, outbox publishing, and every message consumer; see [idempotency](../api/idempotency.md). |
| Where is optimistic locking required? | Invoice drafts/settings and selected project/organization settings where a stale overwrite loses material work; HTTP uses ETag/`If-Match`. Timer uniqueness uses database constraints/locking instead. |
| How are events not lost? | Business change and outbox row commit atomically; a publisher retries unpublished rows until SQS accepts them; see [ADR-008](../decisions/ADR-008-transactional-outbox-and-inbox.md). |
| How are duplicates prevented from causing duplicate effects? | Stable event IDs, consumer-specific inbox uniqueness, atomic effect+inbox commits, provider idempotency keys, and durable sent/file state. |
| How are retries performed? | Only retry-safe failures, bounded exponential backoff with jitter, visibility-aware SQS attempts, retry budgets, and DLQ after exhaustion. |

## Failure Behavior

| Question | Decision |
| --- | --- |
| What if Redis fails? | PostgreSQL truth remains intact. Read caches degrade to bounded DB reads; ordinary limits may use conservative local fallbacks, while sensitive abuse limits fail closed/conservatively. Timeouts/circuit behavior protect capacity. |
| What if messaging fails? | Synchronous commits continue with outbox rows; lag grows and alerts fire. Features dependent on async side effects show pending state. No event is marked published until broker acceptance. |
| What if a worker dies? | SQS visibility expires and another replica retries. Inbox idempotency prevents duplicate durable effects; shutdown stops intake and bounds drain time. |
| What if PostgreSQL fails? | Readiness removes API/worker traffic that cannot safely operate; in-flight transactions fail and retry only at safe operation boundaries. No cache or queue becomes an alternative source of truth. |
| What occurs during RDS failover? | Connections/transactions may break, pools refresh DNS/connections with jitter, retry-safe commands replay through idempotency, and non-idempotent unknown outcomes are reconciled before retry. |
| What if an EKS node dies? | ReplicaSets reschedule pods, readiness gates traffic, SQS returns unacked messages, topology spread limits simultaneous loss, and connection budgets prevent a restart storm. |
| What if one AZ fails? | Production replicas and nodes span AZs; ALB routes to survivors, RDS Multi-AZ fails over, and reduced-capacity alerts/load shedding protect correctness. |

## Security And Compatibility

| Question | Decision |
| --- | --- |
| How is cross-tenant access prevented? | Organization-prefixed routes, membership/permission checks, organization-required repository arguments/SQL, tenant-aware FKs/unique keys, selective RLS, scoped caches/events/jobs/S3, and negative tests; see [multi-tenancy](multi-tenancy.md). |
| How is S3 protected? | Private encrypted buckets, block-public-access, workload IAM, opaque tenant-prefixed keys, short constrained presigned URLs, metadata authorization, content limits, safe disposition, scan/quarantine, and reconciliation. |
| How are APIs versioned? | `/api/v1` is the compatibility boundary; additive compatible changes remain in v1, semantic diff gates breaking changes, and deprecation precedes a new major path; see [OpenAPI](../api/openapi.md). |
| How are database migrations performed without downtime? | Expand schema, deploy compatible dual behavior, resumably backfill, switch reads/writes, observe, and contract later; see [ADR-020](../decisions/ADR-020-expand-contract-migrations.md). |

## Scale, Health, And Reliability

| Question | Decision |
| --- | --- |
| What is the likely first bottleneck? | PostgreSQL connections and tenant list/aggregate query pressure, before Go API CPU. Bound pools, index representative access, cap queries, and precompute proven hot aggregates. |
| How will we know when to scale? | API saturation/latency/error signals, database pool wait/query latency, queue age/depth/drain time, worker utilization, and SLO burn—not CPU alone. |
| How is health determined? | Liveness proves process progress; startup covers initialization; readiness covers required ability to serve without depending on optional Redis/telemetry. Business health comes from SLIs, not probe status alone. |
| Which SLIs? | Valid-request availability, latency by route class, error rate, queue age, async completion latency, outbox lag, notification/PDF success, database/pool health, and critical journey success. |
| Which SLOs make sense? | Start with proposed 99.9% valid-request availability, route-specific latency targets, and bounded async completion; validate baselines and business needs before approval; see [SLIs/SLOs](../operations/sli-slo.md). |

## Recovery And Validation

| Question | Decision |
| --- | --- |
| How is restore performed? | Restore RDS PITR into isolation, recover/verify S3 objects and secrets, reconcile Terraform/GitOps/artifacts, run tenant/financial integrity and application smoke checks, then cut over deliberately. |
| How is DR validated? | Timed restore exercises, regional table-top/rebuild drills, recorded RPO/RTO evidence, and correction of runbooks/readiness gaps. |
| How is resilience tested? | Inject API/worker/node loss, Redis/SQS/provider failure, RDS failover, queue backlog, latency, and partial-AZ loss with hypotheses, expected impact/recovery, data-loss, metrics, and alerts. |
| When would multi-region make sense? | Contractual availability beyond regional risk, mandatory residency, unacceptable geography latency, or measured regional business impact that exceeds complexity/cost. |
| Which decisions wait for real data? | Aurora, read replicas, partitioning, Redis, data warehouse, service extraction, Kafka, service mesh, Karpenter tuning, canary automation, multi-region, and fine-grained custom roles beyond the initial permission map. |
