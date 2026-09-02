# Proposed End-To-End Testing

## Purpose And Status

This document defines the planned Playwright suite for ClouDesk. It proves a small
set of user-critical journeys across Next.js, the generated client, Go API,
PostgreSQL, local OIDC, and required queue/object adapters. It does not replace
[backend](backend.md), [frontend](frontend.md), or
[integration](integration.md) coverage, and no browser suite exists yet.

## Environment And Fixtures

Playwright uses an isolated migrated database and deterministic builders from the
[quality strategy](strategy.md). Each parallel worker receives unique users,
organizations, queues/object prefixes, and browser storage. Storage state is created
per role and organization; suites never share one administrator session.

The base fixture contains organizations A and B, a multi-organization user, A-only
and B-only users, all canonical roles, suspended/revoked memberships, similarly
named foreign resources, active/draft/issued records, and controllable provider
states. Setup APIs are restricted to test environments. Clocks and time zones are
explicit; cleanup verifies the test target before deleting only run-owned data.

Selectors prefer role, name, label, and visible state. Unexpected console errors,
page errors, failed requests, or unhandled dialogs fail the test. Traces, screenshots,
video, and sanitized network logs are retained on first failure/retry without cookies,
tokens, idempotency keys, presigned URLs, form contents, or customer-like PII.

## Critical Journey Matrix

| Journey | Required assertions | Negative/concurrent case | CI placement and signal |
| --- | --- | --- | --- |
| Login/onboarding/logout | OIDC callback, secure app session, organization creation, cache/session cleanup | Invalid state/nonce, expired/revoked session, safe return path | PR smoke from M1; any failure blocks merge/promotion |
| Organization switch/team | Correct membership/capabilities and cache replacement | Late A response after switch to B, suspended member, direct foreign URL | Full merge/release suite; no foreign content or unsafe action |
| Clients/projects/tasks | Create/list/filter/detail/update, accessible states and cursor navigation | Foreign IDs/parents, stale `If-Match`, role downgrade, optimistic rollback | Changed-journey PR smoke; contract and recovery pass |
| Time tracking | Start, persistent active state, stop, UTC/time-zone display | Two contexts start/stop concurrently, duplicate retry, two organizations for same user | Release-blocking from M5; exactly one active timer/effect |
| Invoicing | Draft from time/manual lines, totals, review, issue, PDF pending state, void rules | Same time entry in competing drafts, concurrent issue/stale version, same-key replay | Release-blocking from M6; one number/snapshot/outbox effect |
| Files | Request upload, direct transfer, completion, authorized download/quarantine | Foreign owner, expired URL, wrong size/type/checksum, deleted object | Release-blocking when files enabled; no usable unauthorized URL |
| Notifications/reports | In-app result, export accepted/polled/downloaded, truthful async failure | Provider failure, bounded report range, foreign export/file | Full/release suite; source fact survives provider failure |
| Permissions/session | Capability-aware UI plus API-authoritative denial | Direct request despite hidden action, last-owner rule, permission revoked mid-flow | Every protected feature; safe `403`/concealed `404` |

Direct API calls through Playwright's authenticated request context complement UI
navigation for IDOR, CSRF, idempotency, and authorization cases. They reuse the same
session/tenant fixture but never treat a hidden control as security evidence.

## Accessibility And Responsive Projects

Critical journeys run at desktop and narrow mobile viewports with automated
accessibility scanning. They assert keyboard-only completion, visible focus,
heading/landmark order, dialog escape and focus return, live announcements for timer
and mutation state, labeled tables/forms, non-color status, and a non-drag task
alternative. Before production, manual keyboard and screen-reader review covers
login, tenant switching, timer, invoice issue, file handling, and error recovery.

Cross-browser coverage starts with Chromium in PR, then Chromium, Firefox, and WebKit
on nightly/release candidates when supported. Browser-specific failure is a defect,
not waived by the primary browser.

## Determinism And Flakes

Tests wait on visible UI, documented response, durable status, or bounded condition
polling—never arbitrary sleeps. Async polling fixtures expose controlled transitions.
Retries are at most diagnostic: a test passing only on retry remains failed quality
evidence and needs an owner. No journey depends on order, shared mutable data, real
email delivery, or uncontrolled wall time.

## Pipeline And Production Gate

- **Pull request:** Chromium smoke for a changed critical journey plus static,
  component, and integration prerequisites.
- **Main/nightly:** sharded full journey, role/tenant, responsive, accessibility, and
  browser matrix.
- **Release candidate:** same immutable web/API digest and migrations in staging,
  real production-class routing/session/workload identity, all critical journeys and
  manual accessibility evidence.
- **Production:** bounded non-destructive public/login/read smoke only; no invoice,
  file, tenant, or destructive mutation by default.

Promotion is blocked by a critical journey failure, cross-tenant disclosure,
incorrect durable invariant, serious/critical accessibility defect, secret-bearing
artifact, or unresolved flake. A broad passing E2E suite cannot waive a missing
repository, contract, load, failover, or restore gate.
