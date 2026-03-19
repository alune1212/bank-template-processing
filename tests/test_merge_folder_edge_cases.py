"""merge_folder 私有分支与失败路径测试。"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import bank_template_processing.merge_folder as merge_folder_module
from bank_template_processing.config_loader import ConfigError
from bank_template_processing.merge_folder import (
    MergeFolderError,
    MergeInputFile,
    _build_field_bindings,
    _build_merge_output_group_config,
    _convert_xls_cell,
    _extract_headers,
    _get_cell_value,
    _infer_month_param_from_single_value,
    _is_empty_value,
    _merge_input_file_sort_key,
    _read_all_rows,
    _read_generated_file_rows,
    _read_xls_rows,
    _read_xlsx_rows,
    _resolve_month_column,
    _scan_merge_input_files,
    _select_month_param_on_conflict,
    _split_prefix_to_unit_and_template,
    infer_month_param_from_values,
    parse_merge_filename,
    prepare_merge_tasks,
    resolve_rule_group_for_template,
)
from tests.config_factories import make_basic_unit_config, make_config, make_field_mapping, make_multi_group_unit_config


def _noop_logger() -> SimpleNamespace:
    return SimpleNamespace(
        info=lambda *_args, **_kwargs: None,
        warning=lambda *_args, **_kwargs: None,
    )


def _make_merge_rule_group(
    template_path: str = "tpl.xlsx",
    *,
    field_mappings: object | None = None,
    transformations: object | None = None,
    **extra: Any,
) -> dict[str, Any]:
    return make_basic_unit_config(
        template_path=template_path,
        field_mappings={} if field_mappings is None else field_mappings,
        transformations={} if transformations is None else transformations,
        **extra,
    )


def _make_generated_rows_group_config(
    *,
    header_row: int = 1,
    start_row: int = 2,
    clear_rows: dict[str, int] | None = None,
    month_target_column: str | None = None,
) -> dict[str, Any]:
    config = _make_merge_rule_group(
        header_row=header_row,
        start_row=start_row,
        field_mappings={"姓名": make_field_mapping(source_column="姓名", target_column="姓名")},
    )
    if clear_rows is not None:
        config["clear_rows"] = clear_rows
    if month_target_column is not None:
        config["month_type_mapping"] = {"enabled": True, "target_column": month_target_column}
    return config


def _call_prepare_merge_tasks(
    merge_folder_path: Path | str,
    config: dict[str, Any],
    **overrides: Any,
):
    kwargs: dict[str, Any] = {
        "resolve_path_fn": lambda path: path,
        "apply_transformations_fn": lambda data, _t, _f: data,
        "needs_transformations_fn": lambda _m: False,
        "calculate_stats_fn": lambda data, _fm, _t: (len(data), 0.0),
        "needs_month_for_filename": False,
        "logger": _noop_logger(),
    }
    kwargs.update(overrides)
    return prepare_merge_tasks(
        merge_folder_path=str(merge_folder_path),
        config=config,
        **kwargs,
    )


def test_split_prefix_missing_template_name_raises():
    with pytest.raises(MergeFolderError, match="缺少模板名称"):
        _split_prefix_to_unit_and_template("单位A_", ["单位A"])


def test_split_prefix_unmatched_unit_raises():
    with pytest.raises(MergeFolderError, match="无法匹配单位名称"):
        _split_prefix_to_unit_and_template("未知单位_模板A", ["单位A"])


def test_scan_merge_input_files_empty_folder_raises(tmp_path):
    with pytest.raises(MergeFolderError, match="未找到可合并的 Excel 文件"):
        _scan_merge_input_files(tmp_path, ["单位A"])


def test_parse_merge_filename_unsupported_extension_raises():
    with pytest.raises(MergeFolderError, match="不支持的合并文件格式"):
        parse_merge_filename(Path("单位A_模板A_1人_金额1.00元.txt"), ["单位A"])


def test_resolve_rule_group_for_template_error_paths():
    with pytest.raises(ConfigError, match="未找到单位配置"):
        resolve_rule_group_for_template({"organization_units": {}}, "单位A", "模板")

    cfg_conflict = make_config(
        organization_units={
            "单位A": make_multi_group_unit_config(
                {
                    "default": _make_merge_rule_group("default.xlsx"),
                    "crossbank": _make_merge_rule_group("cross.xlsx"),
                },
                template_selector={"default_group_name": "同名", "special_group_name": "同名"},
            )
        }
    )
    with pytest.raises(MergeFolderError, match="同时命中多个组名配置"):
        resolve_rule_group_for_template(cfg_conflict, "单位A", "同名")

    cfg_legacy = make_config(organization_units={"单位A": _make_merge_rule_group("tpl.xlsx")})
    rule_group, _ = resolve_rule_group_for_template(cfg_legacy, "单位A", "tpl")
    assert rule_group == "default"

    cfg_no_match = make_config(
        organization_units={
            "单位A": make_multi_group_unit_config(
                {
                    "default": _make_merge_rule_group("d.xlsx"),
                    "crossbank": _make_merge_rule_group("c.xlsx"),
                }
            )
        }
    )
    with pytest.raises(MergeFolderError, match="无法为单位"):
        resolve_rule_group_for_template(cfg_no_match, "单位A", "不存在模板")

    cfg_multi_stem = make_config(
        organization_units={
            "单位A": make_multi_group_unit_config(
                {
                    "default": _make_merge_rule_group("same.xlsx"),
                    "crossbank": _make_merge_rule_group("same.xlsx"),
                }
            )
        }
    )
    with pytest.raises(MergeFolderError, match="匹配到多个规则组"):
        resolve_rule_group_for_template(cfg_multi_stem, "单位A", "same")

    cfg_missing_crossbank = make_config(
        organization_units={
            "单位A": make_multi_group_unit_config(
                {
                    "default": _make_merge_rule_group("default.xlsx"),
                },
                template_selector={"special_group_name": "跨行模板"},
            )
        }
    )
    with pytest.raises(ConfigError, match="未找到规则组 'crossbank'"):
        resolve_rule_group_for_template(cfg_missing_crossbank, "单位A", "跨行模板")


def test_resolve_rule_group_for_template_uses_selector_default_group_names():
    cfg = make_config(
        organization_units={
            "单位A": make_multi_group_unit_config(
                {
                    "default": _make_merge_rule_group("default.xlsx"),
                    "crossbank": _make_merge_rule_group("cross.xlsx"),
                },
                template_selector={"enabled": True, "default_bank": "农业银行"},
            )
        }
    )

    default_group, _ = resolve_rule_group_for_template(cfg, "单位A", "default")
    crossbank_group, _ = resolve_rule_group_for_template(cfg, "单位A", "special")

    assert default_group == "default"
    assert crossbank_group == "crossbank"


def test_infer_month_param_from_values_empty_raises():
    with pytest.raises(MergeFolderError, match="未在输入文件中读取到月类型值"):
        infer_month_param_from_values(set(), {"month_format": "{month}月收入"})


def test_merge_input_file_sort_key_stat_failure_raises(tmp_path, monkeypatch):
    file_path = tmp_path / "单位A_模板A_1人_金额1.00元.xlsx"
    file_path.write_text("x", encoding="utf-8")

    def fake_stat(_self):
        raise OSError("stat failed")

    monkeypatch.setattr(type(file_path), "stat", fake_stat)

    with pytest.raises(MergeFolderError, match="读取文件修改时间失败"):
        _merge_input_file_sort_key(file_path)


def test_extract_headers_invalid_header_row_raises():
    with pytest.raises(MergeFolderError, match="header_row 配置无效"):
        _extract_headers([["a"]], -1, Path("a.xlsx"))


def test_extract_headers_header_row_zero_returns_empty():
    assert _extract_headers([["a"]], 0, Path("a.xlsx")) == {}


def test_extract_headers_header_row_out_of_range_raises():
    with pytest.raises(MergeFolderError, match="header_row 超出文件行数"):
        _extract_headers([["a"]], 2, Path("a.xlsx"))


def test_extract_headers_skips_empty_cells():
    headers = _extract_headers([["", "  ", "姓名"]], 1, Path("a.xlsx"))
    assert headers == {"姓名": 3}


def test_build_field_bindings_missing_source_column_raises():
    with pytest.raises(MergeFolderError, match="缺少 source_column"):
        _build_field_bindings(
            {"姓名": {"target_column": "A"}},
            {"姓名": 1},
            5,
            None,
            Path("a.xlsx"),
        )


def test_build_field_bindings_unresolvable_target_raises(monkeypatch):
    def fake_resolve(*_args, **_kwargs):
        raise ValueError("bad column")

    monkeypatch.setattr(merge_folder_module, "resolve_column_index_by_mode", fake_resolve)
    with pytest.raises(MergeFolderError, match="无法解析字段"):
        _build_field_bindings(
            {"姓名": {"source_column": "姓名", "target_column": "坏列"}},
            {"姓名": 1},
            5,
            None,
            Path("a.xlsx"),
        )


def test_build_field_bindings_old_format_mapping():
    bindings = _build_field_bindings(
        {"姓名": "A"},
        {},
        5,
        None,
        Path("a.xlsx"),
    )
    assert bindings == [("姓名", 1)]


def test_resolve_month_column_disabled_returns_none():
    assert _resolve_month_column({}, {}, 1, None, Path("a.xlsx")) is None


def test_resolve_month_column_invalid_target_raises(monkeypatch):
    def fake_resolve(*_args, **_kwargs):
        raise ValueError("bad")

    monkeypatch.setattr(merge_folder_module, "resolve_column_index_by_mode", fake_resolve)

    with pytest.raises(MergeFolderError, match="month_type_mapping.target_column"):
        _resolve_month_column(
            {"month_type_mapping": {"enabled": True, "target_column": "坏列"}},
            {},
            5,
            None,
            Path("a.xlsx"),
        )


def test_read_all_rows_unsupported_extension_raises():
    with pytest.raises(MergeFolderError, match="不支持的文件格式"):
        _read_all_rows(Path("a.unsupported"))


def test_read_xlsx_rows_without_active_sheet_raises(monkeypatch):
    class FakeWorkbook:
        active = None

        @staticmethod
        def close():
            return None

    monkeypatch.setattr(merge_folder_module.openpyxl, "load_workbook", lambda *_args, **_kwargs: FakeWorkbook())
    with pytest.raises(MergeFolderError, match="没有工作表"):
        _read_xlsx_rows(Path("a.xlsx"))


def test_read_xls_rows_and_convert_number_exception_branch(monkeypatch):
    number_type = getattr(merge_folder_module.xlrd, "XL_CELL_NUMBER")
    text_type = getattr(merge_folder_module.xlrd, "XL_CELL_TEXT")

    sheet = SimpleNamespace(
        nrows=1,
        ncols=2,
        cell=lambda _row, col: (
            SimpleNamespace(ctype=number_type, value=object())
            if col == 0
            else SimpleNamespace(ctype=text_type, value="x")
        ),
    )
    workbook = SimpleNamespace(sheet_by_index=lambda _idx: sheet, datemode=0)
    monkeypatch.setattr(merge_folder_module.xlrd, "open_workbook", lambda *_args, **_kwargs: workbook)

    rows = _read_xls_rows(Path("a.xls"))
    assert len(rows) == 1
    assert rows[0][1] == "x"


def test_get_cell_value_and_is_empty_value_branches():
    assert _get_cell_value(["a"], 0) is None
    assert _get_cell_value(["a"], 2) is None
    assert _get_cell_value(["a"], 1) == "a"

    assert _is_empty_value(None) is True
    assert _is_empty_value("   ") is True
    assert _is_empty_value("x") is False


def test_read_generated_file_rows_start_row_invalid(monkeypatch):
    monkeypatch.setattr(merge_folder_module, "_read_all_rows", lambda _path: [["姓名", "用途"], ["张三", "01月收入"]])
    with pytest.raises(MergeFolderError, match="start_row 配置无效"):
        _read_generated_file_rows(
            Path("a.xlsx"),
            _make_generated_rows_group_config(start_row=0),
        )


def test_read_generated_file_rows_skips_empty_rows_and_collects_month_values(monkeypatch):
    monkeypatch.setattr(
        merge_folder_module,
        "_read_all_rows",
        lambda _path: [
            ["姓名", "用途"],
            ["张三", "01月收入"],
            ["", ""],
            ["李四", ""],
        ],
    )
    rows, month_values = _read_generated_file_rows(
        Path("a.xlsx"),
        _make_generated_rows_group_config(month_target_column="用途"),
    )
    assert [row["姓名"] for row in rows] == ["张三", "李四"]
    assert month_values == {"01月收入"}


def test_read_generated_file_rows_respects_clear_rows_boundary(monkeypatch):
    monkeypatch.setattr(
        merge_folder_module,
        "_read_all_rows",
        lambda _path: [
            ["姓名", "用途"],
            ["张三", "01月收入"],
            ["李四", "01月收入"],
            ["制表人", ""],
        ],
    )

    rows, month_values = _read_generated_file_rows(
        Path("a.xlsx"),
        _make_generated_rows_group_config(clear_rows={"end_row": 3}, month_target_column="用途"),
    )

    assert [row["姓名"] for row in rows] == ["张三", "李四"]
    assert month_values == {"01月收入"}


def test_read_generated_file_rows_clear_rows_start_row_defaults_from_group(monkeypatch):
    monkeypatch.setattr(
        merge_folder_module,
        "_read_all_rows",
        lambda _path: [
            ["说明", ""],
            ["姓名", "用途"],
            ["张三", "01月收入"],
            ["李四", "01月收入"],
            ["尾注", ""],
        ],
    )

    rows, _month_values = _read_generated_file_rows(
        Path("a.xlsx"),
        _make_generated_rows_group_config(header_row=2, start_row=3, clear_rows={"end_row": 4}),
    )

    assert [row["姓名"] for row in rows] == ["张三", "李四"]


def test_prepare_merge_tasks_precheck_error_paths(tmp_path, monkeypatch):
    with pytest.raises(FileNotFoundError, match="合并目录不存在"):
        _call_prepare_merge_tasks(tmp_path / "not-exists", {"organization_units": {"单位A": {}}})

    not_dir = tmp_path / "not_dir.txt"
    not_dir.write_text("x", encoding="utf-8")
    with pytest.raises(MergeFolderError, match="合并路径不是目录"):
        _call_prepare_merge_tasks(not_dir, {"organization_units": {"单位A": {}}})

    with pytest.raises(ConfigError, match="配置缺少 organization_units"):
        _call_prepare_merge_tasks(tmp_path, {"organization_units": []})

    file_path = tmp_path / "单位A_模板A_1人_金额1.00元.xlsx"
    file_path.write_text("x", encoding="utf-8")
    monkeypatch.setattr(
        merge_folder_module,
        "resolve_rule_group_for_template",
        lambda *_args, **_kwargs: ("default", {"template_path": ""}),
    )
    with pytest.raises(ConfigError, match="未配置 template_path"):
        _call_prepare_merge_tasks(tmp_path, {"organization_units": {"单位A": {"template_path": "a.xlsx"}}})


def test_prepare_merge_tasks_amount_mismatch_raises(tmp_path, monkeypatch):
    file_meta = MergeInputFile(
        path=Path("x.xlsx"),
        unit_name="单位A",
        template_name="模板A",
        count=1,
        amount=100.0,
    )
    monkeypatch.setattr(merge_folder_module, "_scan_merge_input_files", lambda *_args, **_kwargs: [file_meta])
    monkeypatch.setattr(
        merge_folder_module,
        "resolve_rule_group_for_template",
        lambda *_args, **_kwargs: (
            "default",
            _make_merge_rule_group(
                "tpl.xlsx",
                field_mappings={"金额": make_field_mapping(source_column="金额", transform="amount_decimal")},
            ),
        ),
    )
    monkeypatch.setattr(
        merge_folder_module,
        "_read_generated_file_rows",
        lambda *_args, **_kwargs: ([{"金额": "100"}], set()),
    )

    with pytest.raises(MergeFolderError, match="金额校验失败"):
        _call_prepare_merge_tasks(
            tmp_path,
            {"organization_units": {"单位A": {"template_path": "tpl.xlsx"}}},
            calculate_stats_fn=lambda data, _fm, _t: (1, 999.0),
        )


def test_prepare_merge_tasks_transforms_before_post_validation(tmp_path, monkeypatch):
    file_meta = MergeInputFile(
        path=Path("x.xlsx"),
        unit_name="单位A",
        template_name="模板A",
        count=1,
        amount=0.0,
    )
    monkeypatch.setattr(merge_folder_module, "_scan_merge_input_files", lambda *_args, **_kwargs: [file_meta])
    monkeypatch.setattr(
        merge_folder_module,
        "resolve_rule_group_for_template",
        lambda *_args, **_kwargs: (
            "default",
            _make_merge_rule_group(
                "tpl.xlsx",
                field_mappings={
                    "工资卡卡号": make_field_mapping(
                        source_column="工资卡卡号",
                        transform="card_number",
                    )
                },
                transformations={
                    "card_number": {
                        "remove_formatting": True,
                        "luhn_validation": False,
                    }
                },
                validation_rules={
                    "required_fields": ["工资卡卡号"],
                    "data_types": {"工资卡卡号": "integer"},
                },
            ),
        ),
    )
    monkeypatch.setattr(
        merge_folder_module,
        "_read_generated_file_rows",
        lambda *_args, **_kwargs: ([{"工资卡卡号": "6222 0212 3456 7890 128"}], set()),
    )

    tasks = _call_prepare_merge_tasks(
        tmp_path,
        {"organization_units": {"单位A": {"template_path": "tpl.xlsx"}}},
        apply_transformations_fn=None,
        needs_transformations_fn=None,
    )

    assert len(tasks) == 1
    assert tasks[0].group_data[0]["工资卡卡号"] == "6222021234567890128"


def test_convert_xls_cell_all_branches(monkeypatch):
    empty_cell = SimpleNamespace(ctype=getattr(merge_folder_module.xlrd, "XL_CELL_EMPTY"), value="")
    assert _convert_xls_cell(empty_cell, 0) is None

    number_int_cell = SimpleNamespace(ctype=getattr(merge_folder_module.xlrd, "XL_CELL_NUMBER"), value=12.0)
    number_float_cell = SimpleNamespace(ctype=getattr(merge_folder_module.xlrd, "XL_CELL_NUMBER"), value=12.5)
    assert _convert_xls_cell(number_int_cell, 0) == 12
    assert _convert_xls_cell(number_float_cell, 0) == 12.5

    bool_cell = SimpleNamespace(ctype=getattr(merge_folder_module.xlrd, "XL_CELL_BOOLEAN"), value=1)
    assert _convert_xls_cell(bool_cell, 0) is True

    date_cell = SimpleNamespace(ctype=getattr(merge_folder_module.xlrd, "XL_CELL_DATE"), value=10)
    monkeypatch.setattr(merge_folder_module.xlrd, "xldate_as_datetime", lambda *_args, **_kwargs: "D")
    assert _convert_xls_cell(date_cell, 0) == "D"

    monkeypatch.setattr(
        merge_folder_module.xlrd,
        "xldate_as_datetime",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("bad date")),
    )
    assert _convert_xls_cell(date_cell, 0) == 10

    text_cell = SimpleNamespace(ctype=getattr(merge_folder_module.xlrd, "XL_CELL_TEXT"), value="abc")
    assert _convert_xls_cell(text_cell, 0) == "abc"


def test_infer_month_param_from_single_value_errors():
    with pytest.raises(MergeFolderError, match="month_format 必须是字符串"):
        _infer_month_param_from_single_value("01月收入", {"month_format": 123})

    with pytest.raises(MergeFolderError, match="month_format 缺少变量"):
        _infer_month_param_from_single_value("01-值", {"month_format": "{month}-{missing}"})

    with pytest.raises(MergeFolderError, match="month_format 格式错误"):
        _infer_month_param_from_single_value("x", {"month_format": "{month"})

    with pytest.raises(MergeFolderError, match="匹配到多个月份"):
        _infer_month_param_from_single_value("固定值", {"month_format": "固定值"})

    with pytest.raises(MergeFolderError, match="无法从月类型值推断月份参数"):
        _infer_month_param_from_single_value("未知值", {"month_format": "{month}月收入"})


def test_select_month_param_on_conflict_text_fallback():
    assert _select_month_param_on_conflict({"补偿金", "其他"}) == "补偿金"
    assert _select_month_param_on_conflict({"beta", "alpha"}) == "alpha"


def test_build_merge_output_group_config_branches():
    base_config = {"field_mappings": {"姓名": {"source_column": "姓名"}}}
    assert _build_merge_output_group_config(base_config, keep_row_month_values=False) == base_config
    assert _build_merge_output_group_config(base_config, keep_row_month_values=True) == base_config

    cfg = {
        "field_mappings": {"姓名": {"source_column": "姓名"}},
        "month_type_mapping": {"enabled": True, "target_column": "用途"},
    }
    updated = _build_merge_output_group_config(cfg, keep_row_month_values=True)
    assert updated["month_type_mapping"] == {"enabled": False}
    assert "__merge_month_value__" in updated["field_mappings"]
