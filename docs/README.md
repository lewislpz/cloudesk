# ClouDesk Technical Documentation

## Purpose And Status

This documentation defines the proposed product, software, data, cloud, platform, delivery, security, reliability, and implementation architecture for ClouDesk. The repository currently contains no product implementation or infrastructure; see the [repository assessment](repository-assessment.md). Terms such as **production target**, **planned**, and **future evolution** are intentional.

## Start Here

1. [Product vision](product/vision.md)
2. [Requirements](product/requirements.md) and [glossary](product/glossary.md)
3. [Architecture overview](architecture/overview.md), [system context](architecture/system-context.md), and [containers](architecture/containers.md)
4. [Architecture decisions](decisions/README.md)
5. [Incremental plan](roadmap/implementation-plan.md), [milestones](roadmap/milestones.md), and [production readiness](roadmap/production-readiness.md)

## Software And Data Architecture

- [Go backend](architecture/backend.md)
- [Next.js frontend](architecture/frontend.md)
- [Multi-tenancy](architecture/multi-tenancy.md) and [security/threat model](architecture/security.md)
- [PostgreSQL data model and ERD](architecture/data-model.md)
- [Asynchronous processing](architecture/async-processing.md)
- [Resilience](architecture/resilience.md) and [scalability](architecture/scalability.md)
- [Mandatory architecture questions](architecture/operational-decisions.md)
- [Disaster recovery architecture](architecture/disaster-recovery.md)

## Domains

- [Identity](domains/identity.md), [organizations](domains/organizations.md), [memberships/RBAC](domains/memberships.md)
- [Clients](domains/clients.md), [projects](domains/projects.md), [tasks](domains/tasks.md), [comments](domains/comments.md)
- [Time tracking](domains/time-tracking.md), [invoicing](domains/invoicing.md), [files](domains/files.md)
- [Notifications](domains/notifications.md), [reporting/analytics](domains/reporting.md), [audit](domains/audit.md)

## API Contract

- [Overview](api/overview.md), [conventions](api/conventions.md), and [resources](api/resources.md)
- [Pagination](api/pagination.md), [errors](api/errors.md), and [idempotency](api/idempotency.md)
- [OpenAPI source and generation](api/openapi.md)

## Infrastructure And Environments

- [AWS target](infrastructure/aws.md), [networking](infrastructure/networking.md), and [environments](infrastructure/environments.md)
- [Kubernetes/EKS](infrastructure/kubernetes.md), [Terraform](infrastructure/terraform.md), and [cost management](infrastructure/cost-management.md)

## Operations

- [Observability](operations/observability.md), [logging](operations/logging.md), [metrics](operations/metrics.md), and [tracing](operations/tracing.md)
- [SLIs/SLOs](operations/sli-slo.md), [alerting](operations/alerting.md), and [scaling](operations/scaling.md)
- [Backups](operations/backups.md), [disaster recovery](operations/disaster-recovery.md), [runbooks](operations/runbooks.md), and [chaos testing](operations/chaos-testing.md)

## Delivery And Quality

- [Continuous integration](delivery/ci.md), [continuous delivery](delivery/cd.md), and [GitOps](delivery/gitops.md)
- [Database migrations](delivery/database-migrations.md) and [release strategy](delivery/release-strategy.md)
- [Testing strategy](testing/strategy.md), [backend](testing/backend.md), [frontend](testing/frontend.md), [integration](testing/integration.md), [E2E](testing/e2e.md), [performance](testing/performance.md), and [reliability](testing/reliability.md)

## Shared Invariants

- ClouDesk begins as a modular Go monolith with independent worker processes.
- PostgreSQL is the business source of truth; Redis never stores critical authoritative state.
- Every tenant-owned route, query, constraint, cache key, object, event, job, and idempotency record carries `organization_id`.
- OpenAPI 3.1 is the HTTP contract between Go and generated TypeScript code.
- Reliable asynchronous work uses a PostgreSQL transactional outbox, Amazon SQS, and idempotent inbox-aware consumers.
- Production targets one AWS region across Availability Zones; multi-region is deferred to explicit requirements.
- SLOs and RPO/RTO values are proposed objectives until measured and approved.

## Documentation Rules

Use relative links, Mermaid for maintainable diagrams, exact `ClouDesk` naming, and ADR references for consequential choices. Do not mark a proposal as implemented without repository and runtime evidence.
