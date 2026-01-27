"""测试Excel读取器模块"""

import pytest
from pathlib import Path

from excel_reader import ExcelReader, ExcelError


class TestExcelReader:
    """ExcelReader类的测试用例"""

    def test_read_xlsx_file(self):
        """测试读取.xlsx文件"""
        file_path = "tests/fixtures/test_input.xlsx"
        reader = ExcelReader()
        result = reader.read_excel(file_path)

        assert len(result) == 3  # 跳过空行后应该有3行数据
        assert result[0]["姓名"] == "张三"
        assert result[0]["年龄"] == "25"
        assert result[1]["姓名"] == "李四"
        assert result[2]["姓名"] == "王五"

    def test_read_csv_file(self):
        """测试读取.csv文件"""
        file_path = "tests/fixtures/test_input.csv"
        reader = ExcelReader()
        result = reader.read_excel(file_path)

        assert len(result) == 3  # 跳过空行后应该有3行数据
        assert result[0]["姓名"] == "张三"
        assert result[0]["邮箱"] == "zhangsan@example.com"
        assert result[1]["姓名"] == "李四"
        assert result[2]["姓名"] == "王五"

    def test_read_xls_file(self):
        """测试读取.xls文件"""
        file_path = "tests/fixtures/test_input.xls"
        reader = ExcelReader()
        result = reader.read_excel(file_path)

        assert len(result) == 3  # 跳过空行后应该有3行数据
        assert result[0]["姓名"] == "张三"
        assert result[0]["电话"] == "13800138001"
        assert result[1]["姓名"] == "李四"
        assert result[2]["姓名"] == "王五"

    def test_extract_headers(self):
        """测试表头提取"""
        file_path = "tests/fixtures/test_input.xlsx"
        reader = ExcelReader()
        result = reader.read_excel(file_path)

        # 检查结果包含正确的表头字段
        assert "姓名" in result[0]
        assert "年龄" in result[0]
        assert "邮箱" in result[0]
        assert "电话" in result[0]

    def test_convert_rows_to_dicts(self):
        """测试数据行转换为字典"""
        file_path = "tests/fixtures/test_input.csv"
        reader = ExcelReader()
        result = reader.read_excel(file_path)

        # 检查每行都是字典类型
        for row in result:
            assert isinstance(row, dict)

        # 检查第一行的具体值
        assert result[0] == {
            "姓名": "张三",
            "年龄": "25",
            "邮箱": "zhangsan@example.com",
            "电话": "13800138001",
        }

    def test_skip_empty_rows(self):
        """测试跳过空行"""
        file_path = "tests/fixtures/test_input.xlsx"
        reader = ExcelReader()
        result = reader.read_excel(file_path)

        # 测试数据包含一个中间的空行，应该被跳过
        assert len(result) == 3
        # 检查没有空字典
        for row in result:
            assert len(row) > 0

    def test_file_not_found(self):
        """测试文件未找到异常"""
        file_path = "tests/fixtures/nonexistent.xlsx"
        reader = ExcelReader()

        with pytest.raises(FileNotFoundError):
            reader.read_excel(file_path)

    def test_invalid_file_format(self):
        """测试无效文件格式"""
        file_path = "tests/fixtures/test_input.xlsx"
        reader = ExcelReader()

        # 创建一个无效的xlsx文件（只是文本文件）
        invalid_path = "tests/fixtures/invalid.xlsx"
        Path(invalid_path).write_text(
            "This is not a valid Excel file", encoding="utf-8"
        )

        try:
            with pytest.raises(ExcelError):
                reader.read_excel(invalid_path)
        finally:
            # 清理测试文件
            Path(invalid_path).unlink()

    def test_unsupported_format(self):
        """测试不支持的文件格式"""
        file_path = "tests/fixtures/test_input.txt"
        reader = ExcelReader()

        # 创建一个不支持的格式文件
        Path(file_path).write_text("test data", encoding="utf-8")

        try:
            with pytest.raises(ExcelError):
                reader.read_excel(file_path)
        finally:
            # 清理测试文件
            Path(file_path).unlink()
