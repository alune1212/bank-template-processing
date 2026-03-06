"""文档与运行时默认值同步测试。"""

from __future__ import annotations

import json
from pathlib import Path

from bank_template_processing.main import parse_args


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_docs_and_runtime_defaults_are_aligned():
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    config_doc = (PROJECT_ROOT / "配置文件说明.md").read_text(encoding="utf-8")
    example_config = json.loads((PROJECT_ROOT / "config.example.json").read_text(encoding="utf-8"))
    args = parse_args(["input.xlsx", "单位A", "01"])

    assert example_config["version"] == "2.0"
    assert '"version": "2.0"' in readme
    assert '"version": "2.0"' in config_doc

    assert args.output_filename_template == "{unit_name}_{template_name}_{count}人_金额{amount:.2f}元{ext}"
    assert "{unit_name}_{template_name}_{count}人_金额{amount:.2f}元{ext}" in readme
    assert "{unit_name}_{template_name}_{count}人_金额{amount:.2f}元{ext}" in config_doc
