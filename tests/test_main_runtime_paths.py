"""main 模块运行时分支覆盖测试。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from bank_template_processing import main as main_module


def test_get_executable_dir_non_frozen_returns_project_root(monkeypatch):
    monkeypatch.setattr(sys, "frozen", False, raising=False)

    executable_dir = main_module.get_executable_dir()

    assert executable_dir == Path(main_module.__file__).parents[2].resolve()


def test_get_executable_dir_frozen_returns_executable_dir(monkeypatch):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", "/tmp/bank-template-processing/app.exe", raising=False)

    executable_dir = main_module.get_executable_dir()

    assert executable_dir == Path("/tmp/bank-template-processing")


def test_resolve_path_with_absolute_path_returns_original():
    absolute_path = "/tmp/example.xlsx"
    assert main_module.resolve_path(absolute_path) == absolute_path


def test_resolve_path_with_relative_path_and_custom_base(tmp_path):
    resolved = main_module.resolve_path("templates/test.xlsx", base_dir=tmp_path)
    assert resolved == str((tmp_path / "templates/test.xlsx").resolve())


def test_resolve_path_with_relative_path_and_default_base(monkeypatch, tmp_path):
    monkeypatch.setattr(main_module, "get_executable_dir", lambda: tmp_path)
    resolved = main_module.resolve_path("config.json")
    assert resolved == str((tmp_path / "config.json").resolve())


def test_main_prints_known_error_when_logger_not_initialized(monkeypatch, capsys):
    monkeypatch.setattr(main_module, "setup_logging", lambda: (_ for _ in ()).throw(ValueError("bad-arg")))

    with pytest.raises(SystemExit) as exc_info:
        main_module.main([])

    assert exc_info.value.code == 1
    output = capsys.readouterr().out
    assert "错误：bad-arg" in output


def test_main_prints_unknown_error_when_logger_not_initialized(monkeypatch, capsys):
    monkeypatch.setattr(main_module, "setup_logging", lambda: (_ for _ in ()).throw(RuntimeError("boom")))

    with pytest.raises(SystemExit) as exc_info:
        main_module.main([])

    assert exc_info.value.code == 1
    output = capsys.readouterr().out
    assert "未知错误：boom" in output


def test_generate_output_filename_template_missing_variable_raises():
    with pytest.raises(ValueError, match="输出文件名模板缺少变量"):
        main_module.generate_output_filename(
            unit_name="单位A",
            month="01",
            template_name="模板A",
            template_path="tpl.xlsx",
            count=1,
            amount=1.0,
            output_template="{unit_name}_{unknown}",
        )


def test_calculate_stats_skips_non_dict_mapping_and_invalid_amount():
    count, amount = main_module._calculate_stats(
        data=[{"金额": "100"}, {"金额": "bad"}, {"金额": 50.5}],
        field_mappings={
            "旧格式映射": "A",
            "金额列": {"source_column": "金额", "transform": "amount_decimal"},
        },
        transformations={},
    )
    assert count == 3
    assert amount == 150.5


def test_is_zero_salary_value_unknown_type_returns_false():
    class Unknown:
        pass

    assert main_module._is_zero_salary_value(Unknown()) is False


def test_filter_zero_salary_rows_empty_input():
    assert main_module._filter_zero_salary_rows([]) == []


def test_apply_transformations_old_mapping_warns_once_and_skips_empty_values(caplog):
    caplog.set_level("WARNING")
    data = [{"金额": None, "卡号": "   "}, {"金额": "", "卡号": " "}]
    transformed = main_module.apply_transformations(
        data=data,
        transformations={"amount_decimal": {"decimal_places": 2}},
        field_mappings={"金额": "A", "卡号": "B"},
    )
    assert transformed == data
    assert caplog.text.count("旧格式 field_mappings") == 1


def test_needs_transformations_ignores_non_dict_mapping():
    assert main_module._needs_transformations({"旧": "A", "新": {"transform": "none"}}) is False
    assert main_module._needs_transformations({"新": {"transform": "amount_decimal"}}) is True


def test_main_non_selector_runtime_paths_and_validation(monkeypatch, tmp_path):
    args = argparse.Namespace(
        excel_path="input.xlsx",
        unit_name="单位A",
        month="01",
        output_dir=str(tmp_path / "out"),
        config="config.json",
        merge_folder=None,
        output_filename_template="{unit_name}_{template_name}_{count}人_金额{amount:.2f}元{ext}",
    )

    default_cfg = {
        "template_path": "templates/default.xlsx",
        "header_row": 1,
        "start_row": 2,
        "field_mappings": {
            "金额": {"source_column": "实发工资", "transform": "amount_decimal"},
        },
        "transformations": {},
        "validation_rules": {
            "required_fields": ["实发工资"],
            "data_types": {"实发工资": "numeric"},
            "value_ranges": {"实发工资": {"min": 0}},
        },
        "reader_options": "invalid",  # 触发运行时保护分支
        "month_type_mapping": {"enabled": False},
    }

    config = {
        "version": "2.0",
        "organization_units": {"单位A": default_cfg},
    }

    captured = {"process_called": False}

    monkeypatch.setattr(main_module, "setup_logging", lambda: None)
    monkeypatch.setattr(main_module, "parse_args", lambda _argv=None: args)
    monkeypatch.setattr(main_module, "validate_cli_mode_args", lambda _args: None)
    monkeypatch.setattr(main_module, "get_executable_dir", lambda: tmp_path)
    monkeypatch.setattr(main_module, "load_config", lambda _path: config)
    monkeypatch.setattr(main_module, "validate_config", lambda _cfg: None)
    monkeypatch.setattr(main_module, "get_unit_config", lambda _cfg, _unit, _key=None: default_cfg)
    monkeypatch.setattr(main_module, "resolve_path", lambda path, base_dir=None: str((tmp_path / path).resolve()))
    monkeypatch.setattr(
        main_module,
        "ExcelReader",
        lambda **_kwargs: SimpleNamespace(read_excel=lambda _p: [{"实发工资": "100"}]),
    )
    monkeypatch.setattr(main_module.Validator, "validate_required", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(main_module.Validator, "validate_data_types", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(main_module.Validator, "validate_value_ranges", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(main_module, "_needs_transformations", lambda _m: False)
    monkeypatch.setattr(
        main_module,
        "process_group",
        lambda *_args, **_kwargs: captured.__setitem__("process_called", True),
    )

    main_module.main([])
    assert captured["process_called"] is True


def test_main_dynamic_selector_paths_with_template_fallback_and_transform(monkeypatch, tmp_path):
    args = argparse.Namespace(
        excel_path="input.xlsx",
        unit_name="单位A",
        month="01",
        output_dir=str(tmp_path / "out"),
        config=str(tmp_path / "config.json"),
        merge_folder=None,
        output_filename_template="{unit_name}_{template_name}_{count}人_金额{amount:.2f}元{ext}",
    )

    base_group_cfg = {
        "template_path": "templates/default.xlsx",
        "header_row": 1,
        "start_row": 2,
        "field_mappings": {"金额": {"source_column": "实发工资", "transform": "amount_decimal"}},
        "transformations": {"amount_decimal": {"decimal_places": 2}},
        "validation_rules": {
            "required_fields": ["实发工资"],
            "data_types": {"实发工资": "numeric"},
            "value_ranges": {"实发工资": {"min": 0}},
        },
        "month_type_mapping": {"enabled": False},
    }

    config = {
        "version": "2.0",
        "organization_units": {
            "单位A": {
                "template_selector": {"enabled": True, "default_bank": "A", "bank_column": "开户银行"},
                "default": dict(base_group_cfg),
                "crossbank": dict(base_group_cfg, template_path="templates/crossbank.xlsx"),
            }
        },
    }

    called = {"apply": 0, "process": 0}

    monkeypatch.setattr(main_module, "setup_logging", lambda: None)
    monkeypatch.setattr(main_module, "parse_args", lambda _argv=None: args)
    monkeypatch.setattr(main_module, "validate_cli_mode_args", lambda _args: None)
    monkeypatch.setattr(main_module, "load_config", lambda _path: config)
    monkeypatch.setattr(main_module, "validate_config", lambda _cfg: None)
    monkeypatch.setattr(
        main_module,
        "ExcelReader",
        lambda **_kwargs: SimpleNamespace(
            read_excel=lambda _p: [
                {"姓名": "张三", "实发工资": "100", "开户银行": "A"},
                {"姓名": "李四", "实发工资": "200", "开户银行": "B"},
            ]
        ),
    )
    monkeypatch.setattr(
        main_module.TemplateSelector,
        "group_data",
        lambda _self, _data, _default_bank, _bank_column: {
            "default": {"data": [{"实发工资": "100"}], "template": "", "group_name": "默认模板"},
            "special": {"data": [{"实发工资": "200"}], "template": "templates/special.xlsx", "group_name": "特殊模板"},
        },
    )
    monkeypatch.setattr(
        main_module,
        "resolve_path",
        lambda path, base_dir=None: str((tmp_path / path).resolve()),
    )
    monkeypatch.setattr(main_module.Validator, "validate_required", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(main_module.Validator, "validate_data_types", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(main_module.Validator, "validate_value_ranges", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(main_module, "_needs_transformations", lambda _m: True)
    monkeypatch.setattr(
        main_module,
        "apply_transformations",
        lambda data, _t, _f: called.__setitem__("apply", called["apply"] + 1) or data,
    )
    monkeypatch.setattr(
        main_module,
        "process_group",
        lambda *_args, **_kwargs: called.__setitem__("process", called["process"] + 1),
    )

    main_module.main([])
    assert called["apply"] == 2
    assert called["process"] == 2


def test_main_logs_unknown_error_when_logger_initialized(monkeypatch, caplog):
    caplog.set_level("ERROR")
    monkeypatch.setattr(main_module, "setup_logging", lambda: None)
    monkeypatch.setattr(main_module, "parse_args", lambda _argv=None: (_ for _ in ()).throw(RuntimeError("boom")))

    with pytest.raises(SystemExit) as exc_info:
        main_module.main([])
    assert exc_info.value.code == 1
    assert "未知错误：boom" in caplog.text


def test_main_unit_not_found_exits(monkeypatch):
    args = argparse.Namespace(
        excel_path="input.xlsx",
        unit_name="不存在单位",
        month="01",
        output_dir="output",
        config="config.json",
        merge_folder=None,
        output_filename_template="{unit_name}_{template_name}_{count}人_金额{amount:.2f}元{ext}",
    )
    monkeypatch.setattr(main_module, "setup_logging", lambda: None)
    monkeypatch.setattr(main_module, "parse_args", lambda _argv=None: args)
    monkeypatch.setattr(main_module, "validate_cli_mode_args", lambda _args: None)
    monkeypatch.setattr(main_module, "load_config", lambda _path: {"version": "2.0", "organization_units": {"单位A": {}}})
    monkeypatch.setattr(main_module, "validate_config", lambda _cfg: None)

    with pytest.raises(SystemExit) as exc_info:
        main_module.main([])
    assert exc_info.value.code == 1
