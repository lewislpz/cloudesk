#!/bin/sh

set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
generated_dir=$(mktemp -d "${TMPDIR:-/tmp}/cloudesk-generated.XXXXXX")
trap 'rm -rf "$generated_dir"' EXIT HUP INT TERM

OPENAPI_GO_OUTPUT="$generated_dir/backend/internal/gen/openapi" \
OPENAPI_TS_OUTPUT="$generated_dir/frontend/src/lib/api/generated" \
  pnpm --dir "$repo_root" generate:openapi

for generated_path in \
  backend/internal/gen/openapi \
  frontend/src/lib/api/generated
do
  if [ ! -d "$repo_root/$generated_path" ]; then
    echo "missing committed generated directory: $generated_path" >&2
    exit 1
  fi

  diff -ru "$repo_root/$generated_path" "$generated_dir/$generated_path"
done

test -f "$generated_dir/backend/internal/gen/openapi/oas_interfaces_gen.go"
test -f "$generated_dir/frontend/src/lib/api/generated/types.gen.ts"
test -f "$generated_dir/frontend/src/lib/api/generated/sdk.gen.ts"

grep -q 'type GetOrganizationRes interface' \
  "$generated_dir/backend/internal/gen/openapi/oas_interfaces_gen.go"
grep -q 'export type GetOrganizationData' \
  "$generated_dir/frontend/src/lib/api/generated/types.gen.ts"
grep -q 'export const getOrganization' \
  "$generated_dir/frontend/src/lib/api/generated/sdk.gen.ts"

if grep -R -q '__Host-cloudesk_session' "$generated_dir/frontend/src/lib/api/generated"; then
  echo "generated browser client must not request access to the HttpOnly session cookie" >&2
  exit 1
fi
