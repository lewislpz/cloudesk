#!/usr/bin/env bash
set -euo pipefail

export PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/codex-control-pycache"
failed=0
required_paths=(
  .codex/config.json
  .codex/MANUAL.md
  .codex/PORTABILITY.md
  .codex/templates/AGENTS.md
  .codex/templates/status.md
  .codex/templates/plan.md
  .codex/templates/delegation-contract.md
  .codex/templates/delegation-contract.json
  .codex/templates/gate-receipts.json
  .codex/templates/checkpoint.json
  .codex/schemas/workspace-status.schema.json
  .codex/schemas/config.schema.json
  .codex/evals/README.md
  .codex/skills/README.md
  .codex/rules/agent-security.md
  .codex/rules/risk-gates.md
  .codex/scripts/control.py
  .codex/scripts/bootstrap.sh
  .codex/scripts/doctor.sh
  .codex/scripts/transition-workspace.sh
  .codex/scripts/run-gate.sh
  .codex/scripts/run-evals.sh
  .codex/scripts/bind-files.sh
  .codex/scripts/control_skill_validation.py
)

for required_instruction in \
  'Slash Alias Routing' \
  '.codex/prompts/<alias>.md' \
  'Unknown aliases'; do
  if ! rg -Fq "$required_instruction" .codex/templates/AGENTS.md; then
    echo "missing context-free slash routing instruction: $required_instruction" >&2
    failed=1
  fi
done
scan_paths=(.codex)
[[ -f GUIDELINES.md ]] && scan_paths+=(GUIDELINES.md)

for path in "${required_paths[@]}"; do
  if [[ ! -e "$path" ]]; then
    echo "missing required path: $path" >&2
    failed=1
  fi
done

stale_references="$(mktemp "${TMPDIR:-/tmp}/codex-stale-references.XXXXXX")"
obsolete_references="$(mktemp "${TMPDIR:-/tmp}/codex-obsolete-references.XXXXXX")"
trap 'rm -f "$stale_references" "$obsolete_references"' EXIT

if rg -n '/Users/[^/]+/|/home/[^/]+/|@architect' "${scan_paths[@]}" \
  --glob '!**/validate-workflows.sh' >"$stale_references"; then
  cat "$stale_references" >&2
  echo "stale or non-operational references found" >&2
  failed=1
fi

if rg -n 'latest approved plan|delegate with `\\.codex/templates/delegation-contract\\.md`|based on `\\.codex/templates/delegation-contract\\.md`' "${scan_paths[@]}" \
  --glob '!**/validate-workflows.sh' >"$obsolete_references"; then
  cat "$obsolete_references" >&2
  echo "obsolete operational references found" >&2
  failed=1
fi

for workflow in audit think forge test pr ship; do
  if [[ ! -f ".codex/workflows/$workflow.md" ]]; then
    echo "missing workflow: $workflow" >&2
    failed=1
  fi
done

for skill in .codex/skills/*/SKILL.md; do
  if ! sed -n '1,12p' "$skill" | rg -q 'description:.*Use when|^  Use when'; then
    echo "skill description must declare a Use when trigger: $skill" >&2
    failed=1
  fi
done

for prompt in audit think forge test pr ship resume; do
  if [[ ! -f ".codex/prompts/$prompt.md" ]]; then
    echo "missing prompt: $prompt" >&2
    failed=1
  fi
done

for eval_case in .codex/evals/cases/*.yaml; do
  for field in id target prompt setup expected forbidden; do
    if ! grep -Eq "^${field}:" "$eval_case"; then
      echo "missing eval field '$field': $eval_case" >&2
      failed=1
    fi
  done

  target="$(sed -n 's/^target: //p' "$eval_case" | head -n 1)"
  if [[ -n "$target" && ! -e "$target" ]]; then
    echo "missing eval target '$target': $eval_case" >&2
    failed=1
  fi
done

if find .codex -name .DS_Store -print -quit | rg -q .; then
  echo "platform-specific .DS_Store found under .codex" >&2
  failed=1
fi

while IFS= read -r json_file; do
  if ! python3 -m json.tool "$json_file" >/dev/null; then
    echo "invalid JSON: $json_file" >&2
    failed=1
  fi
done < <(find .codex -type f -name '*.json' | sort)

python3 -m py_compile .codex/scripts/control*.py
python3 .codex/scripts/control_config_check.py
python3 .codex/scripts/control_skill_validation.py

for module in .codex/scripts/control*.py; do
  if [[ "$(wc -l < "$module")" -gt 200 ]]; then
    echo "control module exceeds 200 lines: $module" >&2
    failed=1
  fi
done

if [[ "$failed" -ne 0 ]]; then
  exit 1
fi

echo "workflow package is internally consistent"
