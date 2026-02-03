"""测试Excel读取器公式读取策略"""

from bank_template_processing.excel_reader import ExcelReader


def test_read_xlsx_formula_data_only_false():
    """公式单元格在 data_only=False 时应返回公式字符串"""
    file_path = "tests/fixtures/test_formula.xlsx"
    reader = ExcelReader(data_only=False)
    result = reader.read_excel(file_path)

    assert result[0]["结果"] == "=A2*2"
    assert result[1]["结果"] == "=A3*2"


def test_read_xlsx_formula_data_only_true():
    """公式单元格在 data_only=True 时应返回缓存值（未计算则为空）"""
    file_path = "tests/fixtures/test_formula.xlsx"
    reader = ExcelReader(data_only=True)
    result = reader.read_excel(file_path)

    # openpyxl 不计算公式，未保存缓存值时为 None
    assert result[0]["结果"] is None
    assert result[1]["结果"] is None
