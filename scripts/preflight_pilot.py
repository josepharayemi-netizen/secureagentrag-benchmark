#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from secureagentrag.preflight import empirical_pilot_preflight


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    report = empirical_pilot_preflight(ROOT)
    print(json.dumps(report.as_dict(), indent=2))
    return 0 if report.ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
