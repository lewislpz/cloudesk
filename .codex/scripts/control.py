#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from control_actions import (
    ControlError,
    create_checkpoint,
    record_gate,
    record_implementation,
    record_metric,
    run_gate,
    select_workspace,
    transition_workspace,
)
from control_bindings import bind_files, bind_git
from control_validation import validate_scope, validate_workspace
from control_evals import run_scenario


def parse_case(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line and not line.startswith((" ", "-")) and ":" in line:
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip()
    return data


def validate_command(workspace: Path) -> int:
    errors = validate_workspace(workspace)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"valid workspace: {workspace}")
    return 0


def run_evals(cases_directory: Path, results_path: Path, baseline_path: Path) -> int:
    results = []
    for case_path in sorted(cases_directory.glob("*.yaml")):
        case = parse_case(case_path)
        if not case.get("scenario") or not case.get("expected_exit"):
            results.append({"id": case.get("id"), "status": "spec-only"})
            continue
        expected = int(case["expected_exit"])
        actual = run_scenario(case["scenario"])
        results.append(
            {
                "actual_exit": actual,
                "expected_exit": expected,
                "id": case["id"],
                "status": "passed" if actual == expected else "failed",
            }
        )
    passed = sum(result["status"] == "passed" for result in results)
    executable = sum(result["status"] != "spec-only" for result in results)
    payload = {
        "executable": executable,
        "passed": passed,
        "pass_rate": passed / executable if executable else 0,
        "results": results,
    }
    results_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    history_path = results_path.parent / (
        datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ") + ".json"
    )
    history_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    minimum = float(baseline.get("minimum_pass_rate", 1))
    print(f"executable evals: {passed}/{executable} passed")
    return 0 if payload["pass_rate"] >= minimum and passed == executable else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Semantic agentic workflow control plane")
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate")
    validate.add_argument("workspace", type=Path)
    transition = commands.add_parser("transition")
    transition.add_argument("workspace", type=Path)
    transition.add_argument("target")
    transition.add_argument("--actor", required=True)
    transition.add_argument("--evidence", action="append", default=[])
    gate = commands.add_parser("record-gate")
    gate.add_argument("workspace", type=Path)
    gate.add_argument("gate")
    gate.add_argument("--actor", required=True)
    gate.add_argument("--evidence", action="append", default=[])
    gate.add_argument("--command", dest="gate_command_text", default="")
    gate.add_argument("--exit-code", type=int)
    run = commands.add_parser("run-gate")
    run.add_argument("workspace", type=Path)
    run.add_argument("gate")
    run.add_argument("--actor", required=True)
    run.add_argument("--repository", type=Path, default=Path("."))
    run.add_argument("gate_command", nargs=argparse.REMAINDER)
    checkpoint = commands.add_parser("checkpoint")
    checkpoint.add_argument("workspace", type=Path)
    checkpoint.add_argument("task_id")
    checkpoint.add_argument("--result", required=True)
    checkpoint.add_argument("--next-action", required=True)
    metric = commands.add_parser("metric")
    metric.add_argument("workspace", type=Path)
    metric.add_argument("name")
    metric.add_argument("value", type=float)
    implementation = commands.add_parser("record-implementation")
    implementation.add_argument("workspace", type=Path)
    implementation.add_argument("--actor", required=True)
    binding = commands.add_parser("bind-git")
    binding.add_argument("workspace", type=Path)
    binding.add_argument("--repository", type=Path, default=Path("."))
    binding.add_argument("--allow", action="append", default=[])
    file_binding = commands.add_parser("bind-files")
    file_binding.add_argument("workspace", type=Path)
    file_binding.add_argument("root", nargs="+")
    file_binding.add_argument("--repository", type=Path, default=Path("."))
    selection = commands.add_parser("select-workspace")
    selection.add_argument("root", type=Path)
    scope = commands.add_parser("validate-scope")
    scope.add_argument("contract", type=Path)
    scope.add_argument("changed_path", nargs="+")
    evals = commands.add_parser("run-evals")
    evals.add_argument("--cases", type=Path, default=Path(".codex/evals/cases"))
    evals.add_argument(
        "--results", type=Path, default=Path(".codex/evals/results/latest.json")
    )
    evals.add_argument(
        "--baseline", type=Path, default=Path(".codex/evals/baselines/minimum.json")
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "validate":
            return validate_command(args.workspace)
        if args.command == "transition":
            transition_workspace(args.workspace, args.target, args.actor, args.evidence)
        elif args.command == "record-gate":
            record_gate(
                args.workspace,
                args.gate,
                args.actor,
                args.evidence,
                args.gate_command_text,
                args.exit_code,
            )
        elif args.command == "run-gate":
            return run_gate(
                args.workspace,
                args.gate,
                args.actor,
                args.gate_command,
                args.repository,
            )
        elif args.command == "checkpoint":
            print(create_checkpoint(args.workspace, args.task_id, args.result, args.next_action))
        elif args.command == "metric":
            record_metric(args.workspace, args.name, args.value)
        elif args.command == "record-implementation":
            record_implementation(args.workspace, args.actor)
        elif args.command == "bind-git":
            bind_git(args.workspace, args.repository, args.allow)
        elif args.command == "bind-files":
            bind_files(args.workspace, args.repository, args.root)
        elif args.command == "select-workspace":
            print(select_workspace(args.root))
        elif args.command == "validate-scope":
            errors = validate_scope(args.contract, args.changed_path)
            if errors:
                raise ControlError("; ".join(errors))
        elif args.command == "run-evals":
            return run_evals(args.cases, args.results, args.baseline)
    except (ControlError, OSError, ValueError, json.JSONDecodeError) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
