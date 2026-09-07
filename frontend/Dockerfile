ARG IMAGE_REVISION=unknown

FROM node:26.8.1-alpine3.24@sha256:2d984a15c9b54fd0aeb608b8e0d0d83529eb34d2966db27a1fb4f1edc3d298a3 AS base

RUN apk add --no-cache libcrypto3=3.5.8-r0 libssl3=3.5.8-r0

FROM base AS dependencies

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

FROM base AS runtime

ARG IMAGE_REVISION=unknown
ARG IMAGE_VERSION=0.0.0

# The standalone server needs Node, not package installation tools.
RUN rm -rf /usr/local/lib/node_modules /opt/yarn-* \
    /usr/local/bin/npm /usr/local/bin/npx /usr/local/bin/corepack \
    /usr/local/bin/yarn /usr/local/bin/yarnpkg

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
