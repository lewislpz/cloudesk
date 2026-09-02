# ClouDesk AWS Cost Management

## Purpose And Status

This document defines the proposed AWS cost model, allocation controls, optimization
rules, and cost-versus-reliability trade-offs for ClouDesk. It deliberately avoids
hard-coded price claims: Region, usage, commitments, and AWS pricing change, so a
versioned estimate from the AWS Pricing Calculator and actual Cost and Usage data are
required before each production capacity decision.

Related documents: [AWS target architecture](aws.md),
[networking](networking.md), and [environments](environments.md).

## Cost Principles

- Optimize architecture after correctness, tenant security, recoverability, and an
  approved production availability target; optimize non-production aggressively.
- Separate fixed platform cost from usage-driven cost. EKS control planes, NAT
  gateways, ALBs, interface endpoints, RDS/ElastiCache nodes, and minimum observability
  capacity can dominate an initially quiet SaaS.
- Add a managed service only for a named requirement and remove it when the requirement
  disappears. Portfolio value is not a sufficient production dependency.
- Measure unit cost and business value, not only the monthly AWS total. A cheaper
  service that causes operational toil or lost recovery evidence is not necessarily
  lower cost.
- Commit to Savings Plans, Reserved Instances, or other term discounts only after
  stable measured baselines; keep burst capacity and uncertain workloads flexible.

## Allocation And Guardrails

All supported resources carry cost-allocation tags where AWS supports them:

| Tag | Example | Purpose |
| --- | --- | --- |
| `Application` | `ClouDesk` | Product allocation |
| `Environment` | `dev`, `staging`, `production` | Environment budget and anomaly grouping |
| `Owner` | Platform team identifier | Escalation and lifecycle ownership |
| `ManagedBy` | `Terraform` | Drift and manual-resource detection |
| `CostCenter` | Approved internal code | Financial allocation |
| `DataClassification` | `public`, `internal`, `confidential` | Explains controls that constrain optimization |

Tenant identity should not become a high-cardinality resource tag. Tenant unit cost is
derived from application metrics and CUR allocation models, not thousands of AWS
resources per organization.

Configure AWS Budgets at organization, account, and environment levels; Cost Anomaly
Detection for material services; monthly forecast alerts; and a Cost and Usage Report
for detailed analysis when the operational overhead is justified. Alerts route to a
named owner with a runbook. Budget actions may stop expired previews or scheduled dev
capacity, but they never automatically stop production databases, clusters, logging,
or backups.

Account quota and Region allowlists prevent accidental duplication. Terraform policy
checks reject missing required tags, unapproved expensive instance families, public
resources, and resources without an owner/expiry when ephemeral.

## Principal Cost Drivers And Decisions

| Service/capability | Main cost dimensions | Initial decision | Optimization without weakening the contract |
| --- | --- | --- | --- |
| EKS | Per-cluster control plane, worker compute, EBS, load balancers, public IPv4, telemetry | Production target; staging after platform phase; no EKS prerequisite for local | Share a dev cluster/namespace only with explicit isolation; schedule nonprod workers; right-size requests; consolidate safe workloads; use Spot for interruption-tolerant workers after testing |
| NAT gateways | Gateway-hours per AZ, bytes processed, cross-AZ paths | Three in production; one or none in quiet nonprod | Same-AZ routing; S3 gateway endpoint; justified ECR/SQS/Secrets/STS endpoints; reduce noisy telemetry/image pulls; compare endpoint fixed cost before adding |
| Interface endpoints | Endpoint-hours per service per AZ and bytes | Selective, production-first | Deploy from traffic/security break-even analysis; omit quiet dev endpoints; remove unused endpoints |
| ALB | Load-balancer-hours, LCUs, processed traffic | One ALB per persistent environment routes Web and API | Share path routing inside an environment; avoid per-service ALBs; remove preview ALBs; tune keep-alive and payloads based on evidence |
| CloudFront and WAF | Requests, edge/data transfer, invalidations, WAF rules and evaluations | Production and staging edge path; dev only for edge tests | Cache immutable fingerprinted assets; avoid blanket forwarding; consolidate justified rule groups; sample/redact logs; do not cache tenant responses |
| RDS PostgreSQL | Instance-hours, Multi-AZ standby, storage/IOPS, backup beyond allowance, monitoring | Multi-AZ DB instance in production and production-shaped staging tests; smaller/Single-AZ dev | Right-size from CPU/memory/IO/connection data; gp3/default storage before provisioned IOPS unless measured; tune queries/pools; reserve stable production baseline; expire obsolete manual snapshots |
| Aurora PostgreSQL | Instance/ACU, storage, I/O, replicas, backup | Deferred | Adopt only after workload-specific RDS versus Aurora cost/performance/failover test, not for nominal scale |
| RDS Proxy/read replicas | Proxy capacity or replica-hours and data transfer | Deferred | Fix pool budgets, churn, queries, indexes, and aggregates first; add only for measured bottleneck |
| ElastiCache | Node-hours, replicas, data transfer, reserved capacity | Omitted until a justified cache/rate-limit need | Cache only expensive proven reads; TTL and hit-rate metrics; right-size; remove low-value keys; reserve only a stable production footprint |
| S3 | Stored bytes/versions, requests, retrieval, data transfer, KMS calls, logs | Private per-environment application storage | Abort multipart uploads; expire exports and obsolete versions per retention; choose storage class from access evidence; avoid per-object high-cost logging unless risk requires it |
| SQS | API requests, payload chunks, KMS calls, data transfer | Standard queues and DLQs | Long polling, bounded batching, small event references instead of large payloads, retention matched to replay; never sacrifice idempotency to reduce requests |
| ECR | Stored layers, scans, cross-account/Region transfer | Immutable per-target account repositories | Layer reuse, multi-stage images, lifecycle unreferenced images, retain all deployed/rollback digests; build once and promote digest |
| Observability | Log ingest/storage/query, metric series, trace volume, collector/backend compute, cross-AZ/NAT traffic | OTel with a selected proportional backend | Attribute allowlists, cardinality budgets, trace sampling, shorter nonprod retention, log level/retention policy, metric aggregation, exclude secrets and noisy health traffic |
| Backups and DR | Snapshot/object versions, vault storage, restore-test capacity, optional cross-region copies | PITR, S3 versions, state/image retention, scheduled restore tests | Policy-driven retention and deletion; remove orphan snapshots only through reviewed lifecycle; temporary restore environments with TTL; no untested warm standby |
| Cognito, KMS, Secrets Manager | MAU/API operations, keys, secret count/rotation | Environment-separated managed identity and secrets | Avoid secret-per-tenant/resource explosion; group only where least privilege permits; use AWS-managed keys in nonprod when acceptable; delete expired nonprod secrets through lifecycle |

## Environment Cost Posture

### Local

Use developer compute and containers. Do not require EKS, ALB, NAT, RDS, ElastiCache,
CloudFront, WAF, or paid managed observability for normal feature work. Local adapters
must preserve failure semantics so cost reduction does not weaken design validation.

### Dev

Prefer ephemeral or scheduled workloads with TTL, one replica, the smallest verified
database, short log/backup retention, no Redis, and no always-on edge stack unless it
is being tested. A shared non-production EKS cluster may amortize the control-plane
cost after Kubernetes work begins, but namespaces do not provide account/cluster blast
isolation. Shut down only resources documented as safely disposable; preserve shared
state required by active tests.

### Staging

Keep service types and contracts production-shaped while using smaller capacity,
shorter retention, lower telemetry volume, and one NAT during ordinary periods.
Temporarily scale to the production topology for load, RDS failover, AZ, restore, and
rollout tests, then scale down automatically after evidence is captured. A permanently
production-sized staging environment is not necessary; a staging environment that
never tests production failure modes is also not sufficient.

### Production

Preserve three-AZ EKS capacity, three NAT gateways, RDS Multi-AZ, edge protection,
backup/restore, audit, and the telemetry required by approved SLOs. Right-size from
headroom and failure capacity, not average utilization alone: after one AZ loss,
surviving capacity must still serve the essential workload. Purchase commitments only
for the stable baseline after observing seasonal/burst behavior.

## Cost Versus Reliability Decisions

| Decision | Lower-cost posture | Production posture | Change trigger |
| --- | --- | --- | --- |
| NAT | One shared NAT or endpoint-only nonprod | One per AZ with same-AZ route | Production availability target and external egress dependency |
| Database | Local/Single-AZ small PostgreSQL | RDS PostgreSQL Multi-AZ | Customer data and approved recovery/availability objectives |
| Redis | Absent | Still absent until measured; Multi-AZ if adopted | Proven cache/rate-limit need whose value exceeds node and failure cost |
| EKS | No local cluster; scheduled/shared dev | Dedicated production cluster and zonal capacity | Platform phase and operational ownership readiness |
| Edge | Direct local/dev route | CloudFront + WAF + ALB | Public customer traffic and abuse/TLS/caching requirements |
| Endpoints | S3 gateway; NAT for quiet services | Selective interface endpoints | NAT-byte break-even, private-path requirement, or NAT failure reduction |
| Observability | Local/short retention | SLO-supporting metrics, logs, traces, alerts | Incident detection/diagnosis requirement; cardinality and retention budgets remain bounded |
| DR | Fixtures and disposable restores | PITR, versioning, protected artifacts, quarterly exercises | Customer recovery objective; regional copy only through a new risk/residency decision |

Reliability choices are not hidden as “optimization opportunities.” Removing a
production NAT gateway, standby, replica headroom, backup, security log, or restore
exercise changes an accepted risk and requires architecture/operational review.

## EKS And Workload Efficiency

Set realistic requests and limits from profiling; requests determine scheduling and
therefore node cost. Track requested versus used CPU/memory by workload, unschedulable
pods, node fragmentation, and headroom under one-AZ loss. Overstated requests waste
nodes; understated memory causes eviction/OOM risk and false savings.

Use separate scaling signals: Web/API latency, saturation, and request rate; worker
queue age/depth and processing time; node provisioning from pending-pod requirements.
Karpenter or managed-node autoscaling is selected by the platform design after testing
zonal balance and disruption. Spot is appropriate for idempotent interruption-tolerant
workers with on-demand fallback, not for the entire minimum API capacity or a stateful
database substitute.

One ALB can route Web and API, and one reversible worker binary can host several quiet
handler classes in V1 when their IAM, dependencies, failure modes, and scaling are
compatible. Split them when isolation evidence appears; do not manufacture deployments
to increase technology count.

## Data Transfer And Observability Controls

Cost reviews must include flows, not only service inventory:

- ECR image pulls use ECR endpoints plus the S3 gateway when the endpoint set is
  economical.
- S3 application traffic uses the gateway endpoint from VPC workloads; browser
  presigned transfers use the public S3 endpoint and its normal transfer/request model.
- Same-AZ NAT routing avoids accidental cross-AZ processing. ALB and multi-AZ database
  traffic still have legitimate cross-zone behavior that must be measured.
- Large event payloads remain in S3/PostgreSQL with bounded references in SQS when the
  contract permits; never put sensitive presigned URLs into telemetry.
- Logs have retention tiers, request bodies are excluded, health/access noise is
  sampled or aggregated, high-cardinality organization/user/resource IDs do not become
  metric labels, and traces use tail/head sampling appropriate to the backend.

## Unit Economics And Capacity Review

Measure at least:

- monthly platform fixed cost per environment;
- cost per active organization and active user;
- compute time and database work per API request class;
- database connections, storage, I/O, and backup growth per active organization;
- stored and transferred object bytes per organization;
- SQS requests and worker seconds per invoice PDF, notification, and report export;
- observability ingest/retention per service and environment; and
- cost of required one-AZ-loss headroom and restore exercises.

Tenant-level application metrics must be aggregated or joined in a controlled cost
model without exposing tenant identity in AWS billing exports or high-cardinality
telemetry. Finance/product policy defines whether unusually heavy tenants require
limits or plan changes; infrastructure must not silently degrade their correctness.

Review forecast versus actual monthly and before every material topology change.
Quarterly, inspect idle resources, ECR images, snapshots, S3 noncurrent versions,
CloudWatch/telemetry retention, NAT flows, endpoint utilization, RDS headroom, cache
hit rate, ALB count, public IPv4, and commitment coverage. Each optimization records
expected savings, reliability/security impact, rollback, owner, and validation date.

## Deferred Cost Decisions

Do not decide instance families, exact node/database sizes, purchase commitments,
Aurora, ElastiCache, RDS Proxy, read replicas, a centralized egress firewall, managed
versus self-hosted observability, or cross-region backup from architecture diagrams
alone. Decide them from representative staging load, current regional pricing, approved
SLO/RPO/RTO, and operational ownership. The default while evidence is absent is the
smallest reversible posture that preserves the documented environment's purpose.
