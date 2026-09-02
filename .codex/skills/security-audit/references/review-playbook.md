# Security Review Playbook

## Triage Commands

Use equivalents for the local stack; do not install tools without approval.

- Inventory files: `rg --files`, `find`, package manifests, Dockerfiles, compose files, IaC, CI workflows, env examples.
- Find secrets patterns: `rg -n "(api[_-]?key|secret|token|password|private[_-]?key|BEGIN [A-Z ]*PRIVATE KEY|AKIA|ghp_|xox[baprs]-)"`.
- Find auth boundaries: `rg -n "(auth|authorize|permission|role|policy|tenant|owner|admin|session|jwt|oauth|oidc)"`.
- Find dangerous sinks: `rg -n "(eval\\(|exec\\(|spawn\\(|system\\(|deserialize|pickle|yaml\\.load|innerHTML|dangerouslySetInnerHTML|raw\\(|template|query\\(|\\$where|new Function|child_process)"`.
- Find URL/file sinks: `rg -n "(fetch\\(|axios|requests\\.|http\\.|open\\(|readFile|writeFile|createReadStream|upload|download|redirect|urlparse|new URL)"`.
- Find config exposure: `rg -n "(CORS|csrf|cookie|secure|sameSite|helmet|csp|debug|trace|swagger|openapi|graphql|introspection)"`.
- Dependency checks: use existing project tools first (`npm audit`, `pnpm audit`, `yarn npm audit`, `pip-audit`, `poetry audit`, `bundle audit`, `cargo audit`, `govulncheck`, `mvn org.owasp:dependency-check`, `trivy`, `grype`) when available.

## Manual Review Method

1. Trace trust boundaries from entry point to sink: request/input -> parser/validator -> authn -> authz -> business logic -> data/tool side effect -> output/log.
2. For every sensitive object ID, verify server-side ownership or policy checks at the point of use.
3. For every role/admin path, attempt to identify an alternate lower-privilege route, job, webhook, batch API, or client-only guard.
4. For every external URL/file/parser, check allowlists, size limits, redirect handling, MIME/type validation, archive traversal, and sandboxing.
5. For every secret-bearing component, check source, runtime injection, logs, client bundles, CI exposure, rotation path, and least privilege.
6. For every dependency/runtime, check whether vulnerable versions are reachable, exposed, and patched by existing lockfiles and images.

## Remediation Patterns

- Centralize authorization checks close to resource access; prefer policy functions that accept actor, action, resource, and tenant.
- Validate input with schemas at boundaries; encode output by context; use parameterized APIs for queries and commands.
- Make dangerous egress deny-by-default: allowlist hosts/schemes, block private/link-local ranges, disable redirects or revalidate after redirects.
- Store secrets only in secret managers or deployment env; rotate exposed credentials; prevent client bundling.
- Harden sessions: secure, HttpOnly, SameSite cookies; short-lived access tokens; refresh rotation; revocation on password/MFA changes.
- Add rate limits and quotas on authentication, expensive queries, uploads, exports, AI inference, and third-party-cost flows.
- Fail closed on security errors and exceptional states; preserve audit logs for denied and high-risk operations.
- For LLM tools, enforce tool allowlists, schema validation, per-action authorization, human confirmation for irreversible actions, and output sanitization.

## Verification

- Add focused tests for the exploit path: unauthorized user cannot access/modify object; malicious input remains data; SSRF/private host blocked; secret not logged; rate limit triggers.
- Include negative tests for alternate paths and background jobs.
- Run existing unit/integration/security checks after remediation.
- If active testing is authorized, use safe local or staging probes and avoid destructive payloads.
