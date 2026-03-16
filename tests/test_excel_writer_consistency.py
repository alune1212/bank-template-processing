"""ExcelWriter 跨格式一致性测试。"""

from __future__ import annotations

import csv

import openpyxl
import pytest

from bank_template_processing.excel_writer import ExcelWriter


@pytest.mark.parametrize("ext", [".xlsx", ".csv", ".xls"])
def test_writer_consistent_mapping_features(tmp_path, ext):
    template_path = tmp_path / f"template{ext}"
    output_path = tmp_path / f"output{ext}"

    if ext == ".xlsx":
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        assert sheet is not None
        sheet.append(["序号", "姓名", "金额", "用途", "备注"])
        workbook.save(template_path)
    elif ext == ".csv":
        with open(template_path, "w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["序号", "姓名", "金额", "用途", "备注"])
    else:
        import xlwt

        workbook = xlwt.Workbook(encoding="utf-8")
        sheet = workbook.add_sheet("Sheet1")
        for col_idx, value in enumerate(["序号", "姓名", "金额", "用途", "备注"]):
            sheet.write(0, col_idx, value)
        workbook.save(template_path)

    ExcelWriter().write_excel(
        template_path=str(template_path),
        data=[{"姓名": "张三", "金额": "12.5"}],
        field_mappings={
            "姓名": {"source_column": "姓名", "target_column": "姓名"},
            "金额": {"source_column": "金额", "target_column": "金额", "transform": "amount_decimal"},
        },
        output_path=str(output_path),
        header_row=1,
        start_row=2,
        mapping_mode="column_name",
        fixed_values={"备注": "固定"},
        auto_number={"enabled": True, "column_name": "序号", "start_from": 1},
        month_type_mapping={"enabled": True, "target_column": "用途", "month_format": "{month}月收入"},
        month_param="01",
        clear_rows={"start_row": 2, "end_row": 3},
    )

    if ext == ".xlsx":
        result = openpyxl.load_workbook(output_path)
        sheet = result.active
        assert sheet is not None
        assert sheet.cell(2, 1).value == 1
        assert sheet.cell(2, 2).value == "张三"
        assert sheet.cell(2, 3).value == 12.5
        assert sheet.cell(2, 4).value == "01月收入"
        assert sheet.cell(2, 5).value == "固定"
        result.close()
    elif ext == ".csv":
        with open(output_path, "r", encoding="utf-8-sig", newline="") as file:
            rows = list(csv.reader(file))
        assert rows[1] == ['="1"', '="张三"', '="12.5"', '="01月收入"', '="固定"']
    else:
        import xlrd

        result = xlrd.open_workbook(str(output_path))
        sheet = result.sheet_by_index(0)
        assert sheet.cell_value(1, 0) == 1
        assert sheet.cell_value(1, 1) == "张三"
        assert sheet.cell_value(1, 2) == "12.5"
        assert sheet.cell_value(1, 3) == "01月收入"
        assert sheet.cell_value(1, 4) == "固定"
