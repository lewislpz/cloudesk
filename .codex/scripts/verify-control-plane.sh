#!/usr/bin/env bash
set -euo pipefail

export PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/codex-control-pycache"
mode="active"
workspace_path=""
case "${1:-}" in
  "")
    ;;
  --active)
    mode="active"
    ;;
  --all)
    mode="all"
    ;;
  --workspace)
    [[ -n "${2:-}" ]] || { echo "--workspace requires a path" >&2; exit 2; }
    mode="workspace"
    workspace_path="$2"
    ;;
  *)
    echo "usage: $0 [--active|--all|--workspace PATH]" >&2
    exit 2
    ;;
esac
eval_results="$(mktemp "${TMPDIR:-/tmp}/codex-control-evals.XXXXXX")"
status_files="$(mktemp "${TMPDIR:-/tmp}/codex-control-workspaces.XXXXXX")"
trap 'rm -f "$eval_results" "$status_files"' EXIT

python3 -m py_compile .codex/scripts/control*.py
bash -n .codex/scripts/*.sh
bash .codex/scripts/validate-workflows.sh
python3 .codex/scripts/control.py run-evals --results "$eval_results"
if [[ "${CODEX_SKIP_PORTABILITY_CHECK:-0}" != "1" ]]; then
  python3 .codex/scripts/control_portability_check.py
fi

validated=0
skipped=0
if [[ "$mode" == "active" ]]; then
  echo "verification scope: active workspaces only; use --all for maintenance/CI and historical validation"
elif [[ "$mode" == "all" ]]; then
  echo "verification scope: all workspaces, including historical states"
else
  echo "verification scope: selected workspace only ($workspace_path)"
fi
validate_status_file() {
  local status_file="$1"
  status="$(sed -n 's/^status: //p' "$status_file" | head -n 1)"
  if [[ "$mode" == "active" && ! "$status" =~ ^(draft|awaiting_approval|approved|in_progress|blocked)$ ]]; then
    skipped=$((skipped + 1))
    return
  fi
  python3 .codex/scripts/control.py validate "${status_file%/status.md}"
  validated=$((validated + 1))
}

if [[ "$mode" == "workspace" ]]; then
  validate_status_file "$workspace_path/status.md"
elif [[ -d .orchestrator ]]; then
  find .orchestrator -mindepth 3 -maxdepth 3 -name status.md -type f | sort >"$status_files"
  while IFS= read -r status_file; do
    validate_status_file "$status_file"
  done <"$status_files"
fi

echo "workspace validation: $validated validated, $skipped skipped ($mode mode)"
if [[ "$mode" == "active" && "$skipped" -gt 0 ]]; then
  echo "notice: $skipped historical workspace(s) were not validated; run '$0 --all' for full-history verification"
fi
