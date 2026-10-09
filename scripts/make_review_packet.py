#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from secureagentrag.packets import build_review_packet


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("language", choices=["fr", "ar", "sw", "yo", "ha"])
    parser.add_argument("--output", default="review_packets")
    args = parser.parse_args()
    packet = build_review_packet(ROOT, Path(args.output), args.language)
    print(json.dumps(packet.as_dict(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
