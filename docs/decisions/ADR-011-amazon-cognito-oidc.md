# ADR-011: Use Amazon Cognito Through OIDC For Production Identity

## Status

Proposed

## Context

ClouDesk needs secure session/token lifecycle, recovery, federation evolution, and MFA without owning password security.

## Decision

Use Amazon Cognito as the initial production identity provider through Authorization Code + PKCE. The Go identity boundary maps the stable provider subject to an application user and issues an opaque, rotated, PostgreSQL-backed browser session cookie; provider tokens remain server-side. Keep organization authorization in ClouDesk.

## Alternatives Considered

Application-managed passwords add disproportionate security burden; external SaaS identity may improve UX but adds vendor cost; other OIDC providers remain replaceable behind standards.

## Consequences

The app depends on provider availability and configuration and must operate revocation, CSRF, expiry, and session cleanup. Local development uses a compatible test provider/adaptor, and production should evolve to MFA policy based on risk.
