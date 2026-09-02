# Proposed Multi-Tenancy Architecture

## Purpose And Status

This document defines the proposed tenant boundary, authorization sequence, query
discipline, and defense-in-depth database controls for ClouDesk. It is a design
target; no tenant enforcement is implemented yet. The decision follows
[ADR-010](../decisions/ADR-010-multi-tenant-isolation.md): one shared PostgreSQL
database, an organization as the tenant, explicit application authorization, and
selective row-level security (RLS).

Related domain contracts are [Organizations](../domains/organizations.md),
[Memberships](../domains/memberships.md), [Identity](../domains/identity.md), and
[Audit](../domains/audit.md). Security threats and residual risks are recorded in
[Security architecture](security.md).

## Tenant Model And Invariants

An `organization` is the tenant. A global `user` may have zero or more
`memberships`, and each membership joins exactly one user to exactly one
organization. Authentication establishes the user; only an active membership plus
an allowed permission establishes tenant authority.

The following invariants apply to every transport, use case, repository, job, event,
cache, object, and audit path:

- Tenant-owned records carry a non-null `organization_id`; globally unique IDs never
  substitute for tenant scope.
- Tenant-owned HTTP routes are nested under
  `/api/v1/organizations/{organizationId}/...`. An organization ID in a body,
  query, cookie, slug, or `X-Organization-ID` header is not authority.
- Every protected operation is deny by default and requires authentication, an
  `ACTIVE` membership, a named permission, and any resource-level condition.
- Every tenant repository method accepts an explicit `organizationID`; SQL selects,
  updates, and deletes match it in addition to the resource ID.
- Parent/child relations use tenant-aware composite foreign keys, such as
  `(organization_id, project_id)`, so a valid child cannot reference another tenant.
- Tenant-aware uniqueness leads with `organization_id`. Examples include invoice
  numbers, normalized client keys, event deduplication, and idempotency records.
- PostgreSQL is authoritative. Redis contains only reconstructible, expiring state
  and is never consulted as the source of membership or permissions.
- S3 keys, cache keys, outbox events, inbox records, queue jobs, exports, and logs
  carry the tenant identifier selected by the server.

## Authorization Context

After authentication, the transport constructs an immutable application context:

```text
principal.user_id
principal.provider_subject
tenant.organization_id
membership.membership_id
membership.role
membership.version
permissions
request_id / trace_id
```

Callers cannot construct this context directly. Middleware and the Organization
Access module resolve it from the verified principal and route organization. Domain
use cases receive the context explicitly and still check the permission appropriate
to the command; transport middleware alone is insufficient because workers and
internal callers can enter the same use case.

### Tenant Authorization Flow

```mermaid
sequenceDiagram
    actor Caller
    participant Edge as Edge / same-origin web
    participant API as Go API
    participant Identity as Identity adapter
    participant Access as Organization Access
    participant Domain as Domain use case
    participant DB as PostgreSQL

    Caller->>Edge: request /organizations/{organizationId}/resource/{id}
    Edge->>API: authenticated request + explicit route IDs
    API->>Identity: validate session/token and map provider subject
    Identity-->>API: immutable ClouDesk user ID
    API->>Access: resolve (user ID, organization ID)
    Access->>DB: SELECT membership WHERE user + organization + ACTIVE
    DB-->>Access: membership role/version or none
    Access-->>API: tenant context + effective permissions
    API->>Domain: command/query + tenant context
    Domain->>Domain: require permission and resource condition
    Domain->>DB: SET LOCAL tenant context; scoped SQL with organization ID
    DB-->>Domain: tenant row or no row
    Domain-->>API: safe result or typed denial/not-found
    API-->>Caller: response without cross-tenant disclosure
```

The sequence deliberately repeats tenant scope in the use case, SQL predicate, data
constraints, and selected RLS policy. A failure in one layer must not silently expand
the result set.

## Route Rules And Deliberate Exceptions

Tenant-independent routes are narrowly allowlisted:

- `GET /api/v1/me` returns only the authenticated user's local identity summary.
- `GET /api/v1/organizations` lists organizations derived from that user's
  memberships; it does not accept an arbitrary user ID.
- `POST /api/v1/organizations` creates one organization and its owner membership in
  one transaction.
- `POST /api/v1/invitation-acceptances` is a pre-tenant, authenticated, idempotent
  command. It accepts a single-use invitation token in the body, never a URL, and
  establishes the membership atomically.
- `GET /api/v1/me/active-timer` is the deliberate user-scoped timer exception.

The active-timer lookup exists because ClouDesk permits only one active timer
globally per `user_id`, even across organizations. It queries only the authenticated
user, verifies that the timer's membership is still active, rechecks project/task
visibility, and returns the minimum organization/project detail required by the UI.
It never accepts a target user or tenant parameter. If membership was suspended or
the resource is no longer visible, the route conceals the tenant detail and the
normal tenant-scoped stop/remediation flow applies. Timer start and stop remain under
`/api/v1/organizations/{organizationId}/...` and require tenant authorization.

Any new non-tenant-prefixed route requires security review because it can become a
confused-deputy path around organization selection.

## Resource And Relationship Scoping

Permission is necessary but not always sufficient. Restricted projects add a
project-membership visibility condition; comments inherit task/project visibility;
files inherit their owner resource; reports filter every contributing row; and
notifications require both recipient and tenant scope.

Repository APIs use shapes similar to:

```go
GetProject(ctx context.Context, organizationID, projectID UUID) (Project, error)
UpdateTask(ctx context.Context, organizationID, projectID, taskID UUID, patch Patch) error
```

The intended SQL shape is:

```sql
SELECT id, organization_id, name
FROM projects
WHERE organization_id = $1
  AND id = $2;
```

Dynamic filters and sort fields come from allowlists and parameters; tenant IDs are
never string-interpolated. A nested route resolves every parent under the same
organization. A mismatch returns the same not-found contract as a missing resource.

## Selective PostgreSQL RLS

RLS is defense in depth, not the primary policy engine. The V1 implementation should
start with the high-blast-radius, directly tenant-owned tables reached by user
requests: memberships, clients, projects, tasks, comments, time entries, invoices
and lines, files, notifications, audit events, idempotency records, and reporting
projections. Join/child tables carry `organization_id` and receive equivalent policy
where practical.

Operational coordination tables are treated selectively:

- The outbox publisher may scan the outbox across tenants through a dedicated
  database role that can access the outbox but cannot read business tables.
- A worker claims an envelope containing the server-written `organization_id`, then
  opens a fresh tenant transaction and sets that organization before touching domain
  tables.
- Inbox/deduplication writes include `(consumer, organization_id, event_id)` and occur
  with the domain effect where possible.
- Migration, backup, and break-glass roles are separate from runtime roles. Runtime
  services never receive table-owner or `BYPASSRLS` privileges.

For a tenant request, the transaction sets server-derived context with `SET LOCAL`
before any protected query. A representative policy compares the row to
`current_setting('app.organization_id', true)` in both `USING` and `WITH CHECK`.
Production implementation must use `FORCE ROW LEVEL SECURITY` where table ownership
would otherwise bypass the policy.

`SET LOCAL`, rather than session-scoped `SET`, contains state to one transaction and
reduces pooled-connection leakage. The pool reset path remains tested, and requests
that cannot set a valid context fail closed. The organization-list and global
active-timer queries use narrow identity-scoped repositories with `app.user_id` and
explicit active-membership predicates; they are not general RLS bypasses.

RLS is initially deferred on tables where cross-tenant operational scanning is the
actual bounded responsibility and a policy would require a broad bypass. Deferral
requires a dedicated least-privilege role, explicit SQL scope for subsequent domain
access, and negative integration tests. RLS-only authorization, policies driven by
caller-provided settings, and a general runtime `BYPASSRLS` role are prohibited.

## Async Jobs, Events, And Cache Isolation

Every event/job envelope contains an immutable `event_id`, `organization_id`, event
type/version, aggregate identifiers, occurrence time, causation/correlation IDs, and
trace context. Consumers:

1. validate the schema and supported event type;
2. reject a missing or malformed organization ID;
3. derive tenant scope from the trusted outbox envelope, never a mutable nested
   payload field;
4. load all referenced records with that organization ID;
5. record inbox deduplication and database effects transactionally;
6. use provider idempotency where an external effect cannot join the transaction;
7. send repeated poison messages to a DLQ without widening privileges.

Cross-tenant batch jobs iterate an authorized list of tenant IDs and open an isolated
transaction per tenant. They never retain mutable tenant context across iterations.
Support/admin tooling uses the same explicit tenant selection, permission checks,
reason capture, and audit trail; there is no hidden global customer-data mode.

Cache keys use a versioned namespace such as
`v1:{environment}:{organizationId}:{visibilityScope}:{resource}:{queryHash}`. A user
or project visibility discriminator is included when organization membership alone
does not define the result. Organization switching cancels in-flight requests and
clears tenant query caches. Cache hits never skip current authorization for sensitive
operations. Redis outage produces a miss or a conservative endpoint-specific abuse
control, not an authorization fallback.

## S3 Tenant Isolation

The server chooses opaque keys under a tenant prefix and records ownership in
PostgreSQL. It authorizes the owner resource before creating a short-lived,
operation-specific presigned URL. Browser grants restrict method, key, content
constraints, expiry, and checksum where supported; they never permit bucket listing
or arbitrary prefixes. Completion revalidates tenant metadata and the actual object.
Workers use distinct workload roles and server-selected keys. Possession of a
presigned URL is temporary bearer access, so URLs are redacted from logs and never
placed in events or durable client caches.

## Authorization Failure Semantics

- Missing or invalid authentication returns `401` without account detail.
- A principal without an active membership receives the same concealed `404` as an
  unknown organization.
- An active member lacking a permission for an otherwise visible scope receives
  `403`.
- A missing resource and a resource in another organization both return the same
  `404`, with comparable work/timing where practical.
- A stale membership or resource version returns the documented conflict/precondition
  response; a cache or prior UI capability never overrides current PostgreSQL state.

Internal logs may distinguish reasons using protected IDs and stable codes, but
responses, metrics labels, and traces must not reveal another tenant's existence or
sensitive cardinality.

## Verification Required Before Release

Future implementation must include negative tests for every tenant endpoint,
repository, event consumer, cache, upload/download path, and reporting aggregate.
The matrix covers absent membership, suspended membership, wrong organization,
cross-tenant parent/child IDs, role downgrade during a request, tampered cursors,
idempotency replay after membership loss, stale pool state, RLS `USING` and
`WITH CHECK`, worker replay, DLQ replay, and the global active-timer exception.

Property/generative tests should create two or more organizations with colliding
human-readable names and similarly shaped records, then assert that no result or
side effect crosses the boundary. Database integration tests use the actual runtime
roles, not a migration owner. An independent security review is required before the
M1 authorization gate is accepted.

## Residual Risks And Evolution

- RLS policy/configuration mistakes remain possible; scoped SQL, tenant-aware
  constraints, runtime-role tests, and query review remain mandatory.
- Database administrators and break-glass actors can access tenant data. Their access
  is minimized, time-bound where possible, monitored, and audited outside the
  application database.
- A compromised application identity can act within its IAM and database grants;
  workload separation limits but cannot eliminate the blast radius.
- Custom roles, delegated administration, support impersonation, organization
  hierarchies, and regional data residency are deferred. Each requires a new threat
  model and ADR rather than extending V1 policy ad hoc.
- Database-per-tenant is reconsidered only for contractual isolation, residency,
  customer-managed keys, or scale that cannot be met safely by the shared model.
