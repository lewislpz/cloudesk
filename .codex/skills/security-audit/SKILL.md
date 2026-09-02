---
name: security-audit
description: Use when auditing, hardening, threat-modeling, reporting, or fixing application security across web, API, mobile, desktop, backend, cloud, container, supply-chain, data, and AI/LLM systems.
---

# Security Audit

## Purpose

Audit security across the full application stack and, when requested, fix issues with focused patches and verification. Adapt scope from local artifacts instead of assuming a framework.

## Operating Rules

- Confirm authorization and scope before any active testing against external systems. If authorization is unclear, limit work to static/local review.
- Prefer evidence over speculation. Tie every finding to files, configuration, reachable flows, commands, or source references.
- Do not expose secrets in responses. Report secret type, location, and rotation guidance without printing the secret value.
- Prioritize exploitable risk over checklist volume. A smaller list of proven issues is better than a large unverified list.
- Fix root causes when asked to remediate. Add regression tests or validation steps proportional to blast radius.
- Use current sources for time-sensitive vulnerability intelligence: CISA KEV, NVD/vendor advisories, package advisories, OWASP current projects, and framework release notes.

## Workflow

1. Establish scope: app type, trust boundaries, exposed surfaces, auth model, data sensitivity, deployment, dependencies, and whether active testing is allowed.
2. Inventory assets: entry points, APIs, jobs, admin tools, storage, queues, webhooks, integrations, cloud resources, containers, CI/CD, and AI tools.
3. Build threat model: identify actors, assets, trust boundaries, abuse cases, privilege boundaries, and high-impact failure modes.
4. Run layered review:
   - Static code and config review.
   - Dependency and supply-chain review.
   - Authn/authz and tenant isolation review.
   - Input, output, serialization, file, URL, and command handling review.
   - Data protection, secrets, crypto, privacy, logging, and monitoring review.
   - Runtime, deployment, container, cloud, and CI/CD review.
   - Domain-specific review for API, mobile, AI/LLM, payments, healthcare, fintech, or regulated workflows.
5. Validate findings with the least invasive method available: tests, local reproduction, reasoning from code paths, config proof, or safe scanner output.
6. Remediate in small patches. Preserve behavior, add security tests, update docs/config examples only when needed.
7. Report results with severity, evidence, exploit path, affected assets, recommended fix, verification performed, and residual risk.

## Reference Selection

Read only the references needed for the target:

- `references/risk-catalog.md`: vulnerability classes and checklist across web, API, mobile, AI/LLM, supply chain, cloud, containers, and operations.
- `references/review-playbook.md`: practical commands, review techniques, evidence collection, and remediation patterns.
- `references/report-template.md`: reusable structure for findings, executive summaries, and remediation plans.
- `references/source-map.md`: standards and live sources to consult when latest vulnerability data matters.

## Severity Model

Set severity from impact, exploitability, exposure, privileges, data sensitivity, tenant/customer blast radius, and compensating controls.

- Critical: unauthenticated or low-complexity compromise of system, production data, secrets, money movement, tenant isolation, code execution, or supply chain.
- High: authenticated privilege escalation, broad sensitive data exposure, account takeover, SSRF to sensitive networks, dangerous deserialization, CI/CD compromise, or exploitable cloud/container misconfiguration.
- Medium: limited data exposure, missing controls requiring meaningful preconditions, defense bypasses, weak rate limits, insecure defaults in non-critical paths.
- Low: hardening gaps, missing headers with limited exploitability, low-impact info leaks, incomplete monitoring, documentation/config drift.

## Deliverables

For audits, produce:

- Scope and assumptions.
- Findings ordered by severity.
- Evidence with file links, config paths, routes, or commands.
- Exploitability and business impact.
- Concrete remediation.
- Verification performed and tests still needed.

For remediation, also include:

- Files changed.
- Tests or checks run.
- Remaining risks and follow-up work.
