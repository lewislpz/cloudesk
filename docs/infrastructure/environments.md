# ClouDesk Environments

## Purpose And Status

This document defines the proposed local, dev, staging, and production environments
and makes their differences deliberate. It prevents the AWS/EKS production target from
turning every developer environment into a production-cost copy. No environment is
currently implemented.

See [AWS target architecture](aws.md), [networking](networking.md), and
[cost management](cost-management.md).

## Environment Principles

- Promote the same source revision, OpenAPI/event/database contracts, container image
  digest, Helm chart, and Terraform module versions; vary configuration and capacity,
  not application behavior.
- Production and non-production use separate AWS accounts. Dev and staging may share
  the non-production account but never VPCs, state, identities, keys, databases,
  buckets, queues, or secrets.
- Production data and credentials never enter local, dev, or staging. Use synthetic,
  deterministic fixtures with multiple tenants and adversarial tenant-isolation cases.
- Availability, retention, telemetry, and scale are proportional to purpose. Every
  known environment difference has an owner and a test or explicit accepted risk.
- Local application delivery precedes EKS. EKS is staged after the application and
  operational contracts are mature enough to justify it.

## Proportionality Matrix

| Capability | Local | Dev | Staging | Production |
| --- | --- | --- | --- | --- |
| Primary purpose | Fast feature work and integration tests | Shared integration/preview and AWS adapter validation | Release, migration, failover, and production-shape validation | Customer workload |
| Account | None | Non-production | Non-production; dedicated account when risk requires | Dedicated production |
| Runtime | Processes/Docker Compose | Ephemeral or scheduled cost-reduced cloud runtime; EKS only after platform phase | Dedicated EKS environment using production chart/controllers | Dedicated EKS cluster across three AZs |
| Web/API replicas | One each as needed | One by default, limited surge | At least two for rollout/readiness testing; temporary production-like count for resilience tests | At least two critical replicas with capacity to survive one AZ, tuned by evidence |
| Workers | Only feature-required workers | One per active class or combined reversible worker | Separate classes and realistic queue/DLQ behavior | Separate least-privilege classes, bounded concurrency, queue-based scaling |
| PostgreSQL | Containerized PostgreSQL with production major version | Small Single-AZ RDS or disposable PostgreSQL until AWS DB behavior is under test | RDS PostgreSQL Multi-AZ for migration/failover exercises; smaller class/data | RDS PostgreSQL Multi-AZ, deletion protection, PITR, monitored connection budget |
| Redis | Omitted unless the feature requires it | Omitted by default | Optional only to validate an adopted production use | Optional Multi-AZ ElastiCache only after measured need |
| Messaging | Before M10, a bounded local worker processes durable PostgreSQL deliveries; from M10, LocalStack/ElasticMQ may provide the SQS-compatible adapter. In-process fakes are test-only. | Environment-specific SQS queues/DLQs after M10; the durable PostgreSQL delivery path exists from M1 | Production-shaped SQS topology and replay runbook tests | SQS queues/DLQs, alarms, controlled replay |
| Object storage | S3-compatible local adapter or filesystem test adapter with equivalent metadata contract | Private environment S3 bucket | Private versioned bucket with production policy/lifecycle tests | Private versioned encrypted bucket with approved retention |
| Identity | OIDC-compatible local/test provider; fixed test identities | Separate Cognito test pool | Separate Cognito staging pool and callback domain | Separate production pool/domain and approved security policy |
| Edge | `localhost` TLS optional for ordinary work | ALB or ephemeral route; CloudFront/WAF only when edge behavior is under test | Route 53, CloudFront, WAF, ALB, and ACM matching production behavior | Route 53, CloudFront, WAF, ALB, and ACM |
| AZ/NAT posture | Not applicable | Lowest-cost explicit posture; may be single-AZ/one NAT | Three-AZ subnet shape; one NAT steady state may expand to three for zonal tests | Three AZs and one same-AZ NAT per application subnet |
| Backups | Disposable; fixture scripts are recovery source | Short retention, no customer recovery promise | PITR and scheduled restore exercises with synthetic data | Proposed 35-day PITR, versioned objects, protected recovery artifacts, quarterly restore exercises |
| Telemetry | Console/local collector, short retention | Minimal metrics/logs/traces with strict caps | Production schemas, dashboards, alerts, and representative retention at reduced volume | Approved SLI telemetry, alerting, redaction, sampling, and retention |
| Availability objective | None | Best effort | Exercise target behavior; no external SLO | Approved SLO target after measurement; never inferred from topology alone |

## Local

Local development should start with Next.js, the Go API, PostgreSQL, and only the
worker processes required by the feature under development. Docker Compose may run
PostgreSQL, an optional Redis-compatible service, an S3-compatible adapter, an
SQS-compatible adapter, email capture, and an OIDC test provider. Each adapter must
preserve the application-facing contract and failure tests; local convenience must
not invent stronger ordering or exactly-once delivery than AWS provides.

Provide seeded users in multiple organizations, identical IDs in different tenant
fixtures where useful, invalid cross-tenant objects, duplicate events, and idempotency
replays. Local secrets live in ignored developer-specific configuration or a documented
secret tool, never committed files. AWS credentials are not required for normal
feature development.

## Dev

Dev is cost-reduced and disposable. Before Phase 3 of the roadmap, local plus CI may
be the only development environment; a permanent EKS cluster is not a prerequisite.
When AWS adapter or shared integration validation becomes necessary, create dev in the
non-production account with its own state and VPC. Prefer scheduled or ephemeral
capacity, one small replica per workload, one NAT or endpoint-only networking, short
log/backup retention, no ElastiCache, and a Single-AZ database if managed failover is
not the test subject.

If dev uses a namespace on a shared non-production EKS cluster for cost reasons, the
namespace must have its own service accounts/Pod Identity associations and roles, network policies, quotas,
secrets, database, queues, and bucket. This saves the EKS control-plane charge but is
not blast-radius equivalent to a dedicated cluster. Staging release evidence cannot
come from a dev namespace.

Preview environments should default to application workloads and disposable schemas,
not a full VPC/EKS/RDS/CloudFront stack per pull request. Set a TTL and owner at
creation, and reap expired previews automatically after preserving useful test output.

## Staging

Staging exists to discover deployment and infrastructure failures that local/dev
cannot. It uses the production Helm chart, Kubernetes controllers, ingress paths,
Pod Identity association model, SQS/DLQ topology, S3 policies, Cognito flows, migration artifact, and
RDS major/parameter compatibility. It uses synthetic representative data and load,
never copied customer data.

The standing environment may use smaller nodes, a smaller RDS class, shorter retention,
sampled telemetry, and one NAT gateway. Those are capacity/cost differences, not
contract differences. Before production readiness or a material platform change,
staging temporarily uses the production three-AZ NAT/routing shape and adequate
capacity to exercise node loss, AZ loss, RDS failover, Redis degradation if adopted,
queue backlog, rolling deployment, migration compatibility, restore, and rollback.

Staging is not a manual sandbox. GitOps owns desired state, releases arrive through the
same promotion path, drift is detected, and test failures block production promotion.

## Production

Production is the only environment with customer data and an availability objective.
It runs in its own account and VPC, uses three application AZs, private EKS workloads,
the CloudFront/WAF/ALB ingress path, RDS PostgreSQL Multi-AZ, production SQS/DLQs,
private versioned S3, immutable ECR artifacts, environment-specific Cognito, Secrets
Manager, KMS, backups, alerts, and audit controls. Redis remains absent unless its
adoption trigger has been met.

Production does not accept ad hoc developer deployments or console configuration.
Emergency mutation uses a named, time-bounded, audited role, follows a runbook, and is
reconciled into Terraform or GitOps immediately afterward. Budgets may alert or stop
clearly disposable automation, but never shut down production resources automatically.

## Configuration, Data, And Secret Boundaries

Every environment has a unique application hostname, OIDC issuer/client, VPC CIDR,
Terraform state key, Kubernetes cluster/namespace, database endpoint and roles, S3
bucket, SQS queues/DLQs, ECR destination, KMS grants, Secrets Manager paths, telemetry
labels, and alert routing. Resource names include application and environment but
tenant identity belongs in tags/records only where privacy and cardinality policy allow
it; tenant IDs are not AWS resource names.

Configuration is schema-validated at startup. Environment variables or mounted secret
values carry runtime configuration, but source-controlled manifests refer only to
secret identifiers. Missing required production configuration fails startup safely.
Feature flags have owner, expiry, and environment rollout policy; they do not bypass
authorization or migration compatibility.

Production data does not flow downward. When realistic staging distributions are
needed, generate them or use an approved irreversibly anonymized dataset whose process
is separately reviewed. Database snapshots, S3 versions, queue payloads, Cognito users,
and observability exports remain inside their environment/account boundary.

## Artifact And Infrastructure Promotion

The promotion unit is immutable:

1. CI validates source, OpenAPI/events, migrations, Terraform, Helm, and security
   checks, then builds and scans one container image.
2. The image manifest/digest is copied or replicated to the target account's ECR and
   the digest is verified; it is not rebuilt per environment.
3. Dev receives the digest for integration evidence.
4. Staging receives the same digest and schema/migration artifact through GitOps.
5. Production promotion references the same digest after required evidence and human
   gates; environment configuration remains separate.

Terraform module versions follow the same ordered progression, but infrastructure
applies and application GitOps syncs remain separate authorities. Database migration
jobs use expand-and-contract sequencing and the same immutable migration artifact.
Production rollback normally restores the prior application digest while the expanded
schema remains compatible.

## Required Parity And Accepted Differences

The following contracts must be identical across dev/staging/production once the
relevant service exists: API/event schema, PostgreSQL major version, migration order,
SQS at-least-once assumptions, S3 authorization/lifecycle state machine, workload-identity association
shape, Helm templates, probes, labels, telemetry attributes, and secret names/interfaces.

Accepted differences are capacity, replica count, AZ resilience, retention, sampling,
backup period, WAF blocking maturity, and optional service presence. Every conditional
integration must be tested both absent and present: Redis-disabled mode is first-class;
optional telemetry export failure cannot make the application unavailable.

## Environment Readiness Evidence

- Local is ready when a new developer can start dependencies, load multi-tenant
  fixtures, and run application/integration tests without AWS credentials.
- Dev is ready when disposable deployment, adapter integration, teardown/TTL, quotas,
  and cost attribution are automated.
- Staging is ready when immutable promotion, ingress, Pod Identity, migrations, synthetic load,
  failure tests, and restore/rollback evidence match the documented contracts.
- Production is ready only after required security, tenant isolation, availability,
  backup/restore, observability, capacity, cost, runbook, and approval gates have
  current evidence. Similarity to staging alone is not proof.
