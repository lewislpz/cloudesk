# ClouDesk Glossary

## Purpose

This glossary gives shared meaning to terms used across product, architecture, operations, and ADRs.

| Term | Meaning |
| --- | --- |
| ClouDesk | The proposed SaaS product; this exact capitalization is mandatory. |
| Organization | The primary tenant and isolation boundary. |
| Principal | An authenticated user or workload identity making a request. |
| Membership | A user's relationship, status, and role within one organization. |
| Permission | A named action granted by a role, such as `invoices:issue`. |
| Tenant-owned resource | A record or object whose authorization and keys include `organization_id`. |
| Modular monolith | One cohesive backend codebase/deployment family with enforced module boundaries. |
| Worker | A separately runnable Go process consuming durable asynchronous work. |
| Outbox | Events written in the same PostgreSQL transaction as the business change. |
| Inbox | Consumer-side deduplication state for at-least-once messages. |
| Idempotency key | A caller-provided key that safely replays one operation for the same tenant, principal, and request fingerprint. |
| Source of truth | The authoritative durable owner of a fact; PostgreSQL owns business state. |
| RLS | PostgreSQL Row-Level Security, used selectively as defense in depth. |
| SLI / SLO | A measured reliability indicator and its proposed objective. |
| RPO / RTO | Maximum proposed data-loss window and recovery-time objective. |
| Production target | A designed state that is not claimed to exist yet. |
| Future evolution | A deferred change requiring an explicit trigger and ADR update. |
