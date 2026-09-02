# Architecture Decision Records

## Purpose

These ADRs record proposed hard-to-reverse choices for ClouDesk. They are design decisions, not evidence that technology has been deployed. A future implementation changes an ADR to `Accepted` only after the decision is deliberately adopted.

| ADR | Decision | Status |
| --- | --- | --- |
| [ADR-001](ADR-001-go-backend.md) | Go backend | Proposed |
| [ADR-002](ADR-002-nextjs-typescript-frontend.md) | Next.js and TypeScript frontend | Proposed |
| [ADR-003](ADR-003-postgresql-system-of-record.md) | PostgreSQL system of record | Proposed |
| [ADR-004](ADR-004-modular-monolith-and-workers.md) | Modular monolith and workers | Proposed |
| [ADR-005](ADR-005-sqlc-and-pgx.md) | sqlc and pgx | Proposed |
| [ADR-006](ADR-006-openapi-contract.md) | OpenAPI contract | Proposed |
| [ADR-007](ADR-007-amazon-sqs-messaging.md) | Amazon SQS messaging | Proposed |
| [ADR-008](ADR-008-transactional-outbox-and-inbox.md) | Transactional outbox and inbox | Proposed |
| [ADR-009](ADR-009-idempotency-keys.md) | Idempotency keys | Proposed |
| [ADR-010](ADR-010-multi-tenant-isolation.md) | Multi-tenant isolation | Proposed |
| [ADR-011](ADR-011-amazon-cognito-oidc.md) | Amazon Cognito OIDC | Proposed |
| [ADR-012](ADR-012-bounded-redis-usage.md) | Bounded Redis usage | Proposed |
| [ADR-013](ADR-013-aws-single-region-multi-az.md) | AWS single-region Multi-AZ | Proposed |
| [ADR-014](ADR-014-eks-production-platform.md) | EKS production platform | Proposed |
| [ADR-015](ADR-015-terraform-iac.md) | Terraform infrastructure as code | Proposed |
| [ADR-016](ADR-016-gitops-delivery-model.md) | GitOps delivery model | Proposed |
| [ADR-017](ADR-017-argo-cd-controller.md) | Argo CD controller | Proposed |
| [ADR-018](ADR-018-opentelemetry-observability.md) | OpenTelemetry observability | Proposed |
| [ADR-019](ADR-019-rolling-deployments.md) | Rolling deployments | Proposed |
| [ADR-020](ADR-020-expand-contract-migrations.md) | Expand-and-contract migrations | Proposed |

## Lifecycle

Use `Proposed`, `Accepted`, `Superseded`, or `Rejected`. Superseding an ADR requires a new record and reciprocal links; do not rewrite historical context silently.
