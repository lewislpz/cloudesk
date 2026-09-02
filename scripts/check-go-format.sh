#!/bin/sh
set -eu

unformatted_files="$(find backend -type f -name '*.go' -exec gofmt -l {} +)"

if [ -n "$unformatted_files" ]; then
  printf '%s\n' 'Go files require formatting:'
  printf '%s\n' "$unformatted_files"
  exit 1
fi
