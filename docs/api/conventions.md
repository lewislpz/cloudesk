# Proposed API Conventions

## Purpose

This document defines proposed HTTP, naming, compatibility, filtering, and concurrency conventions for ClouDesk. The canonical machine-readable contract will be the OpenAPI document described in [openapi](openapi.md).

## Paths And Names

- Base path: `/api/v1`.
- Collections use plural nouns: `/projects`, `/time-entries`, `/audit-events`.
- Tenant resources use `/organizations/{organizationId}/...` without an authoritative tenant header.
- Path parameters are descriptive: `{projectId}`, not `{id}`.
- JSON properties use `camelCase`; schema and operation names use stable `PascalCase`/`camelCase` identifiers in OpenAPI.
- Command endpoints use a final verb only for a real domain transition, for example `POST .../invoices/{invoiceId}/issue`. Ordinary mutation uses `POST`, `PATCH`, or `DELETE` on resources.
- Boolean query values are `true` or `false`; repeated query parameters represent multi-value filters.

## Methods And Success Statuses

| Operation | Method | Normal response | Notes |
| --- | --- | --- | --- |
| Read resource | `GET` | `200` | Includes `ETag` for versioned resources. |
| List resources | `GET` | `200` | Uses cursor pagination. |
| Create resource | `POST` | `201` | Returns body and `Location` after commit. |
| Accept async work | `POST` | `202` | Returns committed status and optional `Location`. |
| Partial update | `PATCH` | `200` | Uses `application/merge-patch+json` only if null/delete semantics are defined; otherwise a named JSON update schema. |
| Delete eligible resource | `DELETE` | `204` | Hard deletion is domain-specific, not universal. |

`PUT` is reserved for complete replacement and is not proposed for initial resources. Bulk endpoints require their own atomicity and partial-failure contract; they are not inferred from single-resource routes.

## Authentication And Tenant Authorization

Browser requests use a same-origin opaque application-session cookie issued by the Go API after Authorization Code + PKCE with Cognito. The API resolves the hashed session record from PostgreSQL, enforces idle/absolute expiry and revocation, and maps it to a ClouDesk user. Cognito access/refresh tokens stay server-side and out of browser JavaScript. A future machine-to-machine bearer contract requires separate endpoints/security requirements and may not be ambiguously combined with browser credentials.

For `/organizations/{organizationId}/...`, the server verifies an active membership before resource lookup. A valid token with no membership receives tenant-not-found behavior. A member who lacks a permission for a known resource receives `403`. UI permission checks are advisory only; every command is authorized server-side.

## Headers

| Header | Direction | Use |
| --- | --- | --- |
| `Cookie` | Request | Secure, HttpOnly opaque application session; generated clients use same-origin credentials. |
| `X-CSRF-Token` | Request | Session-bound token required with Origin/Fetch-Metadata validation on unsafe cookie-authenticated methods. |
| `X-Request-ID` | Both | Optional client correlation input; server validates or replaces it and always returns the effective value. |
| `traceparent`, `tracestate` | Both | W3C trace propagation; never an authorization input. |
| `Idempotency-Key` | Request | Required on operations listed in [idempotency](idempotency.md). |
| `Idempotency-Replayed` | Response | `true` when a stored response is replayed. |
| `If-Match` | Request | Required by selected versioned mutations. |
| `ETag` | Response | Quoted opaque representation version. |
| `Location` | Response | Created or accepted resource/status URI. |
| `Retry-After` | Response | Retry guidance on `429`, temporary `503`, or in-progress idempotency conflict. |

Clients must not log session/CSRF material, bearer tokens for any future service contract, idempotency keys, presigned URLs, or sensitive bodies.

## Optimistic Concurrency

Invoices, organization settings, and other explicitly versioned resources return an `ETag`, initially derived from an opaque encoding of the resource version. Their mutating operations require `If-Match`. The application performs a tenant-scoped update such as `... WHERE organization_id = $1 AND id = $2 AND version = $3` and increments the version atomically.

- Missing required `If-Match`: `428 Precondition Required`.
- Stale/mismatched `If-Match`: `412 Precondition Failed`.
- A valid version that violates the current domain state (for example, issuing an already void invoice): `409 Conflict`.

ETags are opaque; clients store and return them without parsing. Read-modify-write clients refresh after a `412` and ask the user to reconcile rather than silently overwriting.

## Filtering, Search, And Sorting

Each collection documents an allowlist. Unknown filters or sort fields return `400`; they are never interpolated into SQL. Proposed common syntax:

```text
GET .../projects?status=ACTIVE&clientId=<uuid>&sort=-updatedAt&limit=50&after=<cursor>
```

- Repeated values express OR within one filter, for example `status=ACTIVE&status=ON_HOLD`.
- Different filters combine with AND.
- `sort=field` is ascending; `sort=-field` is descending.
- Every sort has a unique deterministic ID tie-breaker.
- Free-text `q` is supported only on documented resources, normalized consistently, length-limited, and backed by an appropriate index before release.
- Date/time ranges use explicit `from`/`to` parameter names documented per resource. Inclusive/exclusive boundaries must be stated in OpenAPI descriptions.

See [pagination](pagination.md) for cursor binding and limits.

## Validation And PATCH Semantics

The transport rejects malformed JSON, duplicate ambiguous fields, unsupported media types, unknown fields where the schema is closed, oversized bodies, invalid UUIDs, and schema-bound violations. Domain validation occurs after parsing. Field errors use JSON Pointer locations in the [error details](errors.md).

Each PATCH operation has a named schema that distinguishes omitted, supplied, and nullable fields. A field is nullable only when the OpenAPI schema says so. Immutable fields such as IDs, organization ownership, computed totals, audit metadata, and versions cannot be patched.

## Rate Limits And Abuse Responses

Rate policy is selected by endpoint sensitivity and may combine per-IP, per-principal, and per-organization token buckets. Authentication attempts, invitation creation, presigned URL requests, exports, and invoice sends are stricter than normal reads. A limit response is `429 RATE_LIMITED`, includes `Retry-After`, and does not reveal whether an account or tenant exists.

Distributed production limits may use Redis. Security-sensitive fail behavior is endpoint-specific: strict endpoints fail closed or fall back to a conservative local emergency limit; ordinary reads may continue with bounded local protection. Redis never becomes the source of permissions, sessions, idempotency records, or business state.

## Versioning And Compatibility

`v1` is a major compatibility boundary in the URI. Minor/additive changes do not change the URI. Compatible evolution includes adding optional request fields, new response fields, and new endpoints when consumers ignore unknown fields as documented. The following receive explicit breaking-change review:

- removing or renaming fields, operations, error codes, or enum values;
- making an optional input required;
- narrowing accepted values or changing field semantics;
- changing status codes, authorization behavior, pagination order, or idempotency scope;
- adding an enum member when a generated exhaustive client would fail.

Potentially incompatible enum growth should use documented extensible string values or a new contract version rather than assuming all generated consumers tolerate it.

Deprecation is announced in documentation and OpenAPI, then signaled with standard `Deprecation`, `Sunset`, and successor `Link` headers where applicable. A proposed minimum migration window is 180 days for production consumers, except when an actively exploited security issue requires faster removal. ClouDesk will not operate a second major version until a real incompatible requirement exists; when it does, the current and successor versions have an explicit consumer migration and retirement plan.

## Request Correlation And Caching

The server returns an effective request ID on every response, including errors. Logs and asynchronous events preserve request/trace correlation without treating caller-supplied IDs as trusted metadata.

Authenticated tenant responses default to `Cache-Control: private, no-store` until a resource-specific cache policy is reviewed. Any future cache key must include principal visibility where needed, `organizationId`, route, normalized query, API version, and representation version. CDN/shared caching of tenant data is prohibited by default.
