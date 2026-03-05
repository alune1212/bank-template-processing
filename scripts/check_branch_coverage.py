"""检查 coverage.xml 的总体分支覆盖率是否达标。"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="检查 coverage.xml 的 branch-rate 是否达到门槛")
    parser.add_argument("--xml", default="coverage.xml", help="coverage xml 文件路径（默认: coverage.xml）")
    parser.add_argument("--min-branch", type=float, default=85.0, help="最低分支覆盖率百分比（默认: 85）")
    return parser.parse_args()


def _read_branch_rate_percent(xml_path: Path) -> float:
    if not xml_path.exists():
        raise FileNotFoundError(f"未找到覆盖率报告文件: {xml_path}")

    tree = ET.parse(xml_path)
    root = tree.getroot()
    rate_str = root.attrib.get("branch-rate")
    if rate_str is None:
        raise ValueError("coverage.xml 缺少 branch-rate 属性")

    try:
        return float(rate_str) * 100
    except ValueError as e:
        raise ValueError(f"branch-rate 不是有效数字: {rate_str}") from e


def main() -> int:
    args = _parse_args()
    xml_path = Path(args.xml)

    try:
        branch_percent = _read_branch_rate_percent(xml_path)
    except Exception as e:
        print(f"[branch-gate] 读取失败: {e}")
        return 2

    print(f"[branch-gate] 总体分支覆盖率: {branch_percent:.2f}%")
    print(f"[branch-gate] 目标门槛: {args.min_branch:.2f}%")

    if branch_percent < args.min_branch:
        print(
            f"[branch-gate] 未达标: {branch_percent:.2f}% < {args.min_branch:.2f}%",
        )
        return 1

    print("[branch-gate] 达标")
    return 0


if __name__ == "__main__":
    sys.exit(main())
