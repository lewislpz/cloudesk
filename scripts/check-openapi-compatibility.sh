#!/bin/sh

set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
base_ref=${OPENAPI_BASE_REF:-origin/main}
spec_path=backend/api/openapi.yaml

(
  cd "$repo_root/backend"
  go run github.com/oasdiff/oasdiff@v1.28.0 validate \
    --allow-external-refs=false \
    "$repo_root/$spec_path"
)

if ! git -C "$repo_root" cat-file -e "$base_ref:$spec_path" 2>/dev/null; then
  echo "OpenAPI compatibility baseline is not present at $base_ref; validation completed without a breaking-change comparison."
  exit 0
fi

baseline_dir=$(mktemp -d "${TMPDIR:-/tmp}/cloudesk-openapi-baseline.XXXXXX")
trap 'rm -rf "$baseline_dir"' EXIT HUP INT TERM
git -C "$repo_root" show "$base_ref:$spec_path" >"$baseline_dir/openapi.yaml"

(
  cd "$repo_root/backend"
  go run github.com/oasdiff/oasdiff@v1.28.0 breaking \
    --allow-external-refs=false \
    --fail-on ERR \
    "$baseline_dir/openapi.yaml" \
    "$repo_root/$spec_path"
)
