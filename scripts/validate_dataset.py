#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from secureagentrag.dataset import load_scenarios, validate_dataset


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    scenarios = load_scenarios(ROOT / "data" / "scenarios.jsonl")
    errors = validate_dataset(scenarios)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"validated {len(scenarios)} source scenarios")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
