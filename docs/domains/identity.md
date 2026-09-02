# Identity Domain

## Purpose And Status

Identity maps an externally authenticated person to a stable ClouDesk user and owns
the application-session lifecycle. It does not own passwords, tenant roles, or
permissions. This is a proposed contract; production targets Amazon Cognito through
OIDC while local development uses a compatible adapter.

See [ADR-011](../decisions/ADR-011-amazon-cognito-oidc.md),
[security architecture](../architecture/security.md), and
[Memberships](memberships.md).

## Boundaries And Model

The provider owns credentials, password reset, federation, MFA challenges, and the
OIDC authorization result. ClouDesk owns:

- `users`: stable `id`, display/profile attributes needed by the product, status,
  timestamps, and version;
- `external_identities`: `user_id`, normalized issuer, immutable provider subject,
  provider kind, verified-email snapshot where useful, timestamps, and a unique
  `(issuer, subject)` constraint;
- `application_sessions`: hashed opaque handle, user, encrypted provider material
  only when required for refresh/logout, issued/idle/absolute expiry, rotation
  lineage, revocation metadata, and security correlation;
- login-related audit intent without raw credentials or tokens.

Email is mutable and cannot be the identity key. Provider groups/custom claims do
not grant organization permissions. Linking a second identity to an existing user is
deferred until an explicit account-linking threat model exists.

## Production Authentication Flow

1. The application creates cryptographically random `state`, `nonce`, and PKCE
   verifier/challenge and retains them in a short-lived server-side login attempt.
2. It redirects to the configured Cognito authorization endpoint using Authorization
   Code flow and an exact allowlisted callback URI.
3. The callback validates state before exchanging the code, then validates issuer,
   audience/client binding, authorized algorithm, signature, expiry, nonce, and token
   type through a maintained OIDC library.
4. The application resolves `(issuer, subject)` to a user. First-login provisioning
   creates the local mapping transactionally but grants no organization authority.
5. It rotates an opaque application session and returns only a `Secure`, `HttpOnly`,
   narrowly scoped cookie using the selected SameSite/CSRF policy.
6. Each protected browser request validates the application session and CSRF contract
   where required, then independently resolves current membership and permissions.

OIDC tokens, authorization codes, PKCE verifiers, session handles, and callback
parameters are never logged. Return URLs are same-origin, normalized, and allowlisted
to prevent open redirects.

## Session Lifecycle

- Idle and absolute expiry are enforced from PostgreSQL time. Provider token expiry
  does not silently extend the application session.
- Rotation is atomic. Reuse of an invalidated predecessor is treated as suspicious,
  revokes the session family where supported, and emits a security event.
- Refresh is single-flight per session to prevent storms. Transient provider failure
  does not bypass expiry; the UI receives a controlled reauthentication state.
- Logout revokes the server session before clearing the cookie. Global/provider
  logout is used when supported but is not assumed to revoke every external session.
- Password reset and account recovery remain Cognito flows. A recovery or email
  change does not alter ClouDesk memberships or invitation ownership automatically.
- Privileged operations may require recent authentication/MFA once the production
  policy is enabled.
- Session records and expired login attempts are removed by bounded cleanup jobs;
  audit records follow their separate retention policy.

The browser contract is the opaque cookie session. A future service/tool bearer
contract must be introduced on explicitly selected operations and no endpoint may
select between two presented credentials in a way that enables principal confusion.

## Local Identity Adapter

The application depends on narrow interfaces such as identity verification, login
initiation/callback, session lookup/rotation/revocation, and provider logout. The
production adapter implements them with Cognito OIDC. The local adapter implements
the same success, expiry, invalid-signature/claim, disabled-user, and outage behaviors
without becoming a production password system.

Local mode is guarded by an explicit environment discriminator, uses disposable
identities and non-production keys, binds to local/test networks, and refuses to
start in a production environment. Automated tests can inject deterministic clocks
and signed test identities through the adapter rather than bypassing authentication
middleware.

## Identity Status And Failure Behavior

Proposed user status is `ACTIVE` or `DISABLED`. Disabling a user revokes application
sessions and prevents new organization authorization while retaining historical
actor references. Deleting an identity is a privacy/retention workflow, not a
cascade over invoices, audit evidence, or memberships.

- No/invalid/expired credentials: generic `401`.
- Valid identity with no tenant membership: identity routes may succeed; tenant
  routes conceal organization existence.
- Disabled local user: generic authentication failure externally and a protected
  security reason internally.
- Provider/JWK outage: cached, still-valid keys may be used within a bounded policy;
  unknown keys or expired metadata fail closed rather than accepting unverifiable
  tokens.
- Ambiguous/missing subject or issuer: reject authentication; never fall back to
  email matching.

## Security Events And Verification

Record successful login/session creation at policy-defined granularity, failed
callback categories without secret input, session refresh/rotation anomaly, logout,
session revocation, disabled-user attempt, recovery/MFA signals received safely from
the provider, and identity-link attempts. High-volume failed logins are primarily
provider/edge telemetry and must be aggregated without storing attempted passwords.

Future tests cover state/nonce/PKCE, wrong issuer/audience/algorithm, expiry/skew,
key rotation, exact redirects, open-redirect attempts, concurrent refresh, session
fixation/reuse, logout/revocation, disabled users, cookie flags, CSRF integration,
provider outage, local-adapter production rejection, and proof that claims never
grant tenant permission.

## Evolution

MFA for privileged roles is the first production evolution. Enterprise federation,
additional OIDC providers, SCIM, account linking, device/session management UI, and
mandatory MFA for all users require explicit product demand and separate threat
modeling. Provider replacement preserves ClouDesk user IDs and organization
memberships through the `(issuer, subject)` mapping; it is a migration, not merely a
configuration toggle.
