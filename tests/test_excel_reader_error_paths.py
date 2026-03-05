"""ExcelReader 失败路径与边界分支测试。"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import bank_template_processing.excel_reader as excel_reader_module
from bank_template_processing.excel_reader import ExcelError, ExcelReader


def test_should_skip_row_branches():
    reader = ExcelReader(row_filter={})
    assert reader._should_skip_row(["a"], ["列"]) is False

    reader = ExcelReader(row_filter={"exclude_keywords": []})
    assert reader._should_skip_row(["a"], ["列"]) is False

    reader = ExcelReader(row_filter={"exclude_keywords": ["忽略"]})
    assert reader._should_skip_row(["忽略"], ["列"]) is True
    assert reader._should_skip_row(["保留"], ["列"]) is False


def test_convert_xls_cell_with_unreadable_ctype_returns_raw_value():
    reader = ExcelReader()
    broken_cell = SimpleNamespace(value="raw")
    assert reader._convert_xls_cell(broken_cell, 0) == "raw"


def test_read_xlsx_without_active_sheet_raises(tmp_path, monkeypatch):
    file_path = tmp_path / "no_sheet.xlsx"
    file_path.write_text("dummy", encoding="utf-8")

    class FakeWorkbook:
        active = None

    monkeypatch.setattr(excel_reader_module.openpyxl, "load_workbook", lambda *_args, **_kwargs: FakeWorkbook())

    with pytest.raises(ExcelError, match="无法读取.xlsx文件"):
        ExcelReader()._read_xlsx(str(file_path))


def test_read_xlsx_load_failure_raises(tmp_path, monkeypatch):
    file_path = tmp_path / "bad.xlsx"
    file_path.write_text("dummy", encoding="utf-8")

    monkeypatch.setattr(
        excel_reader_module.openpyxl,
        "load_workbook",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("bad file")),
    )

    with pytest.raises(ExcelError, match="无法读取.xlsx文件"):
        ExcelReader()._read_xlsx(str(file_path))


def test_read_csv_empty_file_returns_empty(tmp_path):
    file_path = tmp_path / "empty.csv"
    file_path.write_text("", encoding="utf-8")
    result = ExcelReader()._read_csv(str(file_path))
    assert result == []


def test_read_csv_header_row_out_of_range_raises(tmp_path):
    file_path = tmp_path / "a.csv"
    file_path.write_text("a,b\n1,2\n", encoding="utf-8")
    with pytest.raises(ExcelError, match="无法读取\\.csv文件"):
        ExcelReader(header_row=5)._read_csv(str(file_path))


def test_read_xls_header_row_invalid_raises(tmp_path, monkeypatch):
    file_path = tmp_path / "a.xls"
    file_path.write_text("dummy", encoding="utf-8")

    sheet = SimpleNamespace(nrows=1, ncols=1, cell_value=lambda *_args: "H", cell=lambda *_args: None)
    workbook = SimpleNamespace(sheet_by_index=lambda _idx: sheet, datemode=0)
    monkeypatch.setattr(excel_reader_module.xlrd, "open_workbook", lambda *_args, **_kwargs: workbook)

    with pytest.raises(ExcelError, match="无法读取\\.xls文件"):
        ExcelReader(header_row=0)._read_xls(str(file_path))


def test_read_xls_header_row_out_of_range_raises(tmp_path, monkeypatch):
    file_path = tmp_path / "a.xls"
    file_path.write_text("dummy", encoding="utf-8")

    sheet = SimpleNamespace(nrows=1, ncols=1, cell_value=lambda *_args: "H", cell=lambda *_args: None)
    workbook = SimpleNamespace(sheet_by_index=lambda _idx: sheet, datemode=0)
    monkeypatch.setattr(excel_reader_module.xlrd, "open_workbook", lambda *_args, **_kwargs: workbook)

    with pytest.raises(ExcelError, match="无法读取\\.xls文件"):
        ExcelReader(header_row=2)._read_xls(str(file_path))


def test_read_xls_open_failure_raises(tmp_path, monkeypatch):
    file_path = tmp_path / "a.xls"
    file_path.write_text("dummy", encoding="utf-8")

    monkeypatch.setattr(
        excel_reader_module.xlrd,
        "open_workbook",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    with pytest.raises(ExcelError, match="无法读取.xls文件"):
        ExcelReader()._read_xls(str(file_path))


def test_read_excel_wraps_unknown_error(tmp_path, monkeypatch):
    file_path = tmp_path / "a.csv"
    file_path.write_text("a,b\n1,2\n", encoding="utf-8")
    reader = ExcelReader()

    monkeypatch.setattr(reader, "_read_csv", lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("oops")))

    with pytest.raises(ExcelError, match="文件格式无效"):
        reader.read_excel(str(file_path))


def test_read_excel_unsupported_extension_raises(tmp_path):
    file_path = tmp_path / "a.txt"
    file_path.write_text("x", encoding="utf-8")
    with pytest.raises(ExcelError, match="不支持的文件格式"):
        ExcelReader().read_excel(str(file_path))


def test_convert_xls_cell_date_fallback_path(monkeypatch):
    reader = ExcelReader()

    date_cell = SimpleNamespace(ctype=getattr(excel_reader_module.xlrd, "XL_CELL_DATE"), value=12)
    monkeypatch.setattr(
        excel_reader_module.xlrd,
        "xldate_as_datetime",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("bad date")),
    )
    assert reader._convert_xls_cell(date_cell, 0) == 12
