#!/usr/bin/env bash
set -euo pipefail

python3 .codex/scripts/control.py validate "$@"
