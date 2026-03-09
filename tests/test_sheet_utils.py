"""sheet_utils 共享工具测试。"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import bank_template_processing.sheet_utils as sheet_utils


def test_extract_headers_and_get_cell_value():
    rows = [["", "姓名", "金额"], ["张三", 100]]

    headers = sheet_utils.extract_headers(rows, 1)

    assert headers == {"姓名": 2, "金额": 3}
    assert sheet_utils.get_cell_value(rows[1], 1) == "张三"
    assert sheet_utils.get_cell_value(rows[1], 3) is None
    assert sheet_utils.get_cell_value(rows[1], 0) is None


def test_extract_headers_invalid_header_row():
    with pytest.raises(ValueError, match="header_row 配置无效"):
        sheet_utils.extract_headers([["姓名"]], -1)

    with pytest.raises(ValueError, match="header_row 超出文件行数"):
        sheet_utils.extract_headers([["姓名"]], 2)


def test_resolve_column_index_helpers():
    assert sheet_utils.column_letter_to_index("A") == 1
    assert sheet_utils.column_letter_to_index("abc") == 731
    assert sheet_utils.resolve_column_index("姓名", headers={"姓名": 3}) == 3
    assert sheet_utils.resolve_column_index("12") == 12

    with pytest.raises(ValueError, match="无法解析列标识"):
        sheet_utils.resolve_column_index("中文列")

    assert (
        sheet_utils.resolve_column_index_by_mode(
            "姓名",
            headers={"姓名": 2},
            max_columns=3,
            mapping_mode="column_index",
        )
        == 2
    )

    assert sheet_utils.resolve_column_index_by_mode("B", headers={"姓名": 1}, max_columns=2, mapping_mode="column_name") == 2

    with pytest.raises(ValueError, match="超出最大列数"):
        sheet_utils.resolve_column_index_by_mode(
            "NAME",
            headers={"Name": 1},
            max_columns=2,
            mapping_mode="column_name",
        )


def test_convert_xls_cell_branches(monkeypatch):
    empty_cell = SimpleNamespace(ctype=getattr(sheet_utils.xlrd, "XL_CELL_EMPTY", -1), value="")
    assert sheet_utils.convert_xls_cell(empty_cell, 0) is None

    number_cell = SimpleNamespace(ctype=getattr(sheet_utils.xlrd, "XL_CELL_NUMBER", -1), value=12.0)
    assert sheet_utils.convert_xls_cell(number_cell, 0) == 12

    bool_cell = SimpleNamespace(ctype=getattr(sheet_utils.xlrd, "XL_CELL_BOOLEAN", -1), value=1)
    assert sheet_utils.convert_xls_cell(bool_cell, 0) is True

    date_cell = SimpleNamespace(ctype=getattr(sheet_utils.xlrd, "XL_CELL_DATE", -1), value=10)
    monkeypatch.setattr(sheet_utils.xlrd, "xldate_as_datetime", lambda *_args, **_kwargs: "D")
    assert sheet_utils.convert_xls_cell(date_cell, 0) == "D"

    broken_cell = SimpleNamespace(value="raw")
    assert sheet_utils.convert_xls_cell(broken_cell, 0) == "raw"
