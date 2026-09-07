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
- Node.js 24.20.0
- pnpm 10.15.1

Docker 29.x with Compose v2 and Buildx is the verified local runtime for PostgreSQL
integration tests, dependencies, and image checks, but is not managed by this repository's language toolchain
file.

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
| `pnpm deps:up` | Start healthy persistent PostgreSQL and local OIDC dependencies. |
| `pnpm deps:up:ephemeral` | Start the same dependency contracts without durable volumes. |
| `pnpm deps:down` | Stop persistent local dependencies without deleting their data. |
| `pnpm deps:reset` | Explicitly stop persistent dependencies and delete their local volumes. |
| `pnpm build:backend` | Compile every Go process entry point. |
| `pnpm build:images` | Build the pinned non-root API and web OCI images with local test tags. |
| `pnpm format` | Format Go and frontend files. |
| `pnpm format:check` | Check formatting without changing files. |
| `pnpm lint` | Run OpenAPI checks, Go vet, and frontend ESLint. |
| `pnpm typecheck` | Type-check the frontend. |
| `pnpm test` | Run Go tests (including disposable PostgreSQL) and frontend component tests. |
| `pnpm test:images` | Build and harden-smoke both runtime images locally. |
| `pnpm generate` | Regenerate OpenAPI clients plus registered Go and frontend outputs. |
| `pnpm generate:database` | Regenerate the pinned sqlc persistence boundary. |
| `pnpm generate:openapi` | Generate strict Go interfaces and the TypeScript fetch client. |
| `pnpm lint:openapi` | Lint the API contract and reject incompatible changes when a baseline exists. |
| `pnpm check:generated` | Regenerate and fail if either generated tree changes. |
| `pnpm check` | Run formatting, lint, types, tests, and generated drift checks. |
| `make docs-check` | Check documentation links, fences, and product naming. |
| `make test-foundation` | Run foundation checks, uncached race tests, production web HTTP smoke, and CI/docs policy checks. |

Database-specific commands run from `backend/`: `make db-test-reset` migrates a
fresh disposable PostgreSQL database down and forward again, `make sqlc-generate`
updates the generated query package, and `make sqlc-check` proves generation creates
no diff. PostgreSQL 17.11, sqlc 1.31.1, pgx 5.10.0, golang-migrate 4.19.1, and
Testcontainers for Go 0.44.0 are pinned for this baseline.

`pnpm deps:up` is the normal local-dependency bootstrap. It starts PostgreSQL 17.11
and Dex 2.45.1, waits for both health checks, and preserves their data in Compose
volumes. Use `pnpm deps:down` to stop them, or the deliberately destructive
`pnpm deps:reset` when a fresh local state is required. The ephemeral equivalents
use memory-backed storage and an isolated Compose project; stop them with
`pnpm deps:down:ephemeral` before switching modes because both modes bind the
same loopback ports.

Dex is an OIDC-compatible fixture, not a production identity system. Its two
synthetic accounts are `owner@clouddesk.local` and `member@clouddesk.local`, both
with the public local-only password `clouddesk-local-only`. PostgreSQL and the OIDC
client use the same conspicuously non-production fixture value by default. They bind
only to loopback; production uses environment-specific Cognito and RDS secrets from
the approved secret boundary. S3, SQS, and Redis adapters remain absent until a
feature smoke contract needs them.

`pnpm build:images` creates `clouddesk-api:test` and `clouddesk-web:test` without
publishing them. The API uses `backend/` as its narrow build context. The web build
uses the repository root because the authoritative pnpm workspace lockfile lives
there, while the root `.dockerignore` sends only frontend and package-manager inputs.
Run `sh scripts/scan-container-images.sh /tmp/clouddesk-sbom` after building to
create inventories and apply the CI high/critical vulnerability gate locally.

Both multi-stage definitions pin their base image digest, carry OCI source/revision
labels, and run as non-root; no runtime endpoint or secret is baked into either
image. Release automation will replace the local tag and default revision label with
the immutable source revision and promoted digest.

Pull requests, merge queue candidates, and pushes to `main` run the [CI workflow](.github/workflows/ci.yml). See [CI gates and limitations](docs/delivery/ci.md).

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
               plus PostgreSQL migration/sqlc foundations
config/local/  Synthetic, loopback-only local provider configuration
frontend/      Responsive Next.js shells, standalone image build, generated API
               runtime, and component tests
docs/          Implemented M0 reference and proposed product/production architecture
.github/       Read-only CI, dependency updates, and review ownership
scripts/       Small repository-level verification helpers
```

## Delivery Status

No application, AWS resource, Kubernetes object, or release is deployed. See the
[production-readiness checklist](docs/roadmap/production-readiness.md) before making
production claims.
