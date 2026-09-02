# Clients Domain

## Purpose

The Clients module owns an organization's customer records used by projects and invoices.

## Model And Invariants

A client contains `id`, `organization_id`, display and legal names, contacts, email, billing address, tax/VAT identifier, preferred currency, status, notes, timestamps, and optional `archived_at`. Tenant-aware uniqueness applies only where the organization requires it; names are not globally unique.

- Every read and mutation uses both client and organization identifiers.
- `ACTIVE` clients may receive new projects and draft invoices; `ARCHIVED` clients remain readable for history but reject new work.
- Archiving never removes issued invoice history or referenced time entries.
- Billing values copied to an issued invoice become immutable invoice snapshots.
- Sensitive tax and contact fields require specific read/update permissions and are excluded from routine logs.

## Operations

Create, update, archive, restore, list with opaque cursor pagination, manage contacts, and inspect related projects/invoices. Deletion is limited to unreferenced accidental drafts; archive is the normal lifecycle action.

## Integration

Projects reference a client in the same organization. Invoice issuance snapshots billing identity. Audit events cover archival and sensitive billing changes. See [multi-tenancy](../architecture/multi-tenancy.md) and [API resources](../api/resources.md).
