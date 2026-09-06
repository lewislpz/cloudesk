#!/bin/sh

set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
generated_root=$(mktemp -d "${TMPDIR:-/tmp}/clouddesk-sqlc.XXXXXX")
trap 'rm -r "$generated_root"' EXIT HUP INT TERM

mkdir -p "$generated_root/backend"
cp "$repo_root/backend/sqlc.yaml" "$generated_root/backend/sqlc.yaml"
cp -R "$repo_root/backend/migrations" "$generated_root/backend/migrations"
cp -R "$repo_root/backend/queries" "$generated_root/backend/queries"

(
  cd "$generated_root/backend"
  go run github.com/sqlc-dev/sqlc/cmd/sqlc@v1.31.1 generate -f sqlc.yaml
)

committed="$repo_root/backend/internal/gen/sqlc"
generated="$generated_root/backend/internal/gen/sqlc"

if [ ! -d "$committed" ]; then
  printf 'missing committed sqlc output: backend/internal/gen/sqlc\n' >&2
  exit 1
fi

diff -ru "$committed" "$generated"
test -f "$generated/db.go"
test -f "$generated/querier.go"
test -f "$generated/foundation.sql.go"
grep -q 'func (q \*Queries) GetFoundationMetadata' "$generated/foundation.sql.go"
