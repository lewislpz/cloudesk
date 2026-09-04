# ClouDesk

ClouDesk is a planned multi-tenant SaaS for professional services teams. The
repository is currently in **M0 — Repository Foundation**: architecture and product
contracts are documented, while application features and production infrastructure
have not been implemented.

Start with the [technical documentation](docs/README.md), the
[architecture overview](docs/architecture/overview.md), and the
[implementation roadmap](docs/roadmap/implementation-plan.md).

## Toolchain

Install the language and package-manager versions pinned in
[.tool-versions](.tool-versions):

- Go 1.27.0
- Node.js 24.15.0
- pnpm 10.15.1

Docker 29.x is required by later local-dependency tasks but is not managed by this
repository's language toolchain file.

The exact pnpm version is also recorded in `package.json`. Package versions are
locked in `pnpm-lock.yaml`; do not install with an unfrozen lockfile in CI.
ESLint remains pinned to the latest compatible 9.x release because Next.js's current
transitive plugins do not yet accept ESLint 10; strict peer checks keep that temporary
constraint visible. The workspace also overrides transitive `js-yaml` to 4.3.2 so
OpenAPI tooling stays above the patched thresholds for the recorded quadratic-CPU
advisories; remove the override only after the generator dependency graph is verified.

## Bootstrap

```bash
pnpm install --frozen-lockfile
cp .env.example .env
```

`.env.example` contains names and safe local defaults only. Populate secrets in the
ignored `.env` file or an approved secret store; never commit them.

## Repository Commands

Run these commands from the repository root:

| Command | Purpose |
| --- | --- |
| `pnpm format` | Format Go and frontend files. |
| `pnpm format:check` | Check formatting without changing files. |
| `pnpm lint` | Run Go vet and frontend ESLint. |
| `pnpm typecheck` | Type-check the frontend. |
| `pnpm test` | Run backend and frontend unit tests. |
| `pnpm generate` | Regenerate OpenAPI clients plus registered Go and frontend outputs. |
| `pnpm generate:openapi` | Generate strict Go interfaces and the TypeScript fetch client. |
| `pnpm lint:openapi` | Lint the API contract and reject incompatible changes when a baseline exists. |
| `pnpm check:generated` | Regenerate and fail if either generated tree changes. |
| `pnpm check` | Run every non-mutating foundation check. |

The commands intentionally have stable names before product code exists. Later M0
tasks extend them with integration tests, migrations, and documentation checks.

## Current Structure

```text
backend/       Go module and generated OpenAPI boundary; runnable processes arrive later
frontend/      Next.js/React workspace and generated API client; the app shell arrives later
docs/          Proposed product and engineering architecture
scripts/       Small repository-level verification helpers
```

## Delivery Status

No application, AWS resource, Kubernetes object, or release is deployed. See the
[production-readiness checklist](docs/roadmap/production-readiness.md) before making
production claims.
