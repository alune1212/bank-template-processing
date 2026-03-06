"""Check whether the overall branch coverage in coverage.xml meets the threshold."""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check whether coverage.xml branch coverage meets the threshold.")
    parser.add_argument("--xml", default="coverage.xml", help="Path to coverage xml file (default: coverage.xml)")
    parser.add_argument(
        "--min-branch",
        type=float,
        default=85.0,
        help="Minimum overall branch coverage percent (default: 85)",
    )
    return parser.parse_args()


def _read_branch_rate_percent(xml_path: Path) -> float:
    if not xml_path.exists():
        raise FileNotFoundError(f"Coverage report file not found: {xml_path}")

    tree = ET.parse(xml_path)
    root = tree.getroot()
    rate_str = root.attrib.get("branch-rate")
    if rate_str is None:
        raise ValueError("coverage.xml is missing the branch-rate attribute")

    try:
        return float(rate_str) * 100
    except ValueError as e:
        raise ValueError(f"branch-rate is not a valid number: {rate_str}") from e


def main() -> int:
    args = _parse_args()
    xml_path = Path(args.xml)

    try:
        branch_percent = _read_branch_rate_percent(xml_path)
    except Exception as e:
        print(f"[branch-gate] read failed: {e}")
        return 2

    print(f"[branch-gate] overall branch coverage: {branch_percent:.2f}%")
    print(f"[branch-gate] required threshold: {args.min_branch:.2f}%")

    if branch_percent < args.min_branch:
        print(
            f"[branch-gate] threshold not met: {branch_percent:.2f}% < {args.min_branch:.2f}%",
        )
        return 1

    print("[branch-gate] threshold met")
    return 0


if __name__ == "__main__":
    sys.exit(main())
