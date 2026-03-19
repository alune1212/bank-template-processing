"""测试中复用的表格文件工厂。"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import openpyxl


def write_xlsx_rows(path: Path, rows: Iterable[Iterable[object]]) -> Path:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    assert sheet is not None
    for row in rows:
        sheet.append(list(row))
    workbook.save(path)
    return path


def write_xls_rows(path: Path, rows: Iterable[Iterable[object]]) -> Path:
    import xlwt

    workbook = xlwt.Workbook(encoding="utf-8")
    sheet = workbook.add_sheet("Sheet1")
    for row_idx, row in enumerate(rows):
        for col_idx, value in enumerate(row):
            sheet.write(row_idx, col_idx, value)
    workbook.save(path)
    return path
