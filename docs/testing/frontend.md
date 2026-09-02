# Proposed Frontend Testing Strategy

## Purpose And Status

This document defines planned verification for the Next.js App Router, React, strict
TypeScript, generated OpenAPI client, TanStack Query, forms, permission-aware UX, and
accessibility. It complements the [frontend architecture](../architecture/frontend.md)
and [E2E strategy](e2e.md). No frontend test runner is configured yet.

The proposed M0 default is Vitest, React Testing Library, `@testing-library/user-event`,
MSW at the HTTP boundary, and automated `axe-core` checks. The compatibility spike
must confirm the selected Next.js/React versions, Server Component boundaries, fake
timers, ESM, and coverage behavior before versions are pinned. A different runner may
be selected if that evidence fails; the behaviors below remain mandatory.

## Test Layers

| Layer | Scope | Boundary to fake | CI placement | Release signal |
| --- | --- | --- | --- | --- |
| Static | Strict TypeScript, lint, route/import rules, generated-client drift, Tailwind/build constraints | None | Every pull request | Any error or generated drift blocks merge |
| Pure unit | Query-key factories, view-model formatting, Zod UI coercion, permission projection, date/money presentation | Fixed clock/locale and typed DTO builders | Every pull request | All changed branches and risk cases pass |
| Component | Accessible controls, forms, dialogs, tables/cards, loading/empty/error/success, optimistic rollback | HTTP response through MSW only when needed | Every pull request | User-observable behavior and automated accessibility pass |
| Feature integration | Route composition, generated client/runtime, TanStack Query, session/organization context, server/client hydration | HTTP boundary or local backend; never mock the generated client itself | Every pull request, sharded | Tenant-safe cache/auth/error behavior passes |
| Browser E2E | Real web/API/database/OIDC and critical workflows | Only external provider test adapters | Changed-journey PR smoke, merge/release suite | Critical journey and accessibility failures block promotion |

## Component And Form Coverage

Use semantic role, accessible name, label, and visible text queries; `data-testid` is
a narrow fallback for an element with no stable user-facing semantic. Test user
events, focus, and announcements rather than calling component callbacks directly.

Required component cases include:

- initial loading, background refresh, empty collection, no filter matches, partial
  data, safe error with request ID, offline/transient retry, forbidden, concealed not
  found, rate-limited countdown, conflict/precondition, destructive confirmation,
  and success states;
- form required/conditional fields, server error pointer mapping, focus on the error
  summary, draft preservation after safe failures, duplicate-submit prevention, and
  no preservation of authentication secrets;
- invoice decimal/minor-unit display and server-confirmed totals; timer controls that
  remain pending until the server confirms start/stop; no optimistic success for
  invoice, membership, timer, file, or destructive actions;
- reversible optimistic task assignment/status and notification-read updates,
  including full snapshot rollback and server reconciliation;
- permission projections for every capability: discoverable allowed action, hidden
  unauthorized action, state-disabled explanation, and graceful handling when a
  formerly allowed server request returns `403`;
- dialog focus trap/return, live-region announcements, keyboard alternatives to
  drag-and-drop, table headers/captions, chart text/table equivalents, reduced motion,
  and status that is not color-only.

Zod tests cover UI coercion and conditional guidance only. Server-owned domain rules,
invoice totals, timer uniqueness, permissions, and tenant ownership are asserted from
API responses, not duplicated as a competing frontend authority.

## Feature Integration Tests

MSW intercepts documented HTTP operations and returns examples validated against
OpenAPI. The generated endpoint and runtime adapter remain real. Integration tests
prove:

- explicit `organizationId` path arguments and query keys shaped as
  `['organization', organizationId, ...]`; a slug or header never becomes authority;
- organization switching cancels in-flight requests, removes the prior tenant cache,
  resets local feature state, resolves current membership, and does not display a
  late response from the previous tenant;
- logout, `401`, session expiry, and principal changes clear all sensitive query and
  identity state; `403` retains the session but removes stale capability assumptions;
- generated errors preserve status/code/request ID, `Retry-After`, `ETag`, and
  idempotency behavior without branching on human message text;
- only transient idempotent reads receive bounded automatic retry; mutations are not
  replayed secretly, and caller-owned idempotency keys remain stable across an
  explicit safe retry;
- `AbortSignal` reaches fetch on navigation, superseded queries, and unmount;
- server prefetch uses a request-scoped QueryClient, serializes no provider token or
  server object, hydrates once, and does not leak cache data between requests;
- cursor/filter/sort state remains URL-backed and opaque; back navigation restores
  known cursors instead of decoding or inventing them;
- server and client runtime adapters use the same error/tenant contract and forward
  only allowlisted cookies/request context.

Direct negative fixtures return another organization's identically shaped resource,
cursor, file, or error timing. The UI must render the generic not-found/forbidden
contract and must never expose foreign names, identifiers, cached rows, or object URLs.

## Authentication And Authorization Cases

The local identity adapter exposes the production-facing redirect/callback/session
contract. Tests cover valid Authorization Code + PKCE completion, returned-state and
nonce mismatch, wrong issuer/audience, expired code/session, callback provider error,
safe return-path validation, centralized refresh without a storm, revocation, and
logout cleanup.

Browser-readable storage is inspected to ensure it contains no access/refresh token,
opaque session secret, CSRF secret, invitation token, presigned URL, or persisted
tenant query cache. Cookie flags that JavaScript cannot inspect are proven at the HTTP
and Playwright boundary. UI role names never substitute for named capability checks,
and every stale permission outcome is handled as a server-authoritative result.

## Responsive And Accessibility Matrix

Component integration covers narrow phone, tablet, standard laptop, and wide desktop
layout contracts with stable mocked viewport capabilities. Playwright validates the
critical workflows at desktop and mobile viewports. Required assertions include:

- no clipped primary action or horizontal page trap; tables have a usable labeled
  narrow-screen representation;
- keyboard-only navigation, visible focus, logical heading/landmark order, skip link,
  dialog escape/return focus, and usable board alternatives;
- 200% zoom/reflow where automated browser checks are reliable, reduced motion, touch
  targets, contrast, live announcements, and meaningful error focus;
- automated accessibility scan with zero serious/critical violations on critical
  states, followed by manual keyboard and screen-reader review before production.

Snapshot tests are limited to small stable serialized structures or intentional
visual baselines. Broad DOM snapshots do not replace semantic assertions. Visual
regression, if adopted, uses reviewed desktop/mobile baselines for high-value layout
and never auto-accepts a changed image.

## Fixtures And Determinism

- Typed builders consume generated DTOs and require explicit tenant/resource IDs;
  they do not redeclare transport interfaces.
- MSW response examples are generated or checked against the bundled OpenAPI schema.
  A handler without a matching operation ID is a contract failure.
- Test QueryClients disable uncontrolled retries, receive fixed defaults, and are
  new per test. Server-render tests create a new cache per simulated request.
- Clock, locale, IANA zone, browser online state, `Retry-After`, and idempotency UUID
  generation are injected or controlled, then restored after each test.
- Console errors and unhandled rejections fail the test unless an exact expected
  message is asserted. Network handlers default to error on unexpected requests.
- Role/tenant fixtures match the canonical builders in [strategy](strategy.md); no
  suite shares one administrator storage state as a convenience.

## Performance Checks At The Frontend Boundary

Production readiness requires route-group bundle budgets, Core Web Vitals targets,
and server-render/API waterfall inspection based on representative builds. PR checks
compare changed route bundles to an approved baseline and flag material growth;
scheduled browser runs measure navigation/rendering with production minification and
realistic list sizes. A budget change requires cause, user impact, and approval rather
than silently rebasing the threshold.

Browser telemetry tests prove that route/error metrics keep bounded labels and exclude
tokens, cookies, form values, invoice/file details, email, and raw tenant/resource IDs.
Collector or reporting failure cannot break rendering or user actions.

## CI Placement And Release Signal

| Stage | Frontend checks | Blocking signal |
| --- | --- | --- |
| Pull request | Lint, strict typecheck, generated drift, unit/component/feature integration, automated accessibility, production build; changed critical Playwright smoke | Any contract/type/accessibility/behavior failure, unexpected request, console error, or unexplained flake blocks merge |
| Main/nightly | Full integration and browser matrix, responsive/accessibility projects, bundle comparison, scheduled dependency scan | Regression blocks the release candidate; retry-only passes remain defects |
| Release candidate | Same immutable frontend digest with real API/OIDC adapters in staging; all critical journeys, manual keyboard/screen-reader review, web-vitals/bundle budgets | No critical journey, cross-tenant cache, session, accessibility, or performance gap |
| Post-deploy | Bounded login/public shell/authorized read smoke and web/API telemetry sanity | Failure pauses promotion or triggers the documented rollback; no destructive browser test runs by default |

The final signal is that a user can understand and complete each authorized workflow
and safely recover from each expected failure. Component coverage alone cannot waive
missing real-session, cross-tenant, or critical Playwright evidence.
