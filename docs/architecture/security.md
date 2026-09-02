# Proposed Security Architecture And Threat Model

## Purpose And Scope

This document defines ClouDesk's proposed security posture across browser, API,
PostgreSQL, asynchronous workers, S3, AWS, Kubernetes, delivery, and operations. It
is a design and verification contract, not a claim that controls are deployed.

The primary assets are tenant business data, membership and permission state,
identity/session material, invoices and files, audit evidence, AWS resources,
database backups, build artifacts, and service availability. Security decisions are
aligned with [multi-tenancy](multi-tenancy.md), [ADR-011](../decisions/ADR-011-amazon-cognito-oidc.md),
and [ADR-012](../decisions/ADR-012-bounded-redis-usage.md).

## Security Principles

- Authenticate at the edge of every protected flow and authorize every operation in
  the application use case; deny by default.
- Treat route IDs, tokens, cookies, headers, JSON, file metadata, event payloads,
  provider responses, and logs as untrusted input.
- Keep PostgreSQL authoritative for business, membership, idempotency, audit, and
  application-session state. Redis is optional and reconstructible.
- Use established OIDC/OAuth, TLS, AWS, and cryptographic libraries; ClouDesk does not
  invent identity or encryption protocols.
- Apply least privilege to users, database roles, workloads, queues, buckets, CI, and
  human operators. Separate identities by process responsibility.
- Fail closed for authentication, authorization, tenant selection, upload validation,
  and security-sensitive abuse controls. Optional cache/provider outages must not
  trigger unsafe fallback.
- Minimize sensitive data, retention, response detail, log content, metrics
  cardinality, and access duration.
- Make security-relevant actions observable and auditable without placing secrets or
  unnecessary personal data in telemetry.

## Actors, Entry Points, And Trust Boundaries

| Actor | Legitimate authority | Principal abuse concern |
| --- | --- | --- |
| Anonymous internet user | Public web and login initiation only | Enumeration, credential attacks, flooding, malicious inputs |
| Organization member | Permissions of one active membership at a time | IDOR, cross-tenant access, workflow abuse |
| Owner/admin/manager | Explicit privileged capabilities in one tenant | Privilege escalation, destructive or fraudulent action |
| Go API and workers | Narrow service/database/IAM grants | Confused deputy, compromised workload, cross-tenant job |
| Identity/email providers | Contracted identity or delivery response | Forged callback, dependency compromise, sensitive error leakage |
| CI/CD and platform operator | Build/deploy or bounded production operations | Supply-chain compromise, secret exposure, overbroad access |
| Database/cloud administrator | Exceptional infrastructure administration | Insider access, audit tampering, excessive break-glass use |

Trust boundaries exist between the internet and CloudFront/WAF, browser and
same-origin application, web/session boundary and Go API, API and OIDC provider,
application and PostgreSQL/Redis/S3/SQS, queues and workers, workloads and AWS IAM,
CI and cloud accounts, and production telemetry and its readers. Authentication at
one boundary never implies authorization at the next.

## Authentication And Session Architecture

Amazon Cognito is the production identity target through standard OIDC/OAuth 2.0,
as selected by [ADR-011](../decisions/ADR-011-amazon-cognito-oidc.md). ClouDesk maps
the stable `(issuer, subject)` pair to a local user. Email, display name, groups, and
client-supplied organization claims are attributes, not tenant authority. Cognito
owns passwords, recovery, federation, and authentication challenges; ClouDesk owns
application sessions, memberships, roles, and permissions.

The browser flow uses Authorization Code with PKCE, `state`, and `nonce`. The
application callback validates exact redirect URI, state, nonce, issuer, audience,
authorized algorithm, code, token type, signature, expiry, and clock skew through a
maintained OIDC library. Implicit flow and password grant are prohibited.

The browser receives only an opaque, rotated application-session cookie with
`Secure`, `HttpOnly`, narrow `Path`/`Domain`, and an explicit `SameSite` policy. OIDC
access/refresh tokens are not exposed to browser JavaScript or Web Storage. The
server-side session record is stored in PostgreSQL, keeps only encrypted provider
token material when refresh requires it, records absolute and idle expiry, and can be
revoked. Session IDs are generated from a cryptographically secure source and stored
server-side as hashes. Redis may cache a negative/short-lived lookup but cannot be
the only session record.

The selected browser contract is the same-origin opaque session cookie with CSRF
controls, handled by the Go identity/session boundary. A service/tool bearer contract
may be introduced later only on explicitly selected operations. An endpoint must not
ambiguously accept both credentials and choose the more privileged principal.

```mermaid
sequenceDiagram
    actor User
    participant Web as ClouDesk web/session boundary
    participant IdP as Amazon Cognito OIDC
    participant DB as PostgreSQL
    participant API as Go API

    User->>Web: begin login
    Web->>Web: create state, nonce, PKCE verifier
    Web-->>User: redirect with code challenge
    User->>IdP: authenticate / provider challenge
    IdP-->>Web: authorization code + returned state
    Web->>IdP: exchange code + verifier
    IdP-->>Web: validated OIDC tokens
    Web->>DB: map (issuer, subject); create rotated session
    Web-->>User: Secure HttpOnly session cookie
    User->>API: protected request through selected same-origin contract
    API->>DB: validate principal/session, membership, permission
    API-->>User: tenant-scoped response
```

Logout revokes the application session, clears the cookie, invalidates browser query
caches, and performs provider logout/revocation when supported and required. Password
reset stays at Cognito. Risk-based MFA is a production hardening requirement for
owners, operators, and privileged changes; broader mandatory MFA follows adoption and
support evidence. Account recovery and email changes must not silently transfer
existing memberships.

Local development uses an `IdentityProvider`/`SessionStore` adapter with the same
subject mapping, claims, expiry, callback, and failure contract. It is enabled only
by explicit non-production configuration, binds to local interfaces, uses clearly
non-production keys/accounts, and cannot start when the environment is production.
It does not create a second production password database or bypass membership checks.

## Authorization, RBAC, And Tenant Controls

The [Memberships domain](../domains/memberships.md) defines the canonical V1 role to
permission mapping. Roles are convenience bundles; application code checks named
permissions and resource predicates rather than role names. The membership role is
authoritative in PostgreSQL. UI capability data is advisory, short-lived, and cleared
on organization switch or `401`/`403`.

Sensitive invariants include last-owner protection, owner-only owner grants/removal,
no self-escalation, current-authorization-before-idempotency-replay, invitation
single-use, optimistic concurrency on role changes, and append-only privileged audit
events. Tenant selection, RLS, caches, events, jobs, S3, failure disclosure, and the
global active-timer exception follow [multi-tenancy](multi-tenancy.md).

## Input, Browser, And API Protections

- OpenAPI defines closed request schemas, size bounds, content types, field-level
  authorization, and safe error responses. Unknown/mass-assigned ownership, role,
  totals, status, audit, and version fields are rejected.
- SQL uses typed parameters and allowlisted filters/sorts. Dynamic identifiers and
  user text are never concatenated into SQL. Database runtime roles lack DDL and
  table-owner privileges.
- Browser-rendered user content is escaped. Markdown is parsed with raw HTML disabled
  or sanitized by a maintained allowlist; dangerous URLs and SVG/HTML execution are
  blocked. A nonce/hash-based Content Security Policy is introduced before production
  and tightened through report-only evidence.
- Security headers include HSTS after HTTPS coverage is proven, frame protection via
  CSP `frame-ancestors`, `nosniff`, a deliberate referrer policy, and a constrained
  permissions policy. Tenant responses default to `private, no-store`.
- Same-origin cookie-authenticated mutations require anti-CSRF protection: SameSite
  is a baseline, not the sole control. Validate Origin/Fetch Metadata and a session-
  bound CSRF token on unsafe methods. OIDC state protects the login callback. CORS is
  disabled by default and exact-origin allowlisted only for an approved client.
- URLs supplied for future webhooks/imports are an SSRF boundary. V1 does not fetch
  arbitrary URLs. Any future fetcher needs scheme/host allowlists, DNS/IP revalidation,
  redirect limits, response-size/time limits, and denial of metadata/private ranges.
- Errors omit stack traces, SQL/provider details, object keys, account existence, and
  cross-tenant identifiers. Caller-supplied request/trace IDs are validated and are
  never authority.

## Abuse And Availability Controls

Production applies layered controls: coarse WAF/IP reputation and request-size rules,
then application token buckets keyed by endpoint risk and combinations of IP,
principal, and organization. Login/recovery is primarily throttled by Cognito plus
edge controls; invitation, role changes, presigned URL creation, invoice sends,
exports, expensive reports, and audit searches receive stricter quotas. Limits and
pagination bounds are contract values to tune from measurement, not universal
numbers.

Redis may coordinate distributed counters, but endpoint behavior is explicit when it
fails. Authentication, invitation, export, and other abuse-sensitive commands fail
closed or use a conservative bounded local/edge emergency limit. Ordinary bounded
reads may proceed with local protection and database budgets. Limits use bounded
cardinality, expire, and never reveal whether an email, user, organization, or object
exists. `429` responses use `Retry-After`; clients apply bounded jittered retry.

The control set explicitly addresses the applicable OWASP web and API risk classes:
broken object/function/property authorization maps to tenant scoping and RBAC;
authentication failures to the OIDC/session controls; injection and insecure design
to typed boundaries and threat modeling; security misconfiguration and cryptographic
failures to IaC, least privilege, TLS, and managed keys; unrestricted resource
consumption and sensitive business-flow abuse to quotas and idempotency; unsafe
third-party consumption, SSRF, software/data integrity, supply-chain, logging, and
exceptional-condition failures to the provider, egress, CI, audit, and fail-closed
controls in this document. An OWASP checklist never substitutes for route-by-route
negative authorization and abuse tests.

Concurrency limits, request deadlines, body limits, upload quotas, query timeouts,
queue admission controls, worker pools, email budgets, and report range limits guard
resource exhaustion. WAF is supplementary; it does not replace object/function
authorization or application validation.

## File And Presigned URL Security

S3 buckets are private, block public access, enforce TLS, encrypt objects, and deny
unapproved principals. Workloads use scoped IAM rather than browser credentials.
The API creates pending PostgreSQL metadata before a short-lived, method/key-specific
presigned grant. It selects a non-guessable tenant-prefixed key, constrains expected
size/type/checksum where supported, and never accepts a caller-chosen final key.

Completion verifies the actual object, metadata, checksum, size, owner resource, and
tenant before promotion. Extension and client-declared MIME type are not trusted.
Risky uploads enter quarantine and asynchronous malware scanning; they cannot receive
download URLs or be rendered inline. Archives are not extracted in the request path.
Downloads use a safe `Content-Disposition`, restrictive content type, and `nosniff`.
HTML, SVG, scripts, executables, and macro-enabled files follow an explicit deny or
forced-download policy.

Presigned URLs are temporary bearer capabilities. Their lifetime is the minimum
needed for the operation, they are returned with `no-store`, redacted from telemetry,
never sent in events/email, and cannot be individually revoked after issue; deletion,
object-key rotation, short expiry, and authorization before issuance limit residual
risk. Abandoned objects and metadata are reconciled by bounded tenant-safe jobs.

## Secrets, Encryption, And Key Management

- No source, image, Helm value, Terraform variable default, frontend bundle, log, or
  test fixture contains a production secret. `.env` examples contain names only.
- AWS Secrets Manager stores provider credentials, database credentials where IAM
  authentication is not selected, session/token encryption keys, webhook secrets,
  and other runtime secret material. Workloads retrieve only named secrets through
  workload identity; Kubernetes Secrets are not a general long-term source of truth.
- CI uses GitHub OIDC federation to assume narrow environment roles; long-lived AWS
  access keys are prohibited. Fork/untrusted workflows do not receive production
  secrets or privileged tokens.
- TLS protects all external and service-to-managed-service traffic. RDS storage and
  backups, S3, EBS, queue data, and secret stores are encrypted. KMS key scope and
  customer-managed keys are selected when rotation, separation, or contractual audit
  needs justify their operational cost.
- Password hashing remains the Cognito provider's responsibility. Session IDs,
  invitation tokens, idempotency fingerprints, and cursor signatures use maintained
  cryptographic libraries and separate purpose-specific keys.
- Rotation supports current/previous key overlap where protocol state requires it,
  records owner and expiry, tests rollback, and revokes compromised credentials.
  Secret values never appear in rotation evidence.
- Secret scanning, dependency review, SBOM/provenance, pinned build inputs, image
  scanning, and protected review for auth/IAM/migration changes are future CI gates.

## IAM, Database, And Platform Least Privilege

Every workload has a distinct Kubernetes service account and AWS workload identity;
pods never use static access keys or a shared node role for application access.

| Workload | Required cloud authority | Explicitly excluded |
| --- | --- | --- |
| API | Read named identity/secret config; issue grants only for approved S3 prefixes/operations | Bucket listing, queue administration, wildcard S3, IAM mutation |
| Outbox publisher | Send to named SQS queues; read/update outbox through its DB role | Business-table reads, S3, email secret, queue administration |
| Notification worker | Receive/delete named queue messages; read named email secret | S3, IAM, unrelated queues/business tables |
| Document/file worker | Receive named queue; scoped S3 object operations; owned DB tables | Bucket policy/list-all, identity administration, unrelated secrets |
| Audit/projector worker | Receive named queue; insert/read owned projections | Membership mutation, S3, provider credentials |
| CI deployer | Push immutable artifact or update one environment through gated role | Standing production admin, credential creation, human-data access |

IAM policies use explicit resources, actions, regions/accounts, conditions, and
separate environment boundaries. Kubernetes restricts service-account token
automount, capabilities, root execution, writable filesystems, network paths, and
secret mounts to demonstrated need. RDS and Redis are private; security groups permit
only named workload paths. The production database separates migration, API,
publisher, worker, read-only support, and break-glass roles. Runtime roles cannot
disable RLS, run DDL, alter audit rows, or assume another database role.

## Events, Jobs, Providers, And Replay

Reliable events originate in the transactional outbox, contain a server-written
tenant ID and immutable event ID, and are versioned/validated before handling. SQS is
at least once, so consumers store tenant-scoped inbox deduplication with their
database effect. Retries are bounded with jitter; poison messages enter restricted
DLQs. Controlled replay requires an operator identity, reason, scope, dry inspection,
idempotent consumer, audit event, and confirmation that the original tenant still
exists and the action remains permitted.

Queue policies restrict producers/consumers and confused-deputy conditions. Message
attributes and trace headers are observability input, not authorization. External
provider callbacks require signature verification, timestamp/replay window,
canonical payload handling, source/endpoint policy where useful, and idempotency.
Provider errors are normalized and redacted; unsafe third-party fields never become
trusted HTML, SQL, object keys, or log labels.

## Logging, Monitoring, And Audit

Structured application logs may contain timestamp, severity, service, environment,
route template, method/status, duration, stable error code, request/trace ID, and
authorized organization/user IDs under access and retention policy. They do not
contain passwords, tokens, session IDs/cookies, invitation values, CSRF values,
presigned URLs, secret/config values, raw request bodies, file contents, invoice
details, tax identifiers, or unnecessary personal data. Email/IP/user-agent fields
are minimized, normalized, and protected according to the security-use retention
policy.

Metrics use low-cardinality route/error/event labels and never raw tenant, user,
resource, email, cursor, or file-name labels. Trace attributes follow the same data
rules; baggage from callers is allowlisted and size-limited. Access to logs, traces,
audit events, and dashboards is least privileged and itself auditable.

Alert candidates include credential attack spikes, authorization-denial anomalies,
privileged role changes, owner removal attempts, unusual invitation/presigned/export
volume, malware/quarantine detections, DLQ growth/replay, secret access anomalies,
RLS/context failures, audit pipeline lag, and security-log ingestion gaps. Alerts use
runbooks and avoid exposing payloads in paging tools. The application audit contract
is defined in [Audit](../domains/audit.md).

## Threat Model

Severity is architectural risk before implementation evidence. Residual risk assumes
the proposed controls are correctly implemented and verified.

| Threat / abuse path | Initial risk | Required mitigations | Residual risk |
| --- | --- | --- | --- |
| Cross-tenant data access through an unscoped query, relationship, report, or batch | Critical | Explicit route tenant, active membership, permissions, scoped repositories, composite FKs, selective RLS, negative multi-tenant tests | Medium: policy/query defects or privileged DB access remain possible |
| IDOR/BOLA using another tenant's opaque resource ID | Critical | Scope every lookup by organization and parent; conceal wrong-tenant existence; uniform tests on every route/job | Low-Medium: a missed alternate path remains the key concern |
| Confused deputy in global active-timer, jobs, caches, files, or support tools | High | Narrow `/me` exception; server-derived tenant envelope/key; per-tenant transaction; visibility discriminator; reasoned audited admin access | Medium: broad operational roles need continuing review |
| Privilege escalation, mass assignment, self-promotion, or last-owner removal | High | Permission checks in use cases; closed schemas; role hierarchy; owner-only invariants; optimistic versions; audit | Low-Medium: policy mapping mistakes remain possible |
| Compromised credentials, brute force, credential stuffing, recovery abuse | High | Cognito managed controls; generic responses; WAF/provider/IP limits; MFA for privileged roles; recovery/change audit | Medium: phishing and provider/account compromise cannot be eliminated |
| Stolen/fixed session or token replay | High | Code+PKCE/state/nonce; HttpOnly/Secure cookie; opaque rotated sessions; expiry/revocation; no Web Storage; CSP; reauthentication for high risk | Medium: an active browser/session compromise retains authority until revoked |
| CSRF against cookie-authenticated mutation/login | High | SameSite plus Origin/Fetch Metadata and session-bound CSRF token; OIDC state; exact redirects; no permissive CORS | Low if every unsafe route shares middleware |
| XSS from comments, names, files, generated reports, or dependencies | High | Contextual escaping, sanitized Markdown/no raw HTML, CSP, safe downloads, dependency controls, no tokens in JS | Medium: client dependency/runtime defects remain possible |
| SQL/command/template injection | Critical | Typed parameters, allowlists, closed schemas, no shell/template interpolation, least-privilege DB role, safe generators | Low-Medium: new parsers/renderers require review |
| Leaked presigned URL or public/mis-scoped S3 object | High | Block public access; server-selected prefix; short method-specific URLs; no-store/redaction; workload IAM; completion verification | Medium: issued URL is usable until expiry |
| Malicious upload, polyglot/archive bomb, malware, unsafe inline rendering | High | Size/type/checksum limits; quarantine; scan risky files; no request-path extraction; forced download; resource quotas | Medium: scanner evasion and zero-day formats remain possible |
| Event replay, duplicate provider effect, forged callback, cross-tenant DLQ replay | High | Outbox/inbox IDs; tenant-scoped dedupe; signatures/timestamps; provider idempotency; bounded controlled audited replay | Medium: external providers without idempotency require reconciliation |
| API flooding, expensive reports/exports, upload/queue/email cost abuse | High | Layered token buckets, WAF, quotas, pagination/range limits, deadlines, bounded pools, queue admission and spend alerts | Medium: distributed attacks and valid-account abuse consume resources |
| Tenant enumeration or account enumeration through status, timing, invites, cursors, logs | Medium | Concealed `404`; generic identity/invite responses; signed tenant-bound cursors; bounded comparable work; protected telemetry | Low-Medium: aggregate timing and side channels require measurement |
| Secret leakage through source, build, Terraform state, client bundle, logs | Critical | Secrets Manager/workload identity; no static keys; scanning; redaction; protected state; rotation and incident runbook | Medium: authorized runtime compromise can read allowed secrets |
| Insecure logs/audit gaps or audit tampering | High | Field allowlists; append-only runtime grants; retention/access control; ingestion-gap alerts; external break-glass audit | Medium: database/cloud administrators remain a trust boundary |
| IAM/cloud/Kubernetes misconfiguration or compromised workload | Critical | Per-workload roles, private networks, explicit resources/conditions, non-root containers, network policy, config/IaC review | Medium: platform control-plane compromise has broad impact |
| Vulnerable/malicious dependency or CI artifact | High | Pinning/lockfiles, dependency review, SAST/secret/image scans, SBOM/provenance, immutable digests, protected CI OIDC | Medium: novel supply-chain compromise remains possible |
| SSRF through future import, webhook, image/PDF fetcher | High | Do not fetch arbitrary URLs in V1; future egress proxy/allowlists, IP/DNS validation, redirect/size/time limits | Low in V1; must be remodeled before feature introduction |
| Race/replay in timers, invoice issue, invitations, role changes | High | PostgreSQL constraints/locking; idempotency; `If-Match`; one global active timer per user; transactional audit/outbox | Low-Medium: provider effects stay eventually consistent |
| Fail-open behavior during OIDC, PostgreSQL, Redis, SQS, or policy failure | High | Auth/authz/DB fail closed; Redis optional; outbox retains work; bounded retries/circuits; no false success | Medium: availability loss is intentionally preferred to unsafe access |

## Security Verification And Gates

Before M1 is considered complete, tests must cover OIDC/session invalidity and
rotation, CSRF, active/suspended/revoked memberships, every role/permission pair,
resource-level restrictions, organization switching, invitation replay, last-owner
races, global active-timer disclosure, cross-tenant IDs/parents/cursors/idempotency,
RLS pool hygiene, and audit creation. They use actual runtime database roles.

Before file/event production enablement, tests cover presigned constraints and expiry,
quarantine/download behavior, object reconciliation, forged and duplicate messages,
consumer crash/retry, DLQ replay, provider callbacks, and IAM denial paths. CI adds
dependency, secret, SAST, IaC, manifest, and image checks with triage ownership.

Active penetration or cloud testing requires an explicitly authorized target and
scope. This design task performed static review only and did not run active tests.

## Accepted Residual Risks And Deferred Decisions

- Cognito is a provider dependency; local adapter parity and standards-based subject
  mapping reduce migration cost but do not make providers interchangeable without
  testing.
- Presigned URLs cannot be recalled reliably after issuance; short expiry and object
  controls bound the window.
- Application/database/cloud administrators remain privileged trust boundaries.
  Separation, monitoring, and external audit reduce but do not remove insider risk.
- Mandatory MFA for every user, customer-managed encryption keys, tamper-evident audit
  export, custom roles, support impersonation, content disarm/reconstruction, and a
  dedicated security event platform are future decisions triggered by customer,
  regulatory, threat, or operational evidence.
- Numeric rate limits, retention periods, and token/session lifetimes must be set and
  load-tested per environment before production; this document intentionally does not
  present untested examples as guarantees.
