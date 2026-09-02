# Organizations Domain

## Purpose And Status

An organization is ClouDesk's tenant and the root ownership boundary for business
data. This proposed domain owns organization identity, lifecycle, settings, and the
atomic creation of the first owner membership. It does not own authentication or the
lifecycle of domain resources such as projects and invoices.

## Model

An organization contains an opaque `id`, display name, normalized slug used only for
navigation, business/timezone/currency defaults, lifecycle status, version, and
audit timestamps. Legal/tax settings are added only with invoicing requirements and
are permission-restricted. Slugs and names never authorize access and may change.

Proposed lifecycle states are:

- `ACTIVE`: normal authorized use;
- `SUSPENDED`: tenant access is denied except a narrowly designed recovery/support
  flow; workers do not continue ordinary tenant side effects;
- `CLOSURE_PENDING`: future, policy-driven export/retention/deletion workflow;
- `CLOSED`: future terminal business state with retained records as policy requires.

V1 needs `ACTIVE` and an operational suspension control. Self-service tenant deletion
is deferred until legal retention, invoices, files, backups, audit, and recovery have
one approved policy. There is no generic cascading delete.

## Invariants And Operations

- `POST /api/v1/organizations` creates the organization, one `OWNER` membership for
  the authenticated user, audit record, and required outbox event in one PostgreSQL
  transaction. The command uses a pre-tenant idempotency scope.
- An active organization always has at least one active owner. Concurrent role/removal
  operations lock or otherwise serialize the last-owner invariant.
- Settings changes use optimistic concurrency and `organization:update`; sensitive
  policy changes require stronger permissions and an audit reason.
- Tenant-owned routes always use the immutable organization ID under
  `/api/v1/organizations/{organizationId}/...`. A slug is resolved only after
  authenticated membership discovery and cannot override the route ID.
- Default currency/timezone changes affect future calculations/display rules only;
  they do not rewrite issued invoices or historical instants.
- Organization suspension, closure, export, and restore are privileged, idempotent,
  audited workflows. Workers recheck organization status before side effects.

## Discovery And Switching

`GET /api/v1/organizations` derives its list from the authenticated user's current
memberships. It accepts no arbitrary user ID. The response contains only safe
navigation attributes and effective capabilities needed to choose a tenant.

Switching organizations creates no server-side global tenant authority. Each request
still carries the selected organization in the path and revalidates membership.
Frontend query keys begin with the immutable organization ID, in-flight work is
cancelled, and tenant caches are cleared before rendering another workspace.

## Settings And Delegation

Settings are grouped by ownership rather than stored as an unvalidated JSON bag.
Organization owns name/navigation and product defaults; Memberships owns access
policy; Invoicing owns numbering/tax rules; Files owns upload/retention policy; and
Notifications owns channel preferences. Unknown or cross-domain settings are
rejected, and sensitive updates use named schemas and field-level permissions.

Custom roles and organization-specific permission overrides are not V1 features.
They are introduced only with a policy version, safe migration/fallback behavior,
administrative UX, audit coverage, and tests proving that an invalid policy fails
closed.

## Failure And Audit Behavior

Unknown organizations and organizations without an active membership use the same
concealed not-found response. A suspended organization does not leak suspension
detail to non-members. Partial create cannot leave an ownerless organization; all
authoritative rows roll back together. Async provider failure after creation leaves
the committed tenant and outbox work visible/retryable rather than falsely rolling
back success.

Audit organization creation, owner/role changes, sensitive setting changes,
suspension/reactivation, export, closure request/cancel/complete, and administrative
access. Metadata uses allowlisted before/after fields and excludes secrets and full
sensitive settings.

## Verification And Evolution

Tests cover atomic/idempotent creation, concurrent last-owner changes, stale versions,
slug collision/rename, wrong-tenant route IDs, suspension during requests/jobs,
organization switching/cache isolation, settings field authorization, and absence of
cascade deletion. Future hierarchy, subsidiaries, organization merge/transfer,
custom domains, residency, customer-managed keys, and closure workflows require new
ADRs and tenant threat-model updates.
