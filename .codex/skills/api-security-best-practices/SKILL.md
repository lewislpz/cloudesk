---
name: api-security-best-practices
description: Use when implementing or reviewing API authentication, authorization, validation, abuse controls, sensitive data, or vulnerability protections.
---

# API Security

## Boundaries

Use for security-sensitive API work. Treat concrete controls as context-dependent;
do not assume JWT, a specific password algorithm, fixed rate limits, or one framework.

## Operating Loop

1. Identify assets, actors, entry points, trust boundaries, abuse cases, and failure
   impact.
2. Inspect existing identity, authorization, validation, secrets, logging, and
   deployment controls.
3. Select the smallest controls that mitigate the identified threats while preserving
   established architecture.
4. Implement deny-by-default authorization, strict input handling, safe errors, and
   secret-safe observability.
5. Verify positive and negative authorization paths, malformed input, abuse behavior,
   and sensitive-data exposure.

## Required Safety Outcomes

- Authenticate identities where required and authorize every protected operation.
- Validate untrusted input at the trust boundary.
- Never expose secrets, credentials, internal stack traces, or sensitive fields.
- Add abuse controls proportional to exposure, cost, and threat model.
- Use maintained cryptographic and identity libraries; do not invent protocols.
- Record unresolved threats and verification gaps.

## Optional Reference

Load [legacy-guide.md](references/legacy-guide.md) only when its Express, JWT, or
Spring examples match the detected stack. Its fixed limits are examples, not policy.
