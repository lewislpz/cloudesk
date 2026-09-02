# Proposed Idempotency Contract

## Purpose

ClouDesk uses `Idempotency-Key` to make retries of sensitive HTTP commands safe when a client loses a response or a proxy retries. Idempotency does not replace database constraints, optimistic concurrency, authorization, or consumer deduplication.

## Required Operations

V1 requires a key for at least:

- organization creation, tenant invitation creation, and invitation acceptance;
- starting and stopping timers;
- creating invoices and issuing, sending, or voiding them;
- creating file upload requests and completing uploads;
- requesting report exports;
- any later POST that can charge, reserve, send, or launch expensive asynchronous work.

OpenAPI marks the header required per operation. Ordinary reads are naturally idempotent and do not use the store. PATCH/DELETE rely on their resource preconditions unless an operation has an independently retryable side effect, in which case the contract explicitly requires a key.

## Client Contract

```http
POST /api/v1/organizations/{organizationId}/invoices
Idempotency-Key: 018f4f9d-7c1d-7a2f-8d3b-9a33bf50a719
Content-Type: application/json
```

- The key is a client-generated UUID (UUIDv7 is preferred for operational locality); maximum textual length is 64 characters.
- A client creates one key for one intended operation and retains it until the operation's outcome is known.
- A retry sends the same method, canonical route, relevant headers, and semantically identical body.
- A different intended operation always uses a new key.
- The client may retry a transport error or retryable `5xx` with the same key and bounded backoff. It must not automatically replace the key after an unknown outcome.

## Scope And Fingerprint

The primary uniqueness scope is:

```text
(organization_id, principal_id, operation, idempotency_key)
```

`operation` is a stable server identifier, normally the OpenAPI `operationId`, not a raw URL. `principal_id` prevents one member from obtaining another member's stored response. For the pre-tenant organization-create operation only, `organization_id` is absent and a separate partial uniqueness rule scopes the record by `(principal_id, operation, idempotency_key)`.

Authorization and active membership are checked on every request, including replay, before a stored body can be returned. Organization scope comes from the authorized path, never an idempotency header.

The server stores a cryptographic request fingerprint over a deterministic representation of:

- HTTP method and stable operation ID;
- route organization and other identity-bearing path values;
- normalized query parameters when the operation permits them;
- the parsed request body serialized canonically;
- semantically relevant headers such as `If-Match` and content type.

Bearer tokens, request IDs, trace headers, and transport-only headers are excluded. The server hashes rather than stores a second raw request body unless a narrowly defined audit requirement says otherwise.

Reusing the same scoped key with a different fingerprint returns `409 IDEMPOTENCY_KEY_REUSED`. It never executes either interpretation again.

## Persistence Model

The proposed PostgreSQL record contains:

```text
id
organization_id nullable only for approved pre-tenant operations
principal_id
operation
idempotency_key
request_fingerprint
response_status
response_headers (allowlisted only)
response_body
resource_type/resource_id when useful
created_at
completed_at
expires_at
```

Only safe replay headers such as `Content-Type`, `Location`, and `ETag` are stored. Cookies, bearer material, presigned URLs with an expiry longer than the replay window, trace IDs, and hop-by-hop headers are not blindly replayed. The current retry receives a new `X-Request-ID` and `Idempotency-Replayed: true`; the stored response body remains otherwise semantically identical.

The idempotency record, business mutations, audit record, and outbox events commit in the same PostgreSQL transaction. This is why idempotent HTTP commands cannot make required external calls inside the transaction.

## Concurrency Algorithm

After authentication, tenant membership, request parsing, and fingerprint construction:

1. Begin a bounded database transaction.
2. Acquire a transaction-scoped advisory lock derived from the full uniqueness tuple without waiting indefinitely.
3. If the lock is held by the same concurrent operation, return `409 IDEMPOTENCY_IN_PROGRESS` with a short `Retry-After`.
4. Read the existing idempotency record under the lock.
5. If it is complete and the fingerprint matches, commit/close without executing the use case and replay the stored response.
6. If it exists with a different fingerprint, return `409 IDEMPOTENCY_KEY_REUSED`.
7. Otherwise insert the reservation, execute the application command using transaction-bound repositories, serialize the successful OpenAPI response, store its allowlisted replay data, and commit once.
8. Return the committed response.

The durable record is not committed in an `in_progress` state. A process crash releases the advisory lock and rolls back the reservation, business changes, audit entry, and outbox entries together. A retry can then execute safely. The uniqueness constraint remains the correctness backstop even if an advisory-lock hash collision creates a harmless transient in-progress response.

Only committed successful/accepted outcomes are replayed initially. Validation, authorization, and domain errors do not mutate state and need not be cached. `5xx`, cancellation, serialization failure, and transaction failure roll back the reservation. Response serialization occurs before commit so an unrepresentable success cannot commit without replay data.

## Replay And Preconditions

The server performs authentication and current authorization first, then checks the idempotency store before reevaluating a mutation precondition. Therefore a retry with the original `If-Match` can replay the committed response even though the resource version has advanced. A new key with that stale `If-Match` returns `412 VERSION_MISMATCH`.

Replays return the original status (`201`, `200`, or `202`) and semantic body. A replay never re-emits an outbox event, reassigns an invoice number, restarts a timer, creates another S3 metadata record, or repeats an email request.

## Expiration And Cleanup

Retention is operation-specific and declared in the operation description. Proposed minimums are 24 hours for ordinary commands and 7 days for invoice creation/state commands and report exports. These are initial policy values to validate against client retry behavior and storage cost, not universal guarantees.

After `expires_at`, a key may be treated as new once the record is safely cleaned, so clients must not reuse expired keys. Cleanup is a bounded asynchronous PostgreSQL job ordered by expiry and monitored for backlog. It deletes only idempotency replay records; it never deletes business resources, audit evidence, outbox events, or inbox records. Legal/audit policy can require a longer fingerprint-only retention for selected financial operations without retaining response personal data.

## Relationship To Async Deduplication

HTTP idempotency prevents duplicate command acceptance. The transactional outbox may still publish the resulting event more than once. Every event has its own immutable `event_id`, and consumers use a tenant-scoped inbox/processed-event record in the same transaction as their database effect. Provider calls use provider idempotency tokens where supported. HTTP keys are not reused as broker delivery IDs.

## Failure Behavior

| Situation | Result |
| --- | --- |
| Same key, same request, complete record | Replay with `Idempotency-Replayed: true`. |
| Same key, different fingerprint | `409 IDEMPOTENCY_KEY_REUSED`; no execution. |
| Same key currently executing | `409 IDEMPOTENCY_IN_PROGRESS` plus `Retry-After`. |
| Winner crashes before commit | All state rolls back; retry may execute. |
| Commit succeeds but response is lost | Retry replays committed response. |
| External async dependency is down | Business transaction and outbox may commit; accepted status exposes pending delivery. |
| Stored response cannot be serialized | Transaction rolls back; no business change. |
| Caller lost tenant membership | Current authorization failure; no replay body disclosure. |

## Verification

Integration tests use real PostgreSQL and concurrent requests to prove one business effect, one outbox event, response replay, fingerprint conflicts, lock release after cancellation/crash, transaction rollback, authorization-before-replay, expiry policy, and safe header behavior. Contract tests prove every required OpenAPI operation declares the header and documented `409` responses.
