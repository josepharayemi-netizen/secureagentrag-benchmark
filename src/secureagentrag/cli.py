from __future__ import annotations

import argparse
import json
from pathlib import Path

from .adapters import DeterministicMockAdapter
from .dataset import load_scenarios, validate_dataset
from .reporting import summarize, write_summary
from .runner import run_benchmark
from .preflight import empirical_pilot_preflight


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="secureagentrag")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="validate the source dataset")
    validate.add_argument("--dataset", default="data/scenarios.jsonl")

    pilot = subparsers.add_parser("pilot", help="run the safe deterministic CI pilot")
    pilot.add_argument("--dataset", default="data/scenarios.jsonl")
    pilot.add_argument("--output", default="results/mock_pilot.jsonl")
    pilot.add_argument("--summary", default="results/mock_pilot_summary.json")
    pilot.add_argument("--configurations", default="C0,C1,C2")
    pilot.add_argument("--seeds", default="0,1,2")

    preflight = subparsers.add_parser(
        "preflight", help="report blockers for the 1,944-observation empirical pilot"
    )
    preflight.add_argument("--root", default=".")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "preflight":
        report = empirical_pilot_preflight(Path(args.root))
        print(json.dumps(report.as_dict(), indent=2))
        return 0 if report.ready else 2

    scenarios = load_scenarios(Path(args.dataset))
    errors = validate_dataset(scenarios)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    if args.command == "validate":
        print(json.dumps({"status": "valid", "scenarios": len(scenarios)}))
        return 0

    records = run_benchmark(
        scenarios,
        DeterministicMockAdapter(),
        [item.strip() for item in args.configurations.split(",") if item.strip()],
        [int(item) for item in args.seeds.split(",") if item.strip()],
        args.output,
    )
    summary = summarize(records)
    write_summary(summary, args.summary)
    print(json.dumps({"status": "complete", "observations": len(records), "summary": args.summary}))
    return 0
