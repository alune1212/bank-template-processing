"""错误上下文增强测试。"""

from __future__ import annotations

import argparse
from pathlib import Path
from types import SimpleNamespace

import pytest

from bank_template_processing import main as main_module
from bank_template_processing.merge_folder import MergeInputFile, MergeFolderError, prepare_merge_tasks
from tests.config_factories import make_basic_unit_config, make_config, make_field_mapping


def _make_main_args(tmp_path):
    return argparse.Namespace(
        excel_path="input.xlsx",
        unit_name="单位A",
        month="01",
        output_dir=str(tmp_path / "out"),
        config="config.json",
        merge_folder=None,
        output_filename_template="{unit_name}_{template_name}_{count}人_金额{amount:.2f}元{ext}",
    )


def _noop_logger() -> SimpleNamespace:
    return SimpleNamespace(
        info=lambda *_args, **_kwargs: None,
        warning=lambda *_args, **_kwargs: None,
    )


def test_main_missing_salary_column_reports_context(monkeypatch, tmp_path, caplog):
    args = _make_main_args(tmp_path)
    config = make_config(
        version="2.0",
        unit_name="单位A",
        unit_config=make_basic_unit_config(template_path="tpl.xlsx", field_mappings={}),
    )

    monkeypatch.setattr(main_module, "setup_logging", lambda: None)
    monkeypatch.setattr(main_module, "parse_args", lambda _argv=None: args)
    monkeypatch.setattr(main_module, "validate_cli_mode_args", lambda _args: None)
    monkeypatch.setattr(main_module, "load_config", lambda _path: config)
    monkeypatch.setattr(main_module, "validate_config", lambda _cfg: None)
    monkeypatch.setattr(
        main_module,
        "ExcelReader",
        lambda **_kwargs: type("R", (), {"read_excel": lambda _self, _p: [{"姓名": "张三"}]})(),
    )

    caplog.set_level("ERROR")

    with pytest.raises(SystemExit) as exc_info:
        main_module.main([])

    assert exc_info.value.code == 1
    assert "零工资筛选失败（单位=单位A，规则组=default）" in caplog.text


def test_main_card_number_transform_reports_context(monkeypatch, tmp_path, caplog):
    args = _make_main_args(tmp_path)
    config = make_config(
        version="2.0",
        unit_name="单位A",
        unit_config=make_basic_unit_config(
            template_path="tpl.xlsx",
            field_mappings={"卡号": make_field_mapping(source_column="卡号", transform="card_number")},
            transformations={"card_number": {"luhn_validation": True}},
            validation_rules={},
        ),
    )

    monkeypatch.setattr(main_module, "setup_logging", lambda: None)
    monkeypatch.setattr(main_module, "parse_args", lambda _argv=None: args)
    monkeypatch.setattr(main_module, "validate_cli_mode_args", lambda _args: None)
    monkeypatch.setattr(main_module, "load_config", lambda _path: config)
    monkeypatch.setattr(main_module, "validate_config", lambda _cfg: None)
    monkeypatch.setattr(
        main_module,
        "ExcelReader",
        lambda **_kwargs: type("R", (), {"read_excel": lambda _self, _p: [{"实发工资": "1", "卡号": "123"}]})(),
    )
    monkeypatch.setattr(main_module, "process_group", lambda *_args, **_kwargs: None)

    caplog.set_level("ERROR")

    with pytest.raises(SystemExit) as exc_info:
        main_module.main([])

    assert exc_info.value.code == 1
    assert "数据转换失败（单位=单位A，规则组=default，模板=tpl，第1条数据）" in caplog.text


def test_prepare_merge_tasks_stats_mismatch_reports_context(tmp_path, monkeypatch):
    file_meta = MergeInputFile(
        path=Path("a.xlsx"),
        unit_name="单位A",
        template_name="模板A",
        count=1,
        amount=100.0,
    )
    monkeypatch.setattr(
        "bank_template_processing.merge_folder._scan_merge_input_files", lambda *_args, **_kwargs: [file_meta]
    )
    monkeypatch.setattr(
        "bank_template_processing.merge_folder.resolve_rule_group_for_template",
        lambda *_args, **_kwargs: (
            "default",
            {
                "template_path": "tpl.xlsx",
                "field_mappings": {"金额": {"source_column": "金额", "transform": "amount_decimal"}},
                "transformations": {},
            },
        ),
    )
    monkeypatch.setattr(
        "bank_template_processing.merge_folder._read_generated_file_rows",
        lambda *_args, **_kwargs: ([{"金额": "100"}], set()),
    )

    with pytest.raises(MergeFolderError, match="批量合并统计校验失败（单位=单位A，规则组=default，模板=模板A）"):
        prepare_merge_tasks(
            merge_folder_path=str(tmp_path),
            config={"organization_units": {"单位A": {"template_path": "tpl.xlsx"}}},
            resolve_path_fn=lambda path: path,
            apply_transformations_fn=lambda data, _t, _f: data,
            needs_transformations_fn=lambda _m: False,
            calculate_stats_fn=lambda data, _fm, _t: (1, 999.0),
            needs_month_for_filename=False,
            logger=_noop_logger(),
        )
