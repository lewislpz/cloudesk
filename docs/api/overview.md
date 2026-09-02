# Proposed REST API Overview

## Purpose And Status

This document introduces the proposed external HTTP API for ClouDesk. The detailed conventions are defined in [conventions](conventions.md), [resources](resources.md), [pagination](pagination.md), [errors](errors.md), [idempotency](idempotency.md), and the [OpenAPI workflow](openapi.md). Nothing in this document claims that an endpoint is implemented.

## Consumers And Trust Boundaries

The initial consumer is the ClouDesk Next.js application through a generated TypeScript client. Operational tooling may use a separately defined contract later. Browser input, cookies/CSRF material, any future bearer tokens, route identifiers, cursors, idempotency keys, and uploaded-file metadata are all untrusted.

The production API completes OIDC Authorization Code + PKCE with Amazon Cognito, then issues an opaque application-session cookie backed by a hashed PostgreSQL session record. Local development uses the same identity/session port with a documented local adapter; ClouDesk does not introduce a second production password system. Authentication identifies a principal but never selects a tenant or grants a permission.

## Resource Model

- The base path is `/api/v1`.
- Tenant-independent routes include `/me` and `/organizations`.
- Every tenant-owned route is nested below `/organizations/{organizationId}`.
- JSON field names are `camelCase`; route collection names are lowercase plural nouns with hyphens only for compound resources.
- State transitions that cannot be represented safely as a partial resource update use named command subresources such as `/invoices/{invoiceId}/issue`.
- PostgreSQL is authoritative. A successful synchronous response reflects committed state.
- Slow side effects such as email, PDF generation, exports, and malware scanning return a committed status resource and continue asynchronously.

The API never trusts an `X-Organization-ID` header as tenant authority. If a gateway adds such a header for observability, it must equal the authorized route parameter and is discarded before application authorization.

## Media, Time, Money, And Identifiers

- Requests and responses use `application/json`; UTF-8 is implicit.
- Timestamps use RFC 3339 with a UTC `Z` suffix. Date-only business fields use ISO `YYYY-MM-DD` and retain their date semantics.
- Monetary amounts are decimal strings with an explicit ISO 4217 currency, never JSON floating-point values. The server owns rounding rules.
- Public resource IDs are opaque UUIDs. Clients must not infer creation time, tenancy, or ordering from them.
- Absent optional values and explicit `null` are distinct where PATCH semantics require it.

## Contract Shape

Single-resource responses return the resource directly. Collection responses use a stable envelope because they include pagination metadata:

```json
{
  "data": [],
  "page": {
    "nextCursor": null,
    "hasMore": false
  }
}
```

Errors use the envelope in [errors](errors.md). Asynchronous commands return `202 Accepted`, a `Location` header for the status resource where one exists, and a body describing the accepted state. Create operations return `201 Created` only after the resource and required outbox records commit.

## Cross-Cutting Request Flow

```mermaid
sequenceDiagram
    participant Web as Next.js generated client
    participant API as Go API
    participant Session as Identity/session boundary
    participant App as Application use case
    participant DB as PostgreSQL

    Web->>API: Request + opaque cookie + CSRF when unsafe + organizationId path
    API->>Session: Resolve hashed session; enforce expiry/revocation
    Session-->>API: Principal ID
    API->>DB: Load active membership in organization
    DB-->>API: Membership and role
    API->>App: Principal, tenant scope, command/query
    App->>App: Check permission and domain rules
    App->>DB: Tenant-scoped transaction/query
    DB-->>App: Committed result
    App-->>API: Resource or typed error
    API-->>Web: OpenAPI-defined response + request ID
```

The tenant route and authenticated membership form the authorization scope. Resource lookups still include `organization_id`; a globally unique resource ID is not sufficient.

## Current, Target, And Future

- **Local V1:** one API process, local identity adapter, PostgreSQL, and generated clients.
- **Production target:** horizontally scaled stateless API, Cognito OIDC, RDS PostgreSQL, WAF/ALB controls, SQS-backed asynchronous workers, and OpenTelemetry.
- **Future evolution:** a new API major, service extraction, read replicas, or additional clients only after compatibility and load evidence justify them.
