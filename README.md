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
| `pnpm dev` | Run the Next.js M0 shell on the local web port. |
| `pnpm dev:api` | Run the Go API skeleton on `API_HTTP_ADDRESS` (default `:8080`). |
| `pnpm dev:worker` | Run the cancellation-aware Go worker skeleton. |
| `pnpm build:backend` | Compile every Go process entry point. |
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

The API currently serves only `GET /health/live` and `GET /health/ready`. The
organization operation in the OpenAPI compatibility fixture is deliberately not
routed until its authentication, membership, and product behavior arrive in M1.
Both Go processes validate configuration at startup and handle `SIGINT`/`SIGTERM`;
the API withdraws readiness before draining in-flight requests.

The web application currently renders the public route at `/`, the onboarding
shell at `/onboarding`, and the tenant-shaped workspace shell at
`/{organizationSlug}`. These routes deliberately contain no product data and do not
claim authentication; the session and immutable organization resolution arrive in
the first vertical milestone.

## Current Structure

```text
backend/       Runnable Go API/worker skeletons and generated OpenAPI boundary
frontend/      Responsive Next.js shells, generated API runtime, and component tests
docs/          Proposed product and engineering architecture
scripts/       Small repository-level verification helpers
```

## Delivery Status

No application, AWS resource, Kubernetes object, or release is deployed. See the
[production-readiness checklist](docs/roadmap/production-readiness.md) before making
production claims.
