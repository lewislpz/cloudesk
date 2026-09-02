# Proposed Structured Logging And Redaction

## Purpose And Status

This document defines the planned application and platform logging contract for
ClouDesk. It is not implemented. Logs are diagnostic records; security and financial
audit facts remain append-oriented PostgreSQL records described by the audit domain.
The transport and backend topology is defined in [observability](observability.md).

## Log Event Contract

Applications write one UTF-8 JSON object per line to stdout/stderr. Collectors add
trusted Kubernetes/cloud metadata and route the event. The application owns semantic
fields and redaction before serialization.

| Field | Rule |
| --- | --- |
| `timestamp` | RFC 3339 UTC with sub-second precision, generated at the event source |
| `severity` | `DEBUG`, `INFO`, `WARN`, or `ERROR`; `FATAL` only immediately before process exit |
| `message` | Stable human summary without interpolation of customer data or raw dependency errors |
| `service`, `environment`, `release` | Low-cardinality resource identity |
| `request_id` | Validated/generated opaque correlation ID for an HTTP boundary; never a metric label |
| `trace_id`, `span_id` | Added from the active sampled or valid OTel context |
| `event_id`, `correlation_id`, `causation_id` | Async identifiers where applicable; never payload content |
| `organization_id` | Internal immutable UUID only when needed for authorized diagnosis; never organization name/slug and never a metric label |
| `actor_id` | Omit by default; use an internal ID only for a reviewed security/operations event |
| `route`, `method`, `status`, `duration_ms` | Route template, not raw URL; server-measured outcome |
| `operation`, `job_class`, `queue` | Bounded vocabulary defined by the owning adapter |
| `error_code` | Stable application/operations code; no raw database/provider message |
| `retryable`, `attempt` | Explicit retry classification and bounded attempt count where relevant |

Field names and types are versioned as a shared schema. An existing field is not
silently repurposed. Unknown top-level fields are rejected in tests and dropped or
quarantined at the collector until reviewed.

Illustrative safe event:

```json
{
  "timestamp": "2026-09-01T10:15:30.123Z",
  "severity": "WARN",
  "message": "worker attempt failed",
  "service": "clouddesk-notification-worker",
  "environment": "staging",
  "release": "sha256:example",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "event_id": "0191c5d4-7d42-7a25-90c4-3b6cf35d5af1",
  "organization_id": "0191c5b0-44df-7f42-b6e6-2de70ab86a42",
  "queue": "notifications",
  "operation": "email_delivery",
  "error_code": "PROVIDER_UNAVAILABLE",
  "retryable": true,
  "attempt": 2
}
```

The example identifiers are synthetic. Real payloads, addresses, message bodies, and
provider responses are excluded.

## Severity And Event Ownership

- `DEBUG`: short-lived diagnostic detail, disabled in production by default and
  sampled when enabled. It is never a way to bypass redaction.
- `INFO`: lifecycle, completed boundary, controlled state transition, deployment,
  and low-volume operational event. Routine successful HTTP requests may be sampled
  if complete metrics exist.
- `WARN`: recoverable degradation, bounded retry, rejected unsafe input, rate/load
  shedding, or approaching a capacity/recovery threshold.
- `ERROR`: an operation failed at its owning process boundary, an invariant was
  violated, or operator action is required. Expected validation, not-found,
  permission, conflict, and cancellation outcomes are not error logs.

An error is logged once by the boundary that owns the outcome: HTTP middleware,
message handler/dispatcher, process supervisor, migration job, or controller. Lower
layers wrap/classify it and add span events but do not each emit a duplicate stack.
Retries record one bounded attempt event and one terminal outcome; they do not flood
logs on every SDK sub-attempt.

## Data Classification And Prohibited Content

The following are prohibited in every severity, trace event, collector diagnostic,
test artifact, alert, and dashboard annotation:

- passwords, MFA values, API keys, access/refresh/ID tokens, session cookies, CSRF
  tokens, OIDC codes, AWS credentials, database credentials, and secret values;
- authorization headers, cookie headers, unfiltered HTTP headers, request/response
  bodies, SQL bind values, event/message bodies, and Terraform state/plan content;
- presigned S3 URLs, object keys containing customer-derived names, SQS receipt
  handles, email bodies/addresses, invoice lines/tax identifiers, file names/content,
  comments, task descriptions, notes, physical addresses, and other unnecessary PII;
- raw URL paths or query strings containing organization slugs, resource IDs,
  cursors, search terms, return URLs, or tokens; and
- raw stack/dependency error text when it can contain SQL, endpoints, paths, payloads,
  or credentials.

Internal `organization_id` is **Confidential** operational metadata. It is allowed
only in restricted server logs/traces where tenant-scoped diagnosis or incident
containment needs it, with access/audit controls and short retention. Browser
telemetry, public errors, metrics, alerts, dashboard variables, and notification
destinations must not expose it. `user_id` is omitted unless a security runbook has a
specific need; use the audit system for actor history.

## Defense-In-Depth Redaction

Redaction happens at four independent boundaries:

1. **Construction:** call sites use typed fields and allowlisted request/dependency
   summaries. Logging arbitrary structs, maps, DTOs, exceptions, headers, SQL, or
   `%+v` dumps is prohibited.
2. **Application logger:** sensitive field names are denied, URL values are reduced
   to route/host class, and errors are converted to stable codes plus safe diagnostic
   categories.
3. **Collector gateway:** processors remove denylisted keys/patterns and any unknown
   browser attribute. This is a backstop, not permission to emit secrets.
4. **Backend policy:** log-group access, retention, export, saved queries, and alert
   templates prevent broad redisclosure. Break-glass reads are time bounded and
   audited.

When detection finds a secret/PII leak, stop the emitting path if safe, restrict the
affected log group, preserve only necessary incident evidence, expire/delete copies
according to provider and legal capability, rotate exposed credentials, and add a
regression fixture. Redaction after ingestion does not make the original exposure
harmless.

## HTTP, Database, Async, And Security Events

### HTTP

One boundary event records method, route template, status, duration, response size
class, request ID, and stable error code. It excludes bodies and raw paths. Health
probe successes and static assets are dropped or heavily sampled; their failures
remain metrics. A client-provided request ID is accepted only after length/character
validation, otherwise replaced.

### PostgreSQL

Record operation class, normalized query name/fingerprint, duration, rows-affected
class, transaction outcome, pool wait, SQLSTATE class when safe, and error code. Never
log SQL bind values or result rows. Slow-query detail comes from protected RDS/
`pg_stat_statements` evidence with sanitized fingerprints.

### Outbox, SQS, And Workers

Record event ID, event type/version, queue, consumer, attempt, duration, retry class,
visibility action, inbox outcome, and durable result. Do not log envelope payload or
receipt handle. Duplicate inbox acceptance is an `INFO` metric-bearing outcome;
metadata mismatch, tenant mismatch, or unsupported version is an integrity/security
`ERROR` with quarantine reference but no payload.

### Security

Authentication failures, rate-limit decisions, authorization denials, session
revocation, role changes, and cross-tenant attempts use stable reason classes and
privacy-safe network categories. They never reveal whether another tenant/resource
exists. High-volume hostile activity is aggregated/rate-limited before logs can
become an availability or cost attack. Required audit facts are committed to
PostgreSQL, not inferred later from sampled logs.

## Retention, Access, And Integrity

Concrete retention days are selected with legal, privacy, incident-response, and cost
owners before production. The initial operating proposal is short retention for
debug/access logs, longer retention for warning/error and security-control logs, and
separate immutable organization audit retention. Non-production is shorter and uses
synthetic data.

Access uses least-privilege roles: application developers query non-production;
production application logs require an operational role; security log groups require
a narrower security role. Queries and exports are attributable. Logs must not be
downloaded to unmanaged devices or copied into chat/issues. Cross-account archival,
if adopted, is encrypted and retains the same classification/deletion obligations.

## Verification

Before staging and production, automated tests must:

- parse every representative log as the schema and assert field types;
- inject synthetic secrets, tokens, cookies, emails, names, SQL values, presigned
  URLs, event bodies, and stack errors and prove none reaches collector output;
- prove route templates replace raw tenant/resource paths and query strings;
- prove expected `4xx`, cancellation, duplicate messages, retries, and terminal
  failures use the intended severity and are logged once;
- verify trace/request/event correlation works with sampled and unsampled traces;
- load-test hostile/high-volume error paths and demonstrate sampling/rate limits do
  not hide required counters or exhaust storage; and
- run a log-leak incident drill including access restriction, rotation, purge
  limitations, notification, and regression evidence.

