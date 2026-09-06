ARG IMAGE_REVISION=unknown

FROM node:24.15.0-alpine3.23@sha256:d1b3b4da11eefd5941e7f0b9cf17783fc99d9c6fc34884a665f40a06dbdfc94f AS dependencies

ENV PNPM_HOME=/pnpm \
    PATH=/pnpm:$PATH \
    NEXT_TELEMETRY_DISABLED=1

RUN corepack enable && corepack prepare pnpm@10.15.1 --activate

WORKDIR /app

COPY .npmrc package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY frontend/package.json ./frontend/package.json

RUN --mount=type=cache,id=clouddesk-pnpm,target=/pnpm/store \
    pnpm install --frozen-lockfile --filter @clouddesk/web...

FROM dependencies AS build

ARG IMAGE_REVISION

ENV NEXT_BUILD_ID=$IMAGE_REVISION

COPY frontend ./frontend

RUN pnpm --filter @clouddesk/web build

FROM node:24.15.0-alpine3.23@sha256:d1b3b4da11eefd5941e7f0b9cf17783fc99d9c6fc34884a665f40a06dbdfc94f AS runtime

ARG IMAGE_REVISION=unknown
ARG IMAGE_VERSION=0.0.0

LABEL org.opencontainers.image.title="ClouDesk Web" \
      org.opencontainers.image.description="ClouDesk Next.js web application" \
      org.opencontainers.image.source="https://github.com/lewislpz/cloudesk" \
      org.opencontainers.image.revision="$IMAGE_REVISION" \
      org.opencontainers.image.version="$IMAGE_VERSION" \
      org.opencontainers.image.licenses="UNLICENSED"

WORKDIR /app

ENV HOSTNAME=0.0.0.0 \
    NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000

COPY --from=build --chown=node:node /app/frontend/.next/standalone ./
COPY --from=build --chown=node:node /app/frontend/.next/static ./frontend/.next/static
COPY --from=build --chown=node:node /app/frontend/public ./frontend/public

USER node
EXPOSE 3000
STOPSIGNAL SIGTERM
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
  CMD wget --quiet --spider http://127.0.0.1:3000/ || exit 1
CMD ["node", "frontend/server.js"]
