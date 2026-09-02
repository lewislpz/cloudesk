# Security Source Map

Use these sources when current vulnerability data, standards, or authoritative checklists matter. Prefer primary sources over blogs.

## Standards and Checklists

- OWASP Top 10 2025: `https://owasp.org/Top10/2025/`
- OWASP API Security Top 10 2023: `https://owasp.org/API-Security/editions/2023/en/0x11-t10/`
- OWASP Mobile Top 10 2024: `https://owasp.org/www-project-mobile-top-10/`
- OWASP Top 10 for LLM and GenAI Apps 2025: `https://genai.owasp.org/llm-top-10/`
- OWASP ASVS 5.0.0: `https://owasp.org/www-project-application-security-verification-standard/`
- OWASP Cheat Sheet Series: `https://cheatsheetseries.owasp.org/`
- MITRE CWE Top 25 and Top KEV Weaknesses: `https://cwe.mitre.org/top25/`
- CISA Known Exploited Vulnerabilities catalog: `https://www.cisa.gov/known-exploited-vulnerabilities-catalog`

## Vulnerability Intelligence

- CISA KEV for exploited-in-the-wild prioritization.
- NVD and CVE records for CVE metadata, but confirm exploitability and patches with vendor advisories.
- GitHub Security Advisories, OSV, npm/PyPI/RubyGems/Go/Rust/Maven advisories for dependency ecosystems.
- Vendor security bulletins for frameworks, runtimes, OS images, cloud services, and appliances.
- Container image scanners and base image advisories for deployed runtime exposure.

## How To Use Sources

- If the user asks for "latest", "current", or production risk, browse or query live advisories before finalizing.
- Map CVEs to reachable code paths and deployed versions; do not rank solely by CVSS.
- Prioritize KEV-listed, internet-exposed, unauthenticated, privilege-escalation, RCE, auth-bypass, SSRF, deserialization, command-injection, and supply-chain issues.
- Record source name and date checked in reports when external advisories influence severity.
