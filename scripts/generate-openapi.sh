#!/bin/sh

set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
go_output=${OPENAPI_GO_OUTPUT:-$repo_root/backend/internal/gen/openapi}

(
  cd "$repo_root/backend"
  go run github.com/ogen-go/ogen/cmd/ogen@v1.24.0 \
    --clean \
    --config "$repo_root/backend/api/ogen.yaml" \
    --package openapi \
    --target "$go_output" \
    "$repo_root/backend/api/openapi.yaml"
)

pnpm --dir "$repo_root/frontend" generate:openapi
