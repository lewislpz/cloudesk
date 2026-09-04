# Repository Assessment

## Purpose

This document records the evidence inspected before designing ClouDesk and separates existing repository reality from the proposed target.

## Inspected Evidence

- Root [agent instructions](../AGENTS.md).
- `.codex/MANUAL.md`, `.codex/config.json`, mandatory rules, `/think` prompt/workflow, templates, validators, and relevant local skills.
- Full repository file inventory, documentation candidates, package/configuration markers, source/test directories, CI, Docker, Terraform, and Kubernetes candidates.
- Git discovery and resumable workspace inventory.

## Initial And Current State

At the architecture investigation boundary, the directory contained only the
reusable `.codex/` control plane, root `AGENTS.md`, and `.gitignore`; it had no product
documentation, application artifacts, or Git repository. That historical observation
explains why the architecture was treated as greenfield rather than inferred from
code.

The repository is now initialized on Git. M0 Tasks 1 and 2 have added the root
contributor README, exact Go/Node/pnpm toolchain declarations, package manifests and
lockfiles, strict frontend quality configuration, stable root commands, an
empty-secret `.env.example`, the canonical OpenAPI 3.1 contract, and generated Go and
TypeScript transport boundaries. This is engineering foundation, not a product
feature or deployed runtime.

The following requested technologies and capabilities are therefore **not implemented**:

- Runnable Go backend processes, hand-written module boundaries, migrations, and
  behavioral handler tests.
- Next.js application shell, routes/components, and generated-client runtime wiring.
- PostgreSQL, Redis, object storage, messaging, and worker processes.
- Docker/Compose, AWS, Terraform, EKS/Kubernetes, Helm, Argo CD, or CI/CD.
- Authentication, tenant isolation, RBAC, domains, telemetry, backups, or runbooks.

## Conflicts And Resolutions

| Observation | Conflict or risk | Resolution in this design |
| --- | --- | --- |
| The specification names a broad production stack but no product exists. | Readers could mistake design for implementation. | Every document uses proposed/current/production-target/future labels; readiness requires executable evidence. |
| EKS is mandated as a target for a small initial product. | Fixed cost and operational complexity can overwhelm V1. | Docker Compose is local; EKS begins in M13 after measured application and AWS foundations; ECS remains a cost alternative if the portfolio requirement changes. |
| Event-driven capabilities are requested before core domains exist. | Premature distributed infrastructure. | Domain ports and atomic outbox writes appear incrementally; SQS infrastructure and full worker framework arrive in M10. |
| Redis is listed in the conceptual topology. | It may be treated as mandatory or authoritative. | Redis is optional, non-authoritative, and introduced only for measured caching/rate-limiting needs. |
| No Git repository existed at investigation time. | CI, PR, GitOps, immutable revision binding, and release history could not exist. | The user initialized Git after the design phase. CI and delivery automation remain later M0 work. |
| No stack conventions existed beyond `.codex/`. | Stack conventions could not be inferred from code. | ADRs record the greenfield decisions; M0 Task 1 now establishes the first executable toolchain, manifest, command, and environment conventions. |

## Documentation Authority

The documents under `docs/` are the proposed architecture source of truth. Once product code exists, code/configuration and executable contracts can contradict stale prose; each milestone must update and verify documentation. ADR status remains `Proposed` until implementation deliberately accepts the decision.
