# ClouDesk Milestones

## Purpose

These proposed milestones make ClouDesk incremental and interview-ready without treating production complexity as day-one scope. Each milestone ends with an observable vertical outcome.

## M0 — Repository Foundation

- **Objective:** establish a reproducible local engineering base.
- **Scope:** monorepo layout, Go/Next.js conventions, OpenAPI location, local Compose, migrations, lint/type/test commands, base CI, documentation ownership.
- **Backend:** API and worker entry-point skeletons, configuration, health contract, module dependency checks.
- **Frontend:** App Router shell, generated-client boundary, accessibility/design tokens, test harness.
- **Database:** PostgreSQL container, migration/sqlc tooling, empty baseline schema and reset workflow.
- **Infrastructure:** Dockerfiles and Compose only; no AWS/EKS resources.
- **Tests:** smoke startup, formatting, lint, typecheck, unit harness, OpenAPI lint, migration up/down on disposable data.
- **Acceptance:** one documented command starts dependencies and apps; CI repeats all checks; no production claims.
- **Dependencies:** approved architecture documentation.
- **Risks:** over-scaffolding and premature abstractions; require a thin, runnable base.
- **Definition of done:** commands are reproducible on a clean machine, secrets are examples only, and contributor docs match actual paths.

## M1 — Identity And Organizations

- **Objective:** prove secure tenant selection and membership authorization end to end.
- **Scope:** OIDC/session adapter, users, organizations, memberships, invitations, fixed versioned role-permission policy, tenant-aware repository contract, and the minimal durable audit/idempotency/outbox tables used from this milestone onward.
- **Backend:** OIDC callback and opaque-session lifecycle, principal mapping, organization-prefixed routes, permission middleware/use-case checks, invitation flow, synchronous required audit writes, HTTP idempotency, and a PostgreSQL delivery poller behind the future broker port.
- **Frontend:** login/callback, onboarding, organization switcher, team list, capability-aware navigation.
- **Database:** users/external identities/sessions, organizations, memberships with fixed role code, invitations, `audit_events`, `security_audit_events`, `idempotency_keys`, immutable `outbox_events`, per-destination `outbox_deliveries`, tenant constraints, and selective RLS proof.
- **Infrastructure:** local OIDC provider and mail sink; production Cognito/SQS Terraform remains later. Before SQS, a bounded local worker polls durable PostgreSQL deliveries: process loss delays work but does not lose committed intent; it is not a production throughput/availability claim.
- **Tests:** positive/negative auth/session/CSRF, expired/stolen-context cases, cross-tenant IDs, role matrix, RLS pool-context reset, required-audit atomicity, idempotent invitation replay, and local dispatcher restart recovery.
- **Acceptance:** one user can join multiple organizations but cannot read or mutate another organization's resource without membership/permission.
- **Dependencies:** M0.
- **Risks:** IDOR, confused-deputy tenant selection, invitation takeover, token leakage.
- **Definition of done:** threat-model cases pass, required audit/outbox/idempotency facts commit atomically, local async intent survives process restart, security logs are secret-safe, and permissions are documented in OpenAPI.

## M2 — Clients

- **Objective:** manage tenant-owned client and billing identities.
- **Scope:** create/read/update/archive clients, contacts, address/tax fields, cursor list.
- **Backend:** explicit commands/queries and client permissions.
- **Frontend:** client list/detail/edit with loading, empty, error, and archive recovery states.
- **Database:** clients/contacts, tenant-aware indexes and archive constraints.
- **Infrastructure:** none beyond local stack.
- **Tests:** repository/HTTP integration, authorization matrix, pagination stability, sensitive-field logging.
- **Acceptance:** organization members see only permitted clients; archived clients remain historical and reject new work.
- **Dependencies:** M1.
- **Risks:** PII exposure and accidental hard deletion.
- **Definition of done:** API/client contract generated, accessibility checked, audit events recorded for sensitive mutations.

## M3 — Projects

- **Objective:** model controlled client delivery and project participation.
- **Scope:** projects, lifecycle, project members, billing model, budget/rate settings, tags.
- **Backend:** project state machine and membership/permission checks.
- **Frontend:** project list/detail/settings and member management.
- **Database:** projects/project_members, tenant-aware composite FKs, version column, lifecycle checks.
- **Infrastructure:** none.
- **Tests:** state transitions, optimistic conflict, cross-client/tenant FK rejection, list filters.
- **Acceptance:** active projects can be managed by authorized members; completed/archived rules hold under concurrent requests.
- **Dependencies:** M2.
- **Risks:** project access diverging from organization policy.
- **Definition of done:** project authorization rules and audit history are observable and contract-tested.

## M4 — Tasks And Collaboration

- **Objective:** execute and discuss project work.
- **Scope:** tasks, assignees, labels, comments, mentions, activity; project-level comments deferred.
- **Backend:** task transitions, assignment invariants, comment sanitization, mention event intent.
- **Frontend:** task lists/detail, filters, accessible forms, limited optimistic assignment/labels.
- **Database:** tasks, assignees, labels, comments, activity indexes and versions.
- **Infrastructure:** optional local email sink only.
- **Tests:** state/permission matrix, XSS content, stale updates, mention deduplication, keyboard/screen-reader E2E.
- **Acceptance:** users collaborate within project/tenant boundaries with correct rollback on conflict.
- **Dependencies:** M3.
- **Risks:** stored XSS, notification noise, unbounded task lists.
- **Definition of done:** all interaction states are present and activity is traceable.

## M5 — Time Tracking

- **Objective:** reliably capture billable and non-billable work.
- **Scope:** start/stop timer, manual entry, correction, rate resolution, bounded reports.
- **Backend:** idempotent commands, one-active-timer invariant, transactional concurrency, audit correction.
- **Frontend:** persistent timer control, manual editor, conflict/retry feedback, timezone-aware display.
- **Database:** time_entries, partial unique active-timer index, version/audit linkage and reporting indexes.
- **Infrastructure:** none.
- **Tests:** simultaneous start/stop, retry replay, DST/timezone display, invalid durations, invoiced-entry immutability.
- **Acceptance:** concurrent requests never create two active timers or duplicate stopped entries.
- **Dependencies:** M4.
- **Risks:** clock mistakes, race conditions, billing disputes.
- **Definition of done:** invariants are database-enforced, integration-tested, and visible in audit history.

## M6 — Invoicing

- **Objective:** issue trustworthy invoices from time and manual lines.
- **Scope:** drafts, immutable snapshots, totals/taxes/discounts, numbering, state machine, PDF port.
- **Backend:** calculation domain, issue transaction/outbox intent, payment-state recording without payment provider.
- **Frontend:** invoice list/editor/detail, conflict handling, review-before-issue, print/PDF status.
- **Database:** invoices/lines, tenant numbering, time linkage, constraints, versions, minor-unit/decimal precision.
- **Infrastructure:** local stub/object service for PDF output only.
- **Tests:** property/table calculation tests, state transitions, concurrent issue, rounding, currency, idempotency, immutable issued data.
- **Acceptance:** one valid issue request produces one numbered immutable invoice and durable PDF intent.
- **Dependencies:** M5.
- **Risks:** financial rounding, duplicate numbers, silent edit after issue.
- **Definition of done:** calculations are independently reviewed and every sensitive transition is audited.

## M7 — Files

- **Objective:** safely attach tenant-owned objects without proxying bytes through the API.
- **Scope:** metadata, presigned upload/download, completion verification, lifecycle/delete, scan port.
- **Backend:** authorization and constrained presign commands, reconciliation job.
- **Frontend:** upload progress/error/retry, safe download and quarantine states.
- **Database:** files with lifecycle/checksum/owner/resource metadata.
- **Infrastructure:** local S3-compatible service; AWS S3 configuration later.
- **Tests:** cross-tenant object access, expired/reused URL, size/type/checksum mismatch, orphan cleanup.
- **Acceptance:** unauthorized users cannot obtain usable URLs and failed uploads leave no permanent orphan state.
- **Dependencies:** M4; invoice PDF integration follows M6.
- **Risks:** malicious content and leaked bearer URLs.
- **Definition of done:** lifecycle, retention, scan policy, and safe content disposition are enforced and tested.

## M8 — Notifications

- **Objective:** deliver in-app and email notifications without coupling domain transactions to providers.
- **Scope:** preferences, templates, in-app inbox, email port, retry/status.
- **Backend:** intent policy, recipient resolution, deduplication, provider adapter.
- **Frontend:** notification center and preference controls.
- **Database:** notifications, preferences, delivery attempts.
- **Infrastructure:** local mail sink; production provider selected later.
- **Tests:** deduplication, preference/security overrides, permanent/retryable failure, template safety.
- **Acceptance:** domain actions succeed when email is unavailable and pending/failure state is visible.
- **Dependencies:** M4 and M6 plus the M1 durable PostgreSQL delivery foundation; SQS/inbox/DLQ runtime arrives in M10.
- **Risks:** spam, sensitive payloads, provider coupling.
- **Definition of done:** delivery is idempotent, observable, and manually replayable under policy.

## M9 — Audit Governance And Product Access

- **Objective:** mature the audit foundation already written synchronously since M1 into an operable product/governance capability.
- **Scope:** required-event coverage audit, authorized query/export, retention/governance, external/provider fact projection, and policy ownership.
- **Backend:** preserve transactional business writes; add bounded queries/export and inbox-aware ingestion only for separately durable external facts.
- **Frontend:** authorized audit viewer with filters and redaction.
- **Database:** harden existing append-only audit tables, tenant/time indexes, source-event dedupe, retention jobs, and export support.
- **Infrastructure:** log/archive export remains future.
- **Tests:** required-event coverage, mutation prevention, redaction, tenant isolation.
- **Acceptance:** named sensitive actions create queryable correlated events without secrets.
- **Dependencies:** M1 audit schema/write path, integrated incrementally with M2-M8.
- **Risks:** logging secrets, unbounded volume, false assurance from best-effort records.
- **Definition of done:** retention and access policy are documented and mandatory audit writes share the business transaction.

## M10 — Distributed Processing Foundation

- **Objective:** make asynchronous work durable and operable.
- **Scope:** outbox publisher, SQS adapter, inbox/deduplication, retry/DLQ/replay, bounded worker framework, health/shutdown.
- **Backend:** worker runtime and workload-specific handlers; no generic distributed framework beyond proven common behavior.
- **Frontend:** async operation status/polling and actionable failure UI.
- **Database:** harden the existing `outbox_events` + `outbox_deliveries` foundation, then add `processed_events`, runtime claim/cleanup indexes, and replay retention; HTTP `idempotency_keys` already exist for earlier commands.
- **Infrastructure:** production SQS queues/DLQs plus a compatible local broker adapter; replace the limited direct PostgreSQL poller without changing source transactions.
- **Tests:** commit/publish crash windows, duplicates, poison messages, visibility expiry, worker death, backlog, graceful termination.
- **Acceptance:** no committed event is lost; duplicate delivery causes one durable effect; controlled replay is documented.
- **Dependencies:** M6-M9 event producers.
- **Risks:** duplicate external side effects, ordering assumptions, unbounded retries.
- **Definition of done:** queue/runbook metrics and failure injection prove semantics.

## M11 — Observability

- **Objective:** correlate user journeys and asynchronous work and establish useful service signals.
- **Scope:** OTel, structured logs, RED/domain metrics, traces, dashboards, proposed SLOs/alerts.
- **Backend:** HTTP/DB/outbox/SQS/worker instrumentation and safe attributes.
- **Frontend:** web vitals, route/error traces with privacy controls.
- **Database:** query/pool/outbox metrics; no high-cardinality labels.
- **Infrastructure:** local collector plus backend evaluation; production destinations chosen by cost/operations.
- **Tests:** propagation, attribute redaction, collector outage, alert rule evaluation.
- **Acceptance:** one request can be followed to worker outcome and failures are actionable without sensitive data.
- **Dependencies:** M10.
- **Risks:** telemetry cost/cardinality and secret leakage.
- **Definition of done:** dashboards/runbooks have owners and SLOs are labeled targets, not guarantees.

## M12 — AWS Foundation

- **Objective:** provision secure, cost-aware shared AWS primitives through Terraform.
- **Scope:** accounts/environments, VPC, endpoints/NAT policy, RDS, S3, ECR, SQS, IAM, secrets, certificates, backups; Redis only if justified.
- **Backend:** configure managed endpoints/identity through environment contracts.
- **Frontend:** artifact/config integration; no runtime AWS credentials.
- **Database:** RDS encryption, Multi-AZ production, PITR, parameter/monitoring baseline.
- **Infrastructure:** versioned Terraform state/modules, GitHub OIDC plans/applies, tagging and budgets.
- **Tests:** fmt/validate/lint/policy/security, disposable environment tests, restore exercise plan.
- **Acceptance:** dev resources can be recreated without console drift; production plan shows least privilege and HA differences.
- **Dependencies:** M11 and approved cost model.
- **Risks:** IAM exposure, NAT/EKS/RDS cost, state loss.
- **Definition of done:** state recovery, backup ownership, drift detection, and teardown protections are documented/tested.

## M13 — Kubernetes And EKS

- **Objective:** run API/workers safely across zones with workload identity and bounded resources.
- **Scope:** EKS, namespaces, Helm, deployments/services/ingress, probes, HPA, PDB, topology, Karpenter evaluation.
- **Backend:** readiness/liveness/startup and termination behavior validated.
- **Frontend:** Next.js workload/service and CDN/ALB routing validated.
- **Database:** connection budgets per replica and failover recovery tests.
- **Infrastructure:** node pools, EKS Pod Identity/workload roles, ALB controller, policies, autoscaling.
- **Tests:** Helm/schema/policy validation, rolling update, pod/node/AZ disruption, load-driven scaling.
- **Acceptance:** pod/node loss removes traffic without corrupting work; critical workloads span zones.
- **Dependencies:** M12.
- **Risks:** cluster complexity, capacity deadlock from PDB, connection storms.
- **Definition of done:** runbooks, requests/limits, quotas, upgrade policy, and cost telemetry exist.

## M14 — GitOps And Continuous Delivery

- **Objective:** promote immutable artifacts through environments with auditable reconciliation.
- **Scope:** GitHub Actions, digest-pinned images, ECR scanning/signing, Helm values, Argo CD, migration jobs, rollback.
- **Backend:** compatibility/release metadata and migration preconditions.
- **Frontend:** immutable build and environment-safe runtime configuration.
- **Database:** expand/contract sequencing and migration lock/timeout safeguards.
- **Infrastructure:** Argo projects/RBAC, environment promotion PRs, no static AWS credentials.
- **Tests:** supply-chain, policy, integration, deployment smoke, rollback and drift recovery.
- **Acceptance:** one reviewed change builds once and promotes the same digest to staging; failure stops or rolls back safely.
- **Dependencies:** M13.
- **Risks:** privileged CI/controller, migration rollback mismatch, Git desired-state drift.
- **Definition of done:** deployment evidence is linked to commit/digest/config and emergency procedure reconciles back to Git.

## M15 — Reliability Hardening

- **Objective:** prove production hypotheses and close readiness gaps.
- **Scope:** k6 load/soak, error budgets, backlog tests, chaos, RDS failover, restore, regional recovery tabletop, optional canary.
- **Backend:** profile and remove measured bottlenecks; tune retry/concurrency/pools.
- **Frontend:** performance budgets and degraded-state UX under latency/failure.
- **Database:** query/index review, pool limits, failover and PITR restoration validation.
- **Infrastructure:** disruption, capacity, backup/restore, alert, DR, and rollback exercises.
- **Tests:** all production-readiness scenarios with hypotheses, expected impact/recovery, metrics, data-loss, and alert expectations.
- **Acceptance:** agreed SLO targets and RPO/RTO are supported by measured evidence and owned runbooks.
- **Dependencies:** M14 and representative traffic/data.
- **Risks:** tests causing shared-environment impact and false confidence from synthetic load.
- **Definition of done:** unresolved gaps have owners/deadlines; go-live approval references current evidence, not checklist assertion.
