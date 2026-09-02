# ClouDesk Requirements

## Purpose

This document defines the proposed product and engineering requirements used to judge architecture and future implementation.

## Functional Requirements

| Area | Required behavior |
| --- | --- |
| Identity | Sign in/out, session lifecycle, invitation acceptance, recovery, and organization selection through an OIDC provider. |
| Organizations | Create and configure a tenant; manage memberships and role-derived permissions. |
| Clients | Maintain tenant-owned client identities, contacts, billing details, status, and archive history. |
| Projects | Track client work, members, budget, billing model, status, dates, and archive lifecycle. |
| Tasks and comments | Assign, prioritize, discuss, mention, attach files, and retain activity history. |
| Time tracking | Start/stop at most one active timer per global `user_id` across all organizations, while retaining organization/membership ownership on the entry; add corrections, resolve billability/rates, and preserve audit history. |
| Invoicing | Build invoices from eligible time or manual lines; calculate immutable monetary snapshots; enforce issue/send/payment/void transitions; generate PDFs asynchronously. |
| Files | Authorize direct upload/download with short-lived presigned URLs while PostgreSQL owns metadata and lifecycle state. |
| Notifications | Deliver in-app and email notifications asynchronously with preferences and deduplication. |
| Reporting | Provide bounded operational aggregates first; precompute expensive views only when measured. |
| Audit | Append security and business-sensitive events with actor, tenant, resource, request, and trace context. |

## Non-Functional Requirements

- **Isolation:** every tenant-owned access path carries and verifies `organization_id`; negative cross-tenant tests are release gates.
- **Integrity:** PostgreSQL constraints and transactions protect durable invariants; external side effects never occur inside a database transaction.
- **Reliability:** retries are bounded and jittered, consumers are idempotent, concurrency is bounded, and failed messages have controlled replay.
- **Security:** OIDC, least privilege, encrypted transport/storage, safe logs, upload restrictions, abuse controls, and deny-by-default authorization.
- **Performance:** cursor pagination and tenant-aware indexes; explicit query and payload limits; measured scaling before partitioning or replicas.
- **Availability:** stateless APIs and workers; production target spans Availability Zones; optional dependencies degrade without corrupting truth.
- **Observability:** structured logs, RED/domain metrics, traces across asynchronous boundaries, SLO targets, and actionable runbooks.
- **Delivery:** immutable artifacts, validated OpenAPI, backward-compatible migrations, GitOps reconciliation, and rollback-aware releases.
- **Quality:** unit, integration, contract, E2E, performance, resilience, security, restore, and accessibility verification proportional to risk.

## Stage Classification

| Classification | Meaning |
| --- | --- |
| Current requirement | A documented invariant that all later implementation must preserve. |
| V1 implementation | The smallest local product slice that proves user value. |
| Production target | Capabilities required before serving production workloads on AWS. |
| Future evolution | Deferred until a recorded scale, reliability, compliance, or ownership trigger is observed. |

## Explicit Non-Goals For V1

Payment processing, multi-region active/active, Kafka, a service mesh, a data warehouse, universal event sourcing, and microservice decomposition are not V1 requirements.

## Acceptance Model

Milestone acceptance criteria are authoritative in the [implementation roadmap](../roadmap/implementation-plan.md). Production claims require the [production-readiness checklist](../roadmap/production-readiness.md), not documentation alone.
