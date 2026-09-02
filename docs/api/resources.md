# Proposed API Resources

## Purpose And Scope

This document inventories the proposed V1 REST resources and key state-changing operations. It is a design input for the future [OpenAPI source](openapi.md), not an implemented route list. All `{organizationId}` routes require an active membership, server-side permission checks, and tenant-scoped persistence.

Common response, filtering, version, and status behavior follows [conventions](conventions.md). Collection routes follow [pagination](pagination.md), failures follow [errors](errors.md), and sensitive commands follow [idempotency](idempotency.md).

## Identity And Organizations

Production sign-in, logout, token refresh, password recovery, and later MFA are identity-provider flows rather than application password endpoints. ClouDesk exposes the mapped application identity and organization resources.

| Route | Purpose | Important behavior |
| --- | --- | --- |
| `GET /api/v1/me` | Return the mapped user and identity summary. | Does not select a tenant. |
| `GET /api/v1/me/active-timer` | Return the principal's single active timer, if any. | User-scoped exception; returns tenant/project detail only while the principal retains permission to view it. |
| `GET /api/v1/organizations` | List organizations visible to the principal. | Membership-scoped, cursor paginated. |
| `POST /api/v1/organizations` | Create an organization and owner membership. | Idempotent; atomic organization, owner membership, audit, and outbox write. |
| `GET /api/v1/organizations/{organizationId}` | Return organization settings visible to a member. | Returns `ETag`. |
| `PATCH /api/v1/organizations/{organizationId}` | Update allowed organization settings. | `organization:update`; requires `If-Match`. |
| `GET /api/v1/organizations/{organizationId}/memberships` | List active, suspended, or revoked memberships according to filters. | Pending invitations are separate resources; permission controls sensitive member fields. |
| `GET /api/v1/organizations/{organizationId}/memberships/{membershipId}` | Read one membership. | Resource and tenant IDs are both scoped. |
| `PATCH /api/v1/organizations/{organizationId}/memberships/{membershipId}` | Change supported role/status fields. | Cannot remove the last owner; privileged audit event; `If-Match`. |
| `DELETE /api/v1/organizations/{organizationId}/memberships/{membershipId}` | Remove/revoke a membership when allowed. | Last-owner and self-removal rules apply. |
| `POST /api/v1/organizations/{organizationId}/invitations` | Invite a user by approved identity attributes. | Idempotent; rate-limited; email is asynchronous. |
| `GET /api/v1/organizations/{organizationId}/invitations` | List invitations. | Does not expose reusable secret material. |
| `DELETE /api/v1/organizations/{organizationId}/invitations/{invitationId}` | Revoke a pending invitation. | Already accepted/revoked is a defined conflict or no-op contract. |
| `POST /api/v1/invitation-acceptances` | Accept an invitation for the authenticated principal. | Idempotent pre-tenant command; signed token is supplied in the JSON body, never the URL; creates membership atomically. |

Invitation acceptance requires a signed, short-lived, single-use token and authenticated identity binding. It must not trust an email address supplied separately in the request. The response identifies the newly available organization without returning reusable invitation secret material.

V1 organization status values are `ACTIVE` and `SUSPENDED`. The future closure
workflow adds `CLOSURE_PENDING` and terminal `CLOSED` through an additive contract and
migration; `PENDING_DELETION` is not part of the ClouDesk vocabulary.

## Clients

Base: `/api/v1/organizations/{organizationId}/clients`.

| Method and suffix | Purpose | Important behavior |
| --- | --- | --- |
| `GET /` | List clients. | Filters: `status`, `q`; sort allowlist; cursor pagination. |
| `POST /` | Create a client. | Idempotent; tenant-aware normalized-name/tax constraints where applicable. |
| `GET /{clientId}` | Read client details. | Sensitive billing fields require permission. |
| `PATCH /{clientId}` | Update mutable fields or archive state. | Named update schema; versioning may be introduced before shared editing. |

Clients with referenced invoices or time entries are archived, not deleted. Hard deletion is limited to an explicitly eligible never-used record and may be omitted from V1.

## Projects And Project Membership

Base: `/api/v1/organizations/{organizationId}/projects`.

| Method and suffix | Purpose | Important behavior |
| --- | --- | --- |
| `GET /` | List projects. | Filters: `clientId`, `status`, `ownerId`, `tag`, `q`; deterministic sort. |
| `POST /` | Create a project. | Idempotent; client and owner must belong to the route organization. |
| `GET /{projectId}` | Read a project. | Includes computed summary only when bounded. |
| `PATCH /{projectId}` | Update fields, lifecycle status, or archive it. | Domain transition validation; selected shared settings may require `If-Match`. |
| `GET /{projectId}/memberships` | List project members. | Organization membership remains prerequisite. |
| `POST /{projectId}/memberships` | Add a project member. | Idempotent; cannot reference another tenant. |
| `DELETE /{projectId}/memberships/{membershipId}` | Remove project access. | Protects required owner/manager invariants. |

Project membership routes refer to organization membership IDs, not raw identity-provider subjects.

## Tasks, Assignments, And Comments

Tasks are nested under projects so tenant and project context are explicit:

```text
/api/v1/organizations/{organizationId}/projects/{projectId}/tasks
```

| Method and suffix | Purpose | Important behavior |
| --- | --- | --- |
| `GET /` | List project tasks. | Filters: `status`, `priority`, `assigneeId`, `dueFrom`, `dueTo`, `label`, `q`. |
| `POST /` | Create a task. | Idempotent; all assignees must be eligible project members. |
| `GET /{taskId}` | Read task detail. | Tenant and parent project both participate in lookup. |
| `PATCH /{taskId}` | Update content, state, priority, or schedule. | Server enforces lifecycle and permission rules. |
| `GET /{taskId}/comments` | List comments. | Stable chronological keyset order. |
| `POST /{taskId}/comments` | Add a comment. | Idempotent; mention targets validated in tenant/project scope. |
| `PATCH /{taskId}/comments/{commentId}` | Edit an eligible comment. | Author/time-window/privileged moderation rules; audit where required. |
| `DELETE /{taskId}/comments/{commentId}` | Delete or redact when policy permits. | Response semantics distinguish deleted content without leaking it. |

Assignments are represented in task create/update schemas initially. Dedicated assignment command resources are added only if independent audit/idempotency semantics require them.

## Time Tracking

Base: `/api/v1/organizations/{organizationId}`.

| Route | Purpose | Important behavior |
| --- | --- | --- |
| `GET /time-entries` | List entries across allowed projects. | Filters by user/project/task/billable/time range; cursor pagination. |
| `POST /time-entries` | Create a completed manual entry. | Idempotent; UTC instants; validates positive duration and overlap policy. |
| `GET /time-entries/{timeEntryId}` | Read one entry. | Rates and notes follow billing permissions. |
| `PATCH /time-entries/{timeEntryId}` | Correct an eligible entry. | Audited; invoiced/locked entries require a correction workflow. |
| `DELETE /time-entries/{timeEntryId}` | Delete an eligible unbilled entry. | Audited; never silently removes invoiced evidence. |
| `POST /timers` | Start a timer. | Idempotent; a global partial unique invariant on `user_id` prevents simultaneous active timers across organizations. |
| `POST /timers/{timerId}/stop` | Stop a timer and materialize duration. | Idempotent; concurrent stop returns replay or current state, never double time. |

The entry retains `organizationId` and `membershipId`, but active-timer uniqueness is global per ClouDesk user because simultaneous time across two organizations would be false accounting. `/api/v1/me/active-timer` is the explicit user-scoped lookup; it reveals only the caller's own timer and returns tenant/project details only while current memberships permit them. The API stores instants in UTC. User timezone is display/report context and never rewrites historical instants. Rate resolution is captured on the entry or invoice line at the business-defined lock point so later project-rate changes do not rewrite issued billing history.

## Invoices

Base: `/api/v1/organizations/{organizationId}/invoices`.

| Method and suffix | Purpose | Important behavior |
| --- | --- | --- |
| `GET /` | List invoices. | Filters: client, state, currency, issue/due range; no unbounded totals query. |
| `POST /` | Create a draft from manual lines and/or eligible time entries. | Idempotent; transaction locks/marks source entries and writes outbox/audit records. |
| `GET /{invoiceId}` | Read invoice and immutable monetary snapshot. | Returns `ETag`. |
| `PATCH /{invoiceId}` | Edit allowed draft fields and lines. | Requires `If-Match`; totals recomputed server-side. |
| `POST /{invoiceId}/issue` | Transition `DRAFT` to `ISSUED`; normal synchronous response is `200`. | Requires `If-Match` and idempotency: `428` missing precondition, `412` stale version, `409` current-state conflict; invoice number assigned atomically and PDF generation queued. |
| `POST /{invoiceId}/send` | Request delivery of an issued invoice. | `202`; idempotent; creates durable delivery attempt/outbox state. |
| `GET /{invoiceId}/deliveries/{deliveryId}` | Read one durable delivery attempt. | Exposes queued/processing/sent/failed status without provider secrets. |
| `POST /{invoiceId}/void` | Void an eligible invoice. | Idempotent and version-checked; reason required and audited. |

The persisted financial state machine is `DRAFT -> ISSUED -> SENT -> PARTIALLY_PAID -> PAID`, with eligible non-paid states transitioning to `VOID` under explicit rules. `OVERDUE` is a computed read/filter status from due date plus unpaid balance, not a mutation or stored financial state. `SENT` is recorded only after the delivery provider reports accepted/success according to the notification design, not merely when a queue message is published. Payment processing is outside V1; payment state changes need an audited administrative/reconciliation contract before implementation.

Invoice creation is synchronous for authoritative draft state. PDF rendering, S3 storage, and email are asynchronous. The response exposes processing/delivery status instead of implying completion.

## Files And Attachments

Base: `/api/v1/organizations/{organizationId}/files`.

| Method and suffix | Purpose | Important behavior |
| --- | --- | --- |
| `GET /` | List authorized file metadata. | Filters by owner resource, status, media type; never exposes object-store credentials. |
| `POST /upload-requests` | Create pending metadata and a presigned upload grant. | Idempotent; validates intended owner, size, media type, checksum; short expiry. |
| `POST /{fileId}/complete` | Confirm upload for server verification/scanning. | Idempotent; checks object key, size, checksum, and tenant metadata; may return `202`. |
| `POST /{fileId}/download-requests` | Create a short-lived authorized download URL. | Strict rate limit; response `Cache-Control: no-store`. |
| `DELETE /{fileId}` | Request deletion under retention rules. | Durable metadata state first; physical S3 cleanup may be asynchronous. |

The server chooses object keys containing a non-guessable tenant prefix and file ID. Clients never provide a final bucket/key. A presigned URL is a temporary capability, so its response and logs are treated as sensitive.

## Notifications

Base: `/api/v1/organizations/{organizationId}/notifications`.

| Method and suffix | Purpose | Important behavior |
| --- | --- | --- |
| `GET /` | List the principal's in-app notifications in this tenant. | Filters by read state/type; cursor pagination. |
| `GET /{notificationId}` | Read one notification. | Principal recipient and tenant both scoped. |
| `PATCH /{notificationId}` | Set supported state such as `readAt`. | Idempotent natural update. |
| `GET /preferences` | Read the principal's effective event/channel preferences and defaults. | Returns tenant/member-scoped entries and `ETag`s without exposing other recipients. |
| `PUT /preferences/{eventType}/{channel}` | Enable or disable one preference. | Requires `If-Match` for an existing override; mandatory security/billing notices reject disable with `422`; omission/default restoration is explicit. |

Email is a delivery channel behind asynchronous events, not a separate public CRUD resource. Provider delivery state and retry/DLQ operations are restricted operational interfaces.

## Reports And Exports

Base: `/api/v1/organizations/{organizationId}`.

| Route | Purpose | Important behavior |
| --- | --- | --- |
| `GET /reports/summary` | Return bounded operational aggregates. | Required time range, permission-aware dimensions, query timeout. |
| `POST /report-exports` | Request a durable report export. | `202`; idempotent; bounded range/format; outbox event. |
| `GET /report-exports/{reportExportId}` | Poll status and metadata. | Download uses the file authorization flow after completion. |

Expensive report computation runs in a dedicated bounded worker pool. The initial API does not expose arbitrary SQL-like grouping or unbounded date ranges.

## Audit Events

```text
GET /api/v1/organizations/{organizationId}/audit-events
GET /api/v1/organizations/{organizationId}/audit-events/{auditEventId}
```

Audit events are append-only and API read-only. Lists require a bounded time range for broad tenants and support allowlisted actor, action, resource type, and resource ID filters. Metadata is redacted by policy; the API never exposes credentials, tokens, full sensitive request bodies, or internal stack traces.

## Resource Consistency Rules

- A nested `projectId`, `taskId`, `clientId`, membership ID, or file owner must resolve inside the route organization. Mismatches are not found, not cross-tenant redirects.
- A create/update that writes durable state and emits a reliable event writes both in one PostgreSQL transaction.
- Generated responses describe current committed state. Async progress is a resource state, not a promise hidden behind `200`.
- Collection queries are always bounded and use deterministic keyset order.
- Archive, void, redact, and delete are distinct domain operations; no universal soft-delete behavior is assumed.
