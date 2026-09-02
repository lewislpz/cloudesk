# Proposed Cursor Pagination

## Purpose

ClouDesk collections use opaque keyset cursors so latency and correctness do not degrade with large offsets. This contract applies unless a resource explicitly documents a bounded non-paginated response.

## Request And Response

```http
GET /api/v1/organizations/7c.../projects?status=ACTIVE&sort=-updatedAt&limit=50&after=eyJ...
```

- `limit` defaults to `50`, has a minimum of `1`, and a maximum of `100` for ordinary resources. A resource may define a lower maximum.
- `after` is the opaque cursor returned by the preceding response.
- `sort` and filters must exactly match the query that produced the cursor.

```json
{
  "data": [],
  "page": {
    "nextCursor": "eyJ...",
    "hasMore": true
  }
}
```

`nextCursor` is `null` and `hasMore` is `false` at the end. The server fetches `limit + 1` rows to determine `hasMore`; it does not run a count query on every request. Exact totals are omitted by default and exposed only through a separately justified bounded aggregate.

## Stable Ordering

Every collection defines an allowlisted default sort and a unique tie-breaker. For example, `sort=-updatedAt` is implemented as:

```sql
ORDER BY updated_at DESC, id DESC
```

The cursor contains the last row's ordered values and ID. The next predicate is the tuple comparison matching direction, always including tenant scope and normalized filters. Null-capable sort fields need an explicit null ordering and cursor representation; they are not enabled until tested.

Cursor pagination gives stable continuation relative to the last key, not a frozen snapshot. Concurrent inserts or updates can move items between pages. Export or audit use cases that require snapshot consistency use a dedicated job/watermark rather than holding a long transaction across browser requests.

## Cursor Envelope And Integrity

The encoded cursor is versioned and includes, at minimum:

- cursor format version;
- resource/route identity;
- `organizationId` binding;
- normalized filter and sort fingerprint;
- last ordered values and unique ID;
- optional issuance/expiry metadata for sensitive or expensive queries.

It is serialized deterministically and authenticated with a server-managed HMAC key before base64url encoding. It must not contain secrets or unnecessary personal data because encoding is not encryption. Key rotation accepts the current and immediately previous signing key for a documented overlap.

Clients treat cursors as opaque. A malformed signature, unsupported version, wrong tenant, changed filter/sort, or expired cursor returns `400 INVALID_CURSOR` without explaining cryptographic details.

## Forward And Reverse Navigation

V1 guarantees forward traversal through `after`. Reverse navigation is not implicit. A `before` contract may be added per resource only with inverse ordering tests and a clear UI requirement. Frontends that need a back button retain previously received cursors/pages in client state rather than constructing cursors.

## Index Requirements

Every released filter/sort combination must have a reviewed query plan and a tenant-leading supporting index, typically `(organization_id, <filter columns>, <sort column>, id)`. The exact index follows PostgreSQL selectivity evidence; the API contract must not advertise arbitrary sort fields that cannot be served predictably.

Repository integration tests verify:

- no duplicates or gaps for an unchanged dataset;
- deterministic handling of equal sort values;
- rejection across organizations, resources, filters, and sort orders;
- maximum limits and invalid/tampered cursors;
- inserts/updates between pages have documented behavior;
- SQL uses keyset predicates rather than `OFFSET`.

