"""main.py 模块的测试"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import argparse
import io
import sys


class TestMonthValidation:
    """测试月份参数校验"""

    def test_validate_month_numeric_1_to_12(self):
        """测试数字格式月份：1-12"""
        from main import validate_month

        for month in range(1, 13):
            assert validate_month(str(month)) == str(month)

    def test_validate_month_numeric_with_leading(self):
        """测试数字格式月份：01-09"""
        from main import validate_month

        for month in range(1, 10):
            month_str = f"0{month}"
            assert validate_month(month_str) == month_str

    def test_validate_month_keyword_bonus(self):
        """测试关键字格式：年终奖"""
        from main import validate_month

        assert validate_month("年终奖") == "年终奖"

    def test_validate_month_keyword_compensation(self):
        """测试关键字格式：补偿金"""
        from main import validate_month

        assert validate_month("补偿金") == "补偿金"

    def test_validate_month_invalid_numeric(self):
        """测试无效的数字月份"""
        from main import validate_month

        with pytest.raises(
            ValueError, match="月份参数必须是1-12的数字、01-09格式、'年终奖'或'补偿金'"
        ):
            validate_month("0")

        with pytest.raises(
            ValueError, match="月份参数必须是1-12的数字、01-09格式、'年终奖'或'补偿金'"
        ):
            validate_month("13")

        with pytest.raises(
            ValueError, match="月份参数必须是1-12的数字、01-09格式、'年终奖'或'补偿金'"
        ):
            validate_month("00")

    def test_validate_month_invalid_string(self):
        """测试无效的字符串月份"""
        from main import validate_month

        with pytest.raises(
            ValueError, match="月份参数必须是1-12的数字、01-09格式、'年终奖'或'补偿金'"
        ):
            validate_month("1月")

        with pytest.raises(
            ValueError, match="月份参数必须是1-12的数字、01-09格式、'年终奖'或'补偿金'"
        ):
            validate_month("January")


class TestArgumentParser:
    """测试命令行参数解析"""

    def test_parse_args_with_defaults(self):
        """测试使用默认值的参数解析"""
        from main import parse_args

        args = parse_args(["input.xlsx", "unit1", "01"])

        assert args.excel_path == "input.xlsx"
        assert args.unit_name == "unit1"
        assert args.month == "01"
        assert args.output_dir == "output/"
        assert args.config == "config.json"
        assert args.output_filename_template == "{unit_name}_{month}"

    def test_parse_args_with_custom_values(self):
        """测试使用自定义值的参数解析"""
        from main import parse_args

        args = parse_args(
            [
                "input.xlsx",
                "unit1",
                "年终奖",
                "--output-dir",
                "custom_output/",
                "--config",
                "custom_config.json",
                "--output-filename-template",
                "{unit_name}_{month}_{timestamp}",
            ]
        )

        assert args.excel_path == "input.xlsx"
        assert args.unit_name == "unit1"
        assert args.month == "年终奖"
        assert args.output_dir == "custom_output/"
        assert args.config == "custom_config.json"
        assert args.output_filename_template == "{unit_name}_{month}_{timestamp}"


class TestGenerateTimestamp:
    """测试时间戳生成"""

    def test_generate_timestamp_format(self):
        """测试时间戳格式"""
        from main import generate_timestamp
        import re

        timestamp = generate_timestamp()
        pattern = r"^\d{8}_\d{6}$"
        assert re.match(pattern, timestamp)


class TestGenerateOutputFilename:
    """测试输出文件名生成"""

    def test_generate_output_filename_without_template_name(self):
        """测试生成输出文件名（不含模板名）"""
        from main import generate_output_filename

        filename = generate_output_filename(
            "unit1", "01", None, "20250127_120000", "template.xlsx"
        )

        assert filename == "unit1_01_20250127_120000.xlsx"

    def test_generate_output_filename_with_template_name(self):
        """测试生成输出文件名（含模板名）"""
        from main import generate_output_filename

        filename = generate_output_filename(
            "unit1", "年终奖", "工商银行", "20250127_120000", "template.xlsx"
        )

        assert filename == "unit1_工商银行_年终奖_20250127_120000.xlsx"

    def test_generate_output_filename_csv_extension(self):
        """测试CSV模板生成CSV扩展名"""
        from main import generate_output_filename

        filename = generate_output_filename(
            "unit1", "01", None, "20250127_120000", "template.csv"
        )

        assert filename == "unit1_01_20250127_120000.csv"

    def test_generate_output_filename_xls_extension(self):
        """测试XLS模板生成XLS扩展名"""
        from main import generate_output_filename

        filename = generate_output_filename(
            "unit1", "01", None, "20250127_120000", "template.xls"
        )

        assert filename == "unit1_01_20250127_120000.xls"


class TestMainWorkflow:
    """测试主工作流程"""

    def create_test_config(self, tmp_path, template_path=None):
        """创建测试配置文件"""
        config = {
            "version": "1.0",
            "organization_units": {
                "unit1": {
                    "template_path": template_path or str(tmp_path / "template.xlsx"),
                    "header_row": 1,
                    "start_row": 2,
                    "field_mappings": {},
                    "transformations": {},
                    "validation_rules": {},
                    "fixed_values": {},
                    "auto_number": {"enabled": False},
                    "bank_branch_mapping": {"enabled": False},
                    "month_type_mapping": {"enabled": False},
                }
            },
        }

        config_path = tmp_path / "config.json"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        return config_path

    def create_test_excel(self, tmp_path, filename="input.xlsx"):
        """创建测试Excel文件"""
        import openpyxl

        excel_path = tmp_path / filename
        wb = openpyxl.Workbook()
        ws = wb.active

        ws.append(["姓名", "卡号", "金额"])
        ws.append(["张三", "6222021234567890128", "1000.00"])

        wb.save(excel_path)
        return excel_path

    def create_template_excel(self, tmp_path, filename="template.xlsx"):
        """创建模板Excel文件"""
        import openpyxl

        template_path = tmp_path / filename
        wb = openpyxl.Workbook()
        ws = wb.active

        ws.append(["姓名", "卡号", "金额"])
        ws.append(["示例姓名", "示例卡号", "100.00"])

        wb.save(template_path)
        return template_path

    @patch("main.ExcelReader")
    @patch("main.ExcelWriter")
    def test_main_without_template_selection(
        self, mock_writer_class, mock_reader_class, tmp_path, caplog
    ):
        """测试主流程：不启用模板选择"""
        from main import main

        input_excel = self.create_test_excel(tmp_path, "input.xlsx")
        template_excel = self.create_template_excel(tmp_path, "template.xlsx")
        config_path = self.create_test_config(tmp_path, str(template_excel))

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        mock_reader_instance = MagicMock()
        mock_reader_instance.read_excel.return_value = [
            {"姓名": "张三", "卡号": "6222021234567890128", "金额": "1000.00"}
        ]
        mock_reader_class.return_value = mock_reader_instance

        mock_writer_instance = MagicMock()
        mock_writer_class.return_value = mock_writer_instance

        with patch.object(
            sys,
            "argv",
            [
                "main.py",
                str(input_excel),
                "unit1",
                "01",
                "--output-dir",
                str(output_dir),
                "--config",
                str(config_path),
            ],
        ):
            main()

        mock_reader_class.assert_called_once()
        mock_reader_instance.read_excel.assert_called_once()
        mock_writer_class.assert_called_once()

    @patch("main.ExcelReader")
    @patch("main.TemplateSelector")
    @patch("main.ExcelWriter")
    def test_main_with_template_selection(
        self,
        mock_writer_class,
        mock_selector_class,
        mock_reader_class,
        tmp_path,
        caplog,
    ):
        """测试主流程：启用模板选择"""
        from main import main

        input_excel = self.create_test_excel(tmp_path, "input.xlsx")
        template_excel = self.create_template_excel(tmp_path, "template.xlsx")
        special_template = self.create_template_excel(tmp_path, "special_template.xlsx")

        config = {
            "version": "1.0",
            "organization_units": {
                "unit1": {
                    "template_path": str(template_excel),
                    "header_row": 1,
                    "start_row": 2,
                    "field_mappings": {},
                    "transformations": {},
                    "validation_rules": {},
                    "fixed_values": {},
                    "auto_number": {"enabled": False},
                    "bank_branch_mapping": {"enabled": False},
                    "month_type_mapping": {"enabled": False},
                }
            },
            "template_selection_rules": {
                "enabled": True,
                "bank_column": "开户银行",
                "default_bank": "工商银行",
                "default_template": str(template_excel),
                "special_template": str(special_template),
            },
        }

        config_path = tmp_path / "config.json"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        mock_reader_instance = MagicMock()
        mock_reader_instance.read_excel.return_value = [
            {
                "姓名": "张三",
                "卡号": "6222021234567890128",
                "金额": "1000.00",
                "开户银行": "工商银行",
            }
        ]
        mock_reader_class.return_value = mock_reader_instance

        mock_selector_instance = MagicMock()
        mock_selector_instance.group_data.return_value = {
            "default": {
                "data": [
                    {
                        "姓名": "张三",
                        "卡号": "6222021234567890128",
                        "金额": "1000.00",
                        "开户银行": "工商银行",
                    }
                ],
                "template": str(template_excel),
                "group_name": "template",
            },
            "special": {
                "data": [],
                "template": str(special_template),
                "group_name": "special_template",
            },
        }
        mock_selector_class.return_value = mock_selector_instance

        mock_writer_instance = MagicMock()
        mock_writer_class.return_value = mock_writer_instance

        with patch.object(
            sys,
            "argv",
            [
                "main.py",
                str(input_excel),
                "unit1",
                "01",
                "--output-dir",
                str(output_dir),
                "--config",
                str(config_path),
            ],
        ):
            main()

        mock_reader_class.assert_called_once()
        mock_selector_class.assert_called_once()
        mock_selector_instance.group_data.assert_called_once()
        mock_writer_class.assert_called_once()

    def test_main_file_not_found(self, tmp_path, caplog):
        """测试主流程：输入文件不存在"""
        from main import main

        config = {
            "version": "1.0",
            "organization_units": {
                "unit1": {
                    "template_path": "template.xlsx",
                    "header_row": 1,
                    "start_row": 2,
                    "field_mappings": {},
                    "transformations": {},
                    "validation_rules": {},
                    "fixed_values": {},
                    "auto_number": {"enabled": False},
                    "bank_branch_mapping": {"enabled": False},
                    "month_type_mapping": {"enabled": False},
                }
            },
        }

        config_path = tmp_path / "config.json"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        with (
            patch("sys.exit") as mock_exit,
            patch.object(
                sys,
                "argv",
                [
                    "main.py",
                    "nonexistent.xlsx",
                    "unit1",
                    "01",
                    "--config",
                    str(config_path),
                ],
            ),
        ):
            main()

        mock_exit.assert_called_once_with(1)
        assert any("错误" in record.message for record in caplog.records)


class TestApplyTransformations:
    """测试数据转换"""

    def test_apply_transformations_empty(self):
        """测试空转换配置"""
        from main import apply_transformations

        data = [{"姓名": "张三"}]
        result = apply_transformations(data, {}, {})

        assert result == data

    def test_apply_transformations_date(self):
        """测试日期转换"""
        from main import apply_transformations

        data = [{"日期": "15/01/2024"}]
        transformations = {"date_format": {"output_format": "YYYY-MM-DD"}}
        field_mappings = {"日期": {"source_column": "日期", "transform": "date_format"}}
        result = apply_transformations(data, transformations, field_mappings)

        assert result[0]["日期"] == "2024-01-15"

    def test_apply_transformations_amount(self):
        """测试金额转换"""
        from main import apply_transformations

        data = [{"金额": "1000.456"}]
        transformations = {"amount_decimal": {"decimal_places": 2}}
        field_mappings = {
            "金额": {"source_column": "金额", "transform": "amount_decimal"}
        }
        result = apply_transformations(data, transformations, field_mappings)

        assert result[0]["金额"] == 1000.46

    def test_apply_transformations_card_number(self):
        """测试卡号转换"""
        from main import apply_transformations

        data = [{"卡号": "6222-0212-3456-7890-128"}]
        transformations = {
            "card_number": {"remove_formatting": True, "luhn_validation": True}
        }
        field_mappings = {"卡号": {"source_column": "卡号", "transform": "card_number"}}
        result = apply_transformations(data, transformations, field_mappings)

        assert result[0]["日期"] == "2024-01-15"

    def test_apply_transformations_amount(self):
        """测试金额转换"""
        from main import apply_transformations

        data = [{"金额": "1000.456"}]
        transformations = {"amount_decimal": {"decimal_places": 2}}
        field_mappings = {
            "金额": {"source_column": "金额", "transform": "amount_decimal"}
        }
        result = apply_transformations(data, transformations, field_mappings)

        assert result[0]["金额"] == 1000.46

    def test_apply_transformations_card_number(self):
        """测试卡号转换"""
        from main import apply_transformations

        data = [{"卡号": "6222-0212-3456-7890-128"}]
        transformations = {
            "card_number": {"remove_formatting": True, "luhn_validation": True}
        }
        field_mappings = {"卡号": {"source_column": "卡号", "transform": "card_number"}}
        result = apply_transformations(data, transformations, field_mappings)

        assert result[0]["卡号"] == "6222021234567890128"

    def test_apply_transformations_mixed(self):
        """测试混合转换"""
        from main import apply_transformations

        data = [{"日期": "15/01/2024", "金额": "1000.456"}]
        transformations = {
            "date_format": {"output_format": "YYYY-MM-DD"},
            "amount_decimal": {"decimal_places": 2},
        }
        field_mappings = {
            "日期": {"source_column": "日期", "transform": "date_format"},
            "金额": {"source_column": "金额", "transform": "amount_decimal"},
        }
        result = apply_transformations(data, transformations, field_mappings)

        assert result[0]["日期"] == "2024-01-15"
        assert result[0]["金额"] == 1000.46
