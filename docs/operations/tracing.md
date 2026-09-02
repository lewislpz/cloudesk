# Proposed Distributed Tracing

## Purpose And Status

This document defines ClouDesk's planned trace propagation and span model across the
browser, Next.js, Go API, PostgreSQL, outbox, SQS, workers, S3, and providers. It is a
design, not evidence of instrumentation. [ADR-018](../decisions/ADR-018-opentelemetry-observability.md)
selects OpenTelemetry; [observability](observability.md) owns collection and backends.

## Propagation Contract

W3C Trace Context (`traceparent` and `tracestate`) is the only distributed trace
propagator. W3C Baggage is disabled by default because it is easy to propagate PII,
tenant identity, or high-cardinality data accidentally. Request, event, correlation,
and causation IDs remain explicit application fields and are not smuggled through
baggage.

| Boundary | Injection and extraction rule |
| --- | --- |
| Browser to same-origin Next.js/API | Browser may inject valid W3C headers only for ClouDesk same-origin destinations. Never inject into presigned S3, Cognito, email/provider, or arbitrary links. |
| Next.js server to Go API | Extract incoming remote context, start a server span, and inject the active context through the generated client's allowlisted headers. |
| Go HTTP ingress | Validate header size/format; invalid or excessive context is discarded and a new root starts. Trace context never affects authentication, authorization, tenant selection, or sampling cost without local limits. |
| API/publisher to PostgreSQL | Context is process-local through `context.Context`; DB spans do not serialize trace state into business rows except the explicit trace/correlation fields required by audit/outbox contracts. |
| Outbox to SQS | Publisher injects current valid context into SQS message attributes, not the JSON business payload. The immutable event envelope still carries event/correlation/causation IDs. |
| SQS to worker | Consumer extracts valid attributes, creates a new consumer/processing span and links it to the producer span/context. Invalid context starts a new trace and retains explicit safe correlation IDs. |
| Worker to AWS/provider | Inject only where the owned protocol supports trace headers and the receiving party is approved. Do not put trace headers in presigned URLs or customer-visible content. |

Trace IDs received from a client are untrusted opaque values. Rate limiting and head
sampling prevent an attacker from forcing all traces to be retained. Servers use
fresh span IDs and never accept externally supplied request/event IDs without their
own validation policy.

## Why Async Work Uses Links

An SQS message may wait minutes, be retried, be duplicated, or be replayed after the
original trace retention window. Pretending this is one synchronous child chain
distorts latency and may create an indefinitely long trace. The source request span
ends after the business state and outbox rows commit. Publication and each processing
attempt are separate traces/spans with links to the producer and, when available, to
the previous attempt.

```mermaid
sequenceDiagram
    actor Browser
    participant Web as Next.js
    participant API as Go API
    participant DB as PostgreSQL + outbox
    participant Relay as Outbox publisher
    participant SQS
    participant Worker
    participant S3

    Browser->>Web: action + traceparent
    Web->>API: generated API call + traceparent
    API->>DB: business transaction + outbox event
    DB-->>API: COMMIT
    API-->>Browser: committed result + request ID
    Note over API: source request span ends
    Relay->>DB: claim delivery
    Relay->>SQS: publish + trace context message attributes
    Note over Relay: publication trace links to source/event context
    SQS-->>Worker: at-least-once delivery
    Note over Worker: processing span links to producer; attempt is explicit
    Worker->>DB: inbox + durable effect/intent
    Worker->>S3: optional idempotent effect
    Note over Worker,SQS: retry/replay creates a new attempt span with same event ID
```

The event ID answers “which durable fact?”, correlation ID answers “which user/domain
workflow?”, causation ID answers “what immediately caused it?”, and trace/span IDs
answer “which observed execution attempt?”. They are not interchangeable.

## Span Model

| Component | Required spans | Avoid |
| --- | --- | --- |
| Browser | navigation/route group, selected critical user action, fetch where safe, rendering error | Every click, DOM content, arbitrary URL, third-party calls, session replay |
| Next.js | server request/render, generated API call, safe telemetry intake | One span per React component or serialized props |
| Go API | HTTP server, meaningful application use case, pgx transaction/query, S3/SQS/OIDC adapter | Helper-function spans, request/response bodies, SQL values |
| Outbox publisher | claim batch, individual/batch publish result, acknowledgement | One span per polling sleep or high-volume successful row cleanup |
| Worker | receive batch, processing attempt, inbox/effect transaction, durable external intent/dispatch | Making one long span across visibility waits and retries |
| Platform | ALB/ingress correlation where available, collector export | Fabricated child relationships when no context exists |

Span names are low-cardinality templates such as `HTTP GET /api/v1/organizations/{organizationId}/projects`,
`invoice.issue`, `outbox.publish notifications`, and `worker.process documents`.
Resource IDs, tenant slugs, invoice numbers, SQL text, object keys, and raw URLs never
appear in names.

## Attributes, Events, Status, And Errors

Use stable OTel semantic conventions where they match the runtime version and a
ClouDesk-owned namespace for domain attributes. Safe dimensions include service,
environment, release, route template, method, response status, stable error code,
database operation/query fingerprint, queue, event type/version, consumer, job class,
attempt, duplicate/new inbox outcome, and retry classification.

`organization_id`, request ID, event ID, correlation ID, and causation ID may be span
attributes only in the restricted server-side trace store and only when necessary for
diagnosis. They are never indexed as metric dimensions unless the backend can enforce
a non-series searchable field with equivalent access policy. Browser spans omit
tenant/user IDs.

Expected validation, authorization, not-found, conflict, cancellation, and rate-limit
outcomes record their status/error code but do not automatically set exception status.
Unexpected server failure, failed durable effect, integrity mismatch, or exhausted
retry marks the owning span as error. Exception events contain the typed safe error
category; raw provider/database messages and stack locals are excluded.

## Sampling And Trace Completeness

Sampling is parent-based and deterministic. Local/staging retains enough traffic to
verify topology. Production begins with a cost-tested baseline and reviewed higher
rates for low-volume critical workflows. An external sampled flag is subject to
local policy, so a caller cannot force storage cost.

Metrics and logs are the complete SLO/error source because head sampling can drop an
error trace. Trace search pages show sampling rate and warn that absent spans do not
prove an absent call. Tail sampling is introduced only after a capacity test proves
consistent trace routing, bounded decision wait, failure behavior, and cost; it must
not delay application traffic.

Broken/missing propagation increments a low-cardinality counter by boundary and is
tested. A trace with missing downstream spans is marked incomplete by telemetry
pipeline signals rather than silently interpreted as success.

## Special Failure Cases

- **Unknown database commit outcome:** end the attempt with an ambiguous outcome;
  retry under the same idempotency key creates a new span linked by request/domain
  correlation. Do not rewrite the first span as rollback or success without evidence.
- **Duplicate SQS delivery:** create a new processing-attempt span; inbox result is
  `duplicate`, and both attempts share event/correlation IDs.
- **DLQ redrive:** create a new replay attempt, preserve the event ID, link to any
  retained producer context, and add a sanitized replay change/ticket reference.
- **Collector/backend outage:** SDK export fails within a bounded timeout, increments
  internal drop/export metrics where possible, and never changes HTTP/message result.
- **RDS failover:** failed connections/transactions show explicit error spans;
  reconnect attempts use new spans with jitter, not one misleading operation.
- **Presigned transfer:** the browser-to-S3 byte flow is intentionally not traced by
  propagating headers. ClouDesk correlates authorized metadata intent and later
  completion/reconciliation using the file's internal state and safe request IDs.

## Verification

Future integration tests must use a capture collector and assert:

- browser context reaches only the same-origin ClouDesk path and invalid/oversized
  headers create a safe new root;
- Next.js-to-Go parentage, request ID, route templates, cancellation, and sampled flag
  behave as designed;
- pgx and AWS spans contain normalized operations without SQL values, event payloads,
  S3 keys, tokens, presigned URLs, or customer data;
- outbox/SQS attributes preserve valid context, each worker attempt uses a link, and
  duplicate/replay attempts remain distinguishable by the same event ID;
- tenant/resource IDs do not enter span names, browser spans, metric labels, or public
  error details;
- sampling approximates configured rates and malicious client flags cannot bypass
  the local cap; and
- collector loss, gateway restart, full queue, export timeout, and shutdown remain
  bounded and do not change application availability or durable work.

