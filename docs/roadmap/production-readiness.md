# ClouDesk Production Readiness Checklist

## Purpose

This checklist distinguishes required staging/production evidence from recommendations and future evolution. Checking a box requires a link to current executable or observed evidence; documentation alone is insufficient.

Legend: **Staging**, **Production**, **Recommended**, **Future**.

## Backend And API

- [ ] **Staging:** API and workers build reproducibly and shut down gracefully under SIGTERM.
- [ ] **Staging:** OpenAPI lint, generated-client drift, compatibility, validation, error-envelope, pagination, and idempotency tests pass.
- [ ] **Production:** Explicit dependency timeouts, bounded retries/concurrency, connection budgets, and overload behavior are load-tested.
- [ ] **Recommended:** CPU/memory profiles exist for representative workloads.

## Frontend

- [ ] **Staging:** Typecheck, lint, component/integration tests, and critical Playwright journeys pass.
- [ ] **Staging:** Loading, empty, error, offline/retry, forbidden, conflict, and destructive states are verified responsively.
- [ ] **Production:** WCAG 2.2 AA checks and manual keyboard/screen-reader review cover critical flows.
- [ ] **Recommended:** Web-vitals budgets and production source-map/privacy policy are verified.

## Authentication And Authorization

- [ ] **Staging:** OIDC issuer/audience/signature/time validation and secure session/cookie settings pass negative tests.
- [ ] **Production:** Recovery, invitation, session revocation/expiry, brute-force, credential-stuffing, and compromised-user runbooks are exercised.
- [ ] **Production:** Every protected operation has deny-by-default role/permission tests.
- [ ] **Future:** MFA enforcement is enabled according to role/risk policy.

## Multi-Tenancy

- [ ] **Staging:** Cross-tenant IDs, lists, cache keys, jobs, events, idempotency keys, object keys, and exports pass negative isolation tests.
- [ ] **Production:** Repository query lint/review and selective RLS integration tests prove pool context is set/reset safely.
- [ ] **Production:** Tenant identifiers never act as authorization by themselves and enumeration responses are safe.

## Database And Migrations

- [ ] **Staging:** Constraints, representative indexes, transaction races, deadlocks/timeouts, cursor stability, and rollback/roll-forward paths are tested.
- [ ] **Production:** RDS Multi-AZ, encryption, PITR retention, monitoring, parameter groups, maintenance windows, and connection alarms are configured.
- [ ] **Production:** Expand-and-contract migrations run against production-scale test data with throttled, resumable backfills.
- [ ] **Recommended:** Slow-query review uses `EXPLAIN (ANALYZE, BUFFERS)` on sanitized representative data; vacuum/bloat alerts have owners.

## Redis

- [ ] **Staging:** Every Redis use has TTL, tenant-key scheme, bounded timeout, cardinality limit, and authoritative fallback.
- [ ] **Production:** Redis outage behavior is load-tested; sensitive rate limits fail closed/conservatively while caches degrade to bounded DB reads.
- [ ] **Future:** Introduce ElastiCache only after a measured caching or distributed-limit requirement.

## Messaging And Idempotency

- [ ] **Staging:** Outbox crash windows, duplicate delivery, unordered delivery, visibility expiry, poison messages, DLQ, and controlled replay are tested.
- [ ] **Production:** Queue age/depth, outbox lag, worker failures, DLQ messages, and replay actions have alerts/runbooks.
- [ ] **Production:** External side effects use provider keys or durable sent-state to prevent duplicate email/files/actions.
- [ ] **Recommended:** Event schema compatibility and retention/cleanup jobs are load-tested.

## S3 And Files

- [ ] **Staging:** Presigned upload/download authorization, expiry, size/type/checksum, safe disposition, orphan reconciliation, and deletion semantics pass.
- [ ] **Production:** Buckets are private, encrypted, versioned/lifecycle-managed as required, public access is blocked, and workload IAM is least privilege.
- [ ] **Production:** Malware/quarantine policy is implemented for accepted risky types or those types are explicitly rejected.

## Security And Secrets

- [ ] **Staging:** Threat model, SAST, dependency/container/IaC scan, secret scan, security headers, CORS/CSRF/XSS/SQLi/IDOR tests are current.
- [ ] **Production:** WAF/abuse controls, TLS/certificate renewal, KMS policies, vulnerability SLA, and incident contacts are exercised.
- [ ] **Production:** Secrets Manager rotation/access logging and log/trace redaction are verified; no static AWS credentials exist.
- [ ] **Recommended:** Independent penetration test or focused tenant-isolation review is completed.

## IAM And Networking

- [ ] **Staging:** GitHub OIDC and pod workload identities have resource/action-scoped policies and no wildcard administrative grants.
- [ ] **Production:** Workloads/data stores reside in private subnets; ingress, egress, endpoints, NAT, routes, security groups, DNS, and network logs are reviewed.
- [ ] **Production:** Account/environment boundaries, break-glass access, CloudTrail/security monitoring, and budget alerts are enabled.

## Kubernetes And Scaling

- [ ] **Staging:** Requests/limits, readiness/liveness/startup probes, termination grace, rolling strategy, HPA, PDB, topology spread, and disruption tests pass.
- [ ] **Production:** Critical replicas span nodes/AZs; node loss and one-AZ capacity loss preserve agreed service behavior.
- [ ] **Production:** API and worker autoscaling signals, maximums, queue drain time, and database connection budgets are load-tested.
- [ ] **Recommended:** Karpenter consolidation/disruption settings and cluster upgrade procedure are exercised.

## Observability And SLOs

- [ ] **Staging:** Structured logs, RED/domain metrics, trace propagation, request IDs, dashboards, and telemetry-redaction tests work end to end.
- [ ] **Production:** Proposed SLIs/SLOs have owners, valid data, error-budget policy, multi-window burn alerts, and actionable runbooks.
- [ ] **Production:** Telemetry pipeline outage cannot exhaust or fail application workloads.
- [ ] **Recommended:** Cost/cardinality/retention budgets are measured and enforced.

## Backups And Disaster Recovery

- [ ] **Production:** RDS PITR, snapshots, S3 versioning/replication policy, Terraform state recovery, ECR artifact availability, and GitOps rebuild sources are verified.
- [ ] **Production:** A timed restore into an isolated environment meets agreed RPO/RTO and includes integrity/application smoke checks.
- [ ] **Production:** Regional-disaster and unavailable-provider tabletop exercises identify communication, DNS, secrets, and dependency steps.
- [ ] **Future:** Multi-region architecture is adopted only for contractual availability, residency, latency, or measured risk triggers.

## CI, CD, And Releases

- [ ] **Staging:** Required PR checks include format/lint/type/unit/integration/OpenAPI/security/container/Terraform/Helm policy checks.
- [ ] **Production:** Images are immutable, digest-pinned, scanned, attributable, promoted once, and never tagged `latest` for deployment.
- [ ] **Production:** Argo CD RBAC, desired-state review, drift handling, migration sequencing, rollback, and emergency reconciliation are tested.
- [ ] **Future:** Canary/automated rollback is enabled only with trustworthy traffic volume and SLO analysis.

## Testing, Load, And Chaos

- [ ] **Staging:** Unit, DB/repository, HTTP, contract, frontend integration, E2E, and accessibility suites have stable owners and fixtures.
- [ ] **Production:** k6 normal/burst/sustained/concurrent-timer/invoice/report/backlog scenarios meet agreed budgets without saturation leaks.
- [ ] **Production:** API pod, worker, node, Redis, broker, RDS failover, provider 500, queue backlog, network latency, and partial-AZ hypotheses are exercised safely.
- [ ] **Recommended:** Soak tests validate memory, connections, queue drain, bloat, and telemetry cost.

## Documentation And Operations

- [ ] **Staging:** Architecture, API, schema, environment, deployment, and contributor docs match current implementation and link checks pass.
- [ ] **Production:** Incident, queue replay, RDS failover, restore, compromised credentials, high error burn, and rollback runbooks are timed and owned.
- [ ] **Production:** On-call, escalation, service ownership, change approval, and go-live evidence are recorded.
- [ ] **Recommended:** Game days and post-incident learning routinely update tests, runbooks, ADRs, and this checklist.
