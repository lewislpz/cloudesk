# Security Audit Risk Catalog

Use this catalog as a compact prompt for what to look for. It is intentionally cross-platform; map each item to the stack under review.

## Current Baselines

- OWASP Top 10 2025: broken access control, security misconfiguration, software supply chain failures, cryptographic failures, injection, insecure design, authentication failures, software/data integrity failures, logging/alerting failures, mishandling exceptional conditions.
- OWASP API Security Top 10 2023: BOLA/IDOR, broken authentication, object property authorization, unrestricted resource consumption, broken function authorization, sensitive business flow abuse, SSRF, misconfiguration, improper API inventory, unsafe consumption of third-party APIs.
- OWASP Mobile Top 10 2024: improper credential usage, inadequate supply-chain security, insecure authn/authz, insufficient input/output validation, insecure communication, inadequate privacy controls, insufficient binary protections, security misconfiguration, insecure data storage, insufficient cryptography.
- OWASP LLM/GenAI Top 10 2025: prompt injection, sensitive information disclosure, AI supply chain, data/model poisoning, improper output handling, excessive agency, system prompt leakage, vector/embedding weaknesses, misinformation, unbounded consumption.
- MITRE CWE Top 25 and CISA KEV: prioritize root causes that are common, severe, and actively exploited, especially injection, memory safety, path traversal, auth bypass, deserialization, SSRF, file upload, credential exposure, command execution, and access-control flaws.

## Cross-Cutting Checks

- Access control: object-level, function-level, property/field-level, tenant isolation, admin boundaries, ownership checks, direct object references, policy bypass through alternate routes/jobs/webhooks.
- Authentication: MFA, password reset, session fixation, token validation, JWT algorithms/audience/issuer/expiry, OAuth/OIDC flow misuse, refresh-token rotation, account enumeration, brute force protection.
- Authorization consistency: server-side enforcement, centralized policy, deny-by-default, fail-closed behavior, route guards that match backend checks, background worker permissions.
- Input and output handling: SQL/NoSQL/LDAP/XPath/GraphQL/template/command injection, XSS, HTML sanitization, open redirects, path traversal, file upload, unsafe archive extraction, unsafe deserialization, prototype pollution, unsafe regex.
- SSRF and outbound requests: URL parsing bypasses, redirects, DNS rebinding, cloud metadata access, internal network access, webhook fetchers, image/PDF importers, XML external entities.
- Data protection: secrets in code/logs/build artifacts, PII minimization, encryption in transit and at rest, key management, backup exposure, retention/deletion, masking, cache privacy.
- Crypto: custom crypto, weak randomness, hardcoded keys, obsolete algorithms/modes, missing authentication, predictable tokens, insecure password hashing.
- Errors and exceptional conditions: stack traces, fail-open auth, partial transaction failures, retry storms, inconsistent state, unsafe fallback paths, exception-based bypasses.
- Logging and monitoring: security events for auth, authorization denial, admin actions, key events, suspicious automation, data export, and privilege changes; alertability and tamper resistance.
- Business logic: race conditions, replay, coupon/payment abuse, workflow skipping, inventory/quantity manipulation, approval bypass, idempotency failures, refund or credit abuse.
- Availability and abuse: rate limits, quotas, upload limits, pagination bounds, expensive queries, queue flooding, email/SMS cost abuse, LLM token/cost exhaustion.

## Web and Frontend

- DOM XSS, unsafe `dangerouslySetInnerHTML`, unsafe markdown/HTML rendering, CSP gaps, cookie flags, CSRF on cookie-authenticated state changes.
- Client-only authorization, exposed internal endpoints, source maps with secrets, environment variables bundled into client code.
- CORS misconfiguration, postMessage origin validation, service worker cache leaks, clickjacking, mixed content.

## API and Backend

- Missing auth on internal or deprecated endpoints, inconsistent route middleware, mass assignment, overbroad response fields, GraphQL introspection/excessive depth, batch endpoint authorization bypass.
- Unsafe parsers: XML, YAML, pickle/marshal, Java serialization, PHP object injection, insecure JSON polymorphism.
- Webhooks: signature verification, replay windows, idempotency, source allowlisting, payload canonicalization.

## Mobile and Desktop

- Insecure local storage/keychain usage, hardcoded secrets, debug builds, weak certificate validation, missing certificate pinning when risk warrants it.
- Deep link/auth callback hijacking, exported Android components, iOS URL scheme issues, WebView JavaScript bridges, IPC/RPC permission checks.
- Binary tampering/reverse engineering risk, update integrity, local database encryption, crash/log PII leakage.

## AI, LLM, and Agentic Apps

- Prompt injection through user content, retrieved documents, webpages, emails, tickets, or tool output.
- Excessive agency: tools that can spend money, send messages, modify data, run code, access private systems, or make irreversible changes without scoped authorization and confirmation.
- Tool security: per-tool authz, input schemas, output validation, allowlists, sandboxing, audit logs, least privilege credentials.
- RAG/vector stores: cross-tenant retrieval, poisoned embeddings, insecure metadata filters, stale/deleted data leakage, citation spoofing.
- Data handling: prompts containing secrets/PII, training/fine-tuning leakage, vendor retention settings, model output used as trusted code/SQL/HTML.
- Cost and abuse: token exhaustion, recursive agents, batch fanout, unauthenticated inference, prompt amplification.

## Supply Chain and SDLC

- Vulnerable/outdated dependencies, malicious packages, dependency confusion, typosquatting, unpinned versions, lockfile drift.
- Build integrity: untrusted install scripts, CI secrets exposure, overbroad CI tokens, unsigned artifacts, missing provenance/SBOM, unreviewed generated code.
- Repository hygiene: branch protection, required reviews, CODEOWNERS for sensitive areas, secret scanning, dependency review, release signing.

## Cloud, Containers, and Infrastructure

- Public storage buckets, overly permissive IAM, exposed databases/admin consoles, metadata service exposure, weak network segmentation.
- Containers: root user, privileged mode, host mounts, writable root filesystem, broad capabilities, unsafe Docker socket access, stale base images, secrets in layers.
- Kubernetes: default service account tokens, cluster-admin bindings, privileged pods, hostPath mounts, missing network policies, exposed dashboards.
- TLS/domain: weak TLS, missing HSTS for web apps, misissued cert assumptions, dangling DNS, takeover-prone subdomains.
