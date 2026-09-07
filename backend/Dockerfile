FROM golang:1.27.1-alpine3.24@sha256:cf6fca6641884b8433441b2b0652976f975e1d0fdd26d177eaaf8596087f3125 AS build

WORKDIR /src

COPY go.mod go.sum ./
RUN --mount=type=cache,target=/go/pkg/mod \
    go mod download

COPY cmd ./cmd
COPY internal ./internal

RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    CGO_ENABLED=0 GOOS=linux go build \
      -buildvcs=false \
      -tags timetzdata \
      -trimpath \
      -ldflags="-s -w -buildid=" \
      -o /out/api \
      ./cmd/api

FROM scratch AS runtime

ARG IMAGE_REVISION=unknown
ARG IMAGE_VERSION=0.0.0

LABEL org.opencontainers.image.title="ClouDesk API" \
      org.opencontainers.image.description="ClouDesk Go API" \
      org.opencontainers.image.source="https://github.com/lewislpz/cloudesk" \
      org.opencontainers.image.revision="$IMAGE_REVISION" \
      org.opencontainers.image.version="$IMAGE_VERSION" \
      org.opencontainers.image.licenses="UNLICENSED"

COPY --from=build /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/ca-certificates.crt
COPY --from=build /out/api /app/api

ENV APP_ENV=production \
    API_HTTP_ADDRESS=:8080

USER 65532:65532
EXPOSE 8080
STOPSIGNAL SIGTERM
ENTRYPOINT ["/app/api"]
