# Proposed API Error Contract

## Purpose

This document defines the stable, client-safe error representation for ClouDesk. Internal causes, SQL details, provider responses, stack traces, and sensitive identifiers are logged under access controls and are never copied into this contract.

## Envelope

```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "The request contains invalid fields.",
    "requestId": "01K...",
    "details": [
      {
        "pointer": "/dueDate",
        "code": "DATE_BEFORE_ISSUE_DATE",
        "message": "Due date must not be before issue date."
      }
    ]
  }
}
```

- `code` is a stable machine-readable uppercase identifier. Clients branch on it, not on `message`.
- `message` is safe human-readable fallback text and is not a localization key contract.
- `requestId` is the server-selected correlation value returned in `X-Request-ID`.
- `details` is optional and bounded. Field locations use JSON Pointer for bodies and documented prefixes such as `/query/limit`, `/path/projectId`, or `/headers/If-Match` elsewhere.
- A detail never reveals whether an inaccessible resource exists in another tenant.

Every error response uses `application/json` and this envelope, including gateway-originated responses where ClouDesk controls the gateway template. Empty HTML proxy errors are treated as an operational defect.

## Status And Code Mapping

| Status | Representative codes | Meaning and retry behavior |
| --- | --- | --- |
| `400` | `MALFORMED_JSON`, `VALIDATION_FAILED`, `INVALID_CURSOR`, `INVALID_FILTER` | Request shape/parameters are invalid; change the request. |
| `401` | `AUTHENTICATION_REQUIRED`, `TOKEN_INVALID`, `TOKEN_EXPIRED` | No valid principal. A client may refresh once through the identity flow, never loop. |
| `403` | `PERMISSION_DENIED` | Authenticated tenant member lacks a permission for a known scope. |
| `404` | `RESOURCE_NOT_FOUND`, `ORGANIZATION_NOT_FOUND` | Missing or deliberately concealed inaccessible tenant/resource. |
| `409` | `STATE_CONFLICT`, `ACTIVE_TIMER_EXISTS`, `IDEMPOTENCY_KEY_REUSED`, `IDEMPOTENCY_IN_PROGRESS` | Current committed state conflicts with the command. Retry only as documented. |
| `412` | `VERSION_MISMATCH` | `If-Match` is stale; refetch and reconcile. |
| `415` | `UNSUPPORTED_MEDIA_TYPE` | Use the documented request media type. |
| `422` | `BUSINESS_RULE_VIOLATION` | Structurally valid request violates a domain rule; details explain safe corrections. |
| `428` | `PRECONDITION_REQUIRED` | Required `If-Match` or equivalent precondition is absent. |
| `429` | `RATE_LIMITED` | Retry no earlier than `Retry-After`; use jitter. |
| `500` | `INTERNAL_ERROR` | Unexpected server fault; caller may retry only if the operation is idempotent. |
| `503` | `DEPENDENCY_UNAVAILABLE`, `SERVICE_UNAVAILABLE` | Temporary inability to serve; use `Retry-After` and bounded retry. |
| `504` | `DEPENDENCY_TIMEOUT` | A required downstream deadline expired; outcome may be unknown unless idempotency applies. |

This table is finite at the shared level; domain-specific error codes are declared on each OpenAPI operation. A new code under an existing status is reviewed for generated-client compatibility.

## Authorization Disclosure Rules

- Invalid, absent, expired, or revoked application sessions return `401` with a generic reauthentication challenge; a future service bearer contract follows the same safe-error rule.
- A principal that is not an active member of the route organization receives `404 ORGANIZATION_NOT_FOUND`.
- A member who can establish the tenant context but lacks an action permission receives `403 PERMISSION_DENIED`.
- A resource ID absent from the authorized tenant and a resource ID belonging to another tenant produce the same `404 RESOURCE_NOT_FOUND` response and comparable timing where practical.

Logs may record the internal reason and protected identifiers, but API messages do not expose another tenant's existence.

## Validation Details

The server returns multiple independent validation details only up to a small documented cap; it does not echo entire invalid values. Malformed JSON that prevents reliable field traversal returns one top-level detail. Domain validation and database constraint mapping use the same safe pointers and stable codes when possible.

Examples of prohibited detail content include SQL constraint names, provider account IDs, bearer claims, object-store keys, stack traces, and raw email-provider responses.

## Cancellation, Timeouts, And Unknown Outcomes

A disconnected client may result in no consumable response; server telemetry records cancellation separately from a server error. When the server still has a connection and its own request deadline expires, it returns the closest controlled timeout response available.

For a non-idempotent operation, a timeout can leave outcome uncertainty and clients must refetch state. Sensitive mutations require [idempotency](idempotency.md), allowing a retry with the same key and request to replay or complete the authoritative outcome.

## Logging And Metrics

The HTTP boundary records the stable error code, status, route template, request/trace ID, organization ID when authorized, duration, and wrapped internal cause according to data policy. It does not log request bodies by default. Expected 4xx responses contribute labeled request metrics but are not error-level stack traces; 5xx and repeated dependency failures trigger operational signals with bounded-cardinality labels.
