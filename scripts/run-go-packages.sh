#!/bin/sh
set -eu

command_name="${1:-}"

case "$command_name" in
  generate | test | vet) ;;
  *)
    printf 'unsupported Go command: %s\n' "$command_name" >&2
    exit 2
    ;;
esac

first_go_file="$(find backend -type f -name '*.go' -print -quit)"

if [ -z "$first_go_file" ]; then
  exit 0
fi

exec go -C backend "$command_name" ./...
