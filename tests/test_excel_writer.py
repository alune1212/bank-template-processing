"""测试Excel写入器模块"""

import csv
import os
from pathlib import Path

import openpyxl
import pytest

from excel_writer import ExcelError, ExcelWriter


class TestExcelWriter:
    """ExcelWriter类的测试用例"""

    def test_write_xlsx_file(self, tmp_path):
        """测试写入.xlsx文件"""
        # 创建模板文件
        template_path = tmp_path / "template.xlsx"
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.cell(1, 1, "说明文字")
        ws.cell(2, 1, "姓名")
        ws.cell(2, 2, "年龄")
        ws.cell(2, 3, "金额")
        wb.save(template_path)

        # 准备数据
        data = [
            {"姓名": "张三", "年龄": 25, "金额": 1000.0},
            {"姓名": "李四", "年龄": 30, "金额": 2000.0},
        ]

        # 字段映射
        field_mappings = {"姓名": "姓名", "年龄": "年龄", "金额": "金额"}

        # 输出路径
        output_path = tmp_path / "output.xlsx"

        # 写入文件
        writer = ExcelWriter()
        writer.write_excel(
            template_path=str(template_path),
            data=data,
            field_mappings=field_mappings,
            output_path=str(output_path),
            header_row=2,
            start_row=3,
            mapping_mode="column_name",
        )

        # 验证输出文件存在
        assert output_path.exists()

        # 验证数据
        wb_result = openpyxl.load_workbook(output_path)
        ws_result = wb_result.active
        assert ws_result.cell(1, 1).value == "说明文字"  # 保留说明文字
        assert ws_result.cell(2, 1).value == "姓名"  # 保留表头
        assert ws_result.cell(3, 1).value == "张三"  # 第一行数据
        assert ws_result.cell(3, 2).value == 25
        assert ws_result.cell(4, 1).value == "李四"  # 第二行数据

        wb_result.close()

    def test_amount_written_as_number(self, tmp_path):
        """测试金额字段以数字类型写入，而不是字符串"""
        template_path = tmp_path / "template.xlsx"
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.cell(1, 1, "姓名")
        ws.cell(1, 2, "金额")
        wb.save(template_path)

        data = [
            {"姓名": "张三", "金额": 1000.50},
            {"姓名": "李四", "金额": 2000.75},
        ]

        field_mappings = {
            "姓名": {
                "source_column": "姓名",
                "target_column": "姓名",
                "transform": "none",
            },
            "金额": {
                "source_column": "金额",
                "target_column": "金额",
                "transform": "amount_decimal",
                "required": True,
            },
        }

        output_path = tmp_path / "output.xlsx"
        writer = ExcelWriter()
        writer.write_excel(
            template_path=str(template_path),
            data=data,
            field_mappings=field_mappings,
            output_path=str(output_path),
            header_row=1,
            start_row=2,
            mapping_mode="column_name",
        )

        wb_result = openpyxl.load_workbook(output_path)
        ws_result = wb_result.active

        assert ws_result.cell(2, 1).value == "张三"
        assert isinstance(ws_result.cell(2, 2).value, (int, float)), (
            "金额应该是数字类型"
        )
        assert ws_result.cell(2, 2).value == 1000.50

        assert ws_result.cell(3, 1).value == "李四"
        assert isinstance(ws_result.cell(3, 2).value, (int, float)), (
            "金额应该是数字类型"
        )
        assert ws_result.cell(3, 2).value == 2000.75

        wb_result.close()

    def test_write_csv_file(self, tmp_path):
        """测试写入.csv文件"""
        # 创建模板文件
        template_path = tmp_path / "template.csv"
        with open(template_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["说明文字"])
            writer.writerow(["姓名", "年龄", "金额"])

        # 准备数据
        data = [
            {"姓名": "张三", "年龄": 25, "金额": 1000.0},
            {"姓名": "李四", "年龄": 30, "金额": 2000.0},
        ]

        # 字段映射
        field_mappings = {"姓名": "姓名", "年龄": "年龄", "金额": "金额"}

        # 输出路径
        output_path = tmp_path / "output.csv"

        # 写入文件
        writer = ExcelWriter()
        writer.write_excel(
            template_path=str(template_path),
            data=data,
            field_mappings=field_mappings,
            output_path=str(output_path),
            header_row=2,
            start_row=3,
            mapping_mode="column_name",
        )

        # 验证输出文件存在
        assert output_path.exists()

        # 验证数据（使用utf-8-sig编码以正确处理BOM）
        with open(output_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)
            assert rows[0] == ["说明文字"]
            assert rows[1] == ["姓名", "年龄", "金额"]
            assert rows[2] == ["张三", "25", "1000.0"]
            assert rows[3] == ["李四", "30", "2000.0"]

    def test_write_xls_file(self, tmp_path):
        """测试写入.xls文件"""
        import xlwt

        # 创建模板文件（使用xlwt创建真正的xls格式）
        template_path = tmp_path / "template.xls"
        wb = xlwt.Workbook(encoding="utf-8")
        ws = wb.add_sheet("Sheet1")
        ws.write(0, 0, "说明文字")
        ws.write(1, 0, "姓名")
        ws.write(1, 1, "年龄")
        wb.save(template_path)

        # 准备数据
        data = [{"姓名": "张三", "年龄": 25}, {"姓名": "李四", "年龄": 30}]

        # 字段映射
        field_mappings = {"姓名": "姓名", "年龄": "年龄"}

        # 输出路径
        output_path = tmp_path / "output.xls"

        # 写入文件
        writer = ExcelWriter()
        writer.write_excel(
            template_path=str(template_path),
            data=data,
            field_mappings=field_mappings,
            output_path=str(output_path),
            header_row=2,
            start_row=3,
            mapping_mode="column_name",
        )

        # 验证输出文件存在
        assert output_path.exists()

    def test_fixed_values(self, tmp_path):
        """测试固定值功能"""
        # 创建模板文件
        template_path = tmp_path / "template.xlsx"
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.cell(1, 1, "姓名")
        ws.cell(1, 2, "部门")
        wb.save(template_path)

        # 准备数据
        data = [{"姓名": "张三"}, {"姓名": "李四"}]

        # 字段映射
        field_mappings = {"姓名": "姓名"}

        # 固定值
        fixed_values = {"B": "财务部"}

        # 输出路径
        output_path = tmp_path / "output.xlsx"

        # 写入文件
        writer = ExcelWriter()
        writer.write_excel(
            template_path=str(template_path),
            data=data,
            field_mappings=field_mappings,
            output_path=str(output_path),
            header_row=1,
            start_row=2,
            mapping_mode="column_name",
            fixed_values=fixed_values,
        )

        # 验证固定值
        wb_result = openpyxl.load_workbook(output_path)
        ws_result = wb_result.active
        assert ws_result.cell(2, 1).value == "张三"
        assert ws_result.cell(2, 2).value == "财务部"  # 固定值
        assert ws_result.cell(3, 1).value == "李四"
        assert ws_result.cell(3, 2).value == "财务部"  # 固定值

        wb_result.close()

    def test_auto_number(self, tmp_path):
        """测试自动编号功能"""
        # 创建模板文件
        template_path = tmp_path / "template.xlsx"
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.cell(1, 1, "序号")
        ws.cell(1, 2, "姓名")
        wb.save(template_path)

        # 准备数据
        data = [{"姓名": "张三"}, {"姓名": "李四"}, {"姓名": "王五"}]

        # 字段映射
        field_mappings = {"姓名": "姓名"}

        # 自动编号
        auto_number = {"enabled": True, "column": "A", "start_from": 1}

        # 输出路径
        output_path = tmp_path / "output.xlsx"

        # 写入文件
        writer = ExcelWriter()
        writer.write_excel(
            template_path=str(template_path),
            data=data,
            field_mappings=field_mappings,
            output_path=str(output_path),
            header_row=1,
            start_row=2,
            mapping_mode="column_name",
            auto_number=auto_number,
        )

        # 验证自动编号
        wb_result = openpyxl.load_workbook(output_path)
        ws_result = wb_result.active
        assert ws_result.cell(2, 1).value == 1
        assert ws_result.cell(3, 1).value == 2
        assert ws_result.cell(4, 1).value == 3

        wb_result.close()

    def test_bank_branch_mapping(self, tmp_path):
        """测试银行支行映射功能"""
        # 创建模板文件
        template_path = tmp_path / "template.xlsx"
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.cell(1, 1, "姓名")
        ws.cell(1, 2, "部门")
        wb.save(template_path)

        # 准备数据
        data = [
            {"姓名": "张三", "支行": "北京支行"},
            {"姓名": "李四", "支行": "上海支行"},
        ]

        # 字段映射
        field_mappings = {"姓名": "姓名"}

        # 银行支行映射
        bank_branch_mapping = {
            "enabled": True,
            "source_column": "支行",
            "target_column": "B",
        }

        # 输出路径
        output_path = tmp_path / "output.xlsx"

        # 写入文件
        writer = ExcelWriter()
        writer.write_excel(
            template_path=str(template_path),
            data=data,
            field_mappings=field_mappings,
            output_path=str(output_path),
            header_row=1,
            start_row=2,
            mapping_mode="column_name",
            bank_branch_mapping=bank_branch_mapping,
        )

        # 验证银行支行映射
        wb_result = openpyxl.load_workbook(output_path)
        ws_result = wb_result.active
        assert ws_result.cell(2, 1).value == "张三"
        assert ws_result.cell(2, 2).value == "北京支行"
        assert ws_result.cell(3, 1).value == "李四"
        assert ws_result.cell(3, 2).value == "上海支行"

        wb_result.close()

    def test_month_type_mapping_month_number(self, tmp_path):
        """测试月类型映射功能 - 月份数字"""
        # 创建模板文件
        template_path = tmp_path / "template.xlsx"
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.cell(1, 1, "姓名")
        ws.cell(1, 2, "月份")
        wb.save(template_path)

        # 准备数据
        data = [{"姓名": "张三"}, {"姓名": "李四"}]

        # 字段映射
        field_mappings = {"姓名": "姓名"}

        # 月类型映射
        month_type_mapping = {"enabled": True, "target_column": "B"}

        # 输出路径
        output_path = tmp_path / "output.xlsx"

        # 写入文件（使用月份参数）
        writer = ExcelWriter()
        writer.write_excel(
            template_path=str(template_path),
            data=data,
            field_mappings=field_mappings,
            output_path=str(output_path),
            header_row=1,
            start_row=2,
            mapping_mode="column_name",
            month_type_mapping=month_type_mapping,
            month_param="1",
        )

        # 验证月类型映射
        wb_result = openpyxl.load_workbook(output_path)
        ws_result = wb_result.active
        assert ws_result.cell(2, 1).value == "张三"
        assert ws_result.cell(2, 2).value == "01月收入"
        assert ws_result.cell(3, 1).value == "李四"
        assert ws_result.cell(3, 2).value == "01月收入"

        wb_result.close()

    def test_month_type_mapping_bonus(self, tmp_path):
        """测试月类型映射功能 - 年终奖"""
        # 创建模板文件
        template_path = tmp_path / "template.xlsx"
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.cell(1, 1, "姓名")
        ws.cell(1, 2, "类型")
        wb.save(template_path)

        # 准备数据
        data = [{"姓名": "张三"}]

        # 字段映射
        field_mappings = {"姓名": "姓名"}

        # 月类型映射
        month_type_mapping = {
            "enabled": True,
            "target_column": "B",
            "bonus_value": "年终奖",
        }

        # 输出路径
        output_path = tmp_path / "output.xlsx"

        # 写入文件（使用年终奖参数）
        writer = ExcelWriter()
        writer.write_excel(
            template_path=str(template_path),
            data=data,
            field_mappings=field_mappings,
            output_path=str(output_path),
            header_row=1,
            start_row=2,
            mapping_mode="column_name",
            month_type_mapping=month_type_mapping,
            month_param="年终奖",
        )

        # 验证月类型映射
        wb_result = openpyxl.load_workbook(output_path)
        ws_result = wb_result.active
        assert ws_result.cell(2, 1).value == "张三"
        assert ws_result.cell(2, 2).value == "年终奖"

        wb_result.close()

    def test_column_index_mapping(self, tmp_path):
        """测试使用列索引的映射模式"""
        # 创建模板文件
        template_path = tmp_path / "template.xlsx"
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.cell(1, 1, "姓名")
        ws.cell(1, 2, "年龄")
        wb.save(template_path)

        # 准备数据
        data = [{"name": "张三", "age": 25}, {"name": "李四", "age": 30}]

        # 字段映射（使用列索引）
        field_mappings = {"name": "A", "age": "B"}

        # 输出路径
        output_path = tmp_path / "output.xlsx"

        # 写入文件
        writer = ExcelWriter()
        writer.write_excel(
            template_path=str(template_path),
            data=data,
            field_mappings=field_mappings,
            output_path=str(output_path),
            header_row=1,
            start_row=2,
            mapping_mode="column_index",
        )

        # 验证数据
        wb_result = openpyxl.load_workbook(output_path)
        ws_result = wb_result.active
        assert ws_result.cell(2, 1).value == "张三"
        assert ws_result.cell(2, 2).value == 25
        assert ws_result.cell(3, 1).value == "李四"
        assert ws_result.cell(3, 2).value == 30

        wb_result.close()

    def test_clear_existing_data(self, tmp_path):
        """测试清除现有数据"""
        # 创建包含现有数据的模板文件
        template_path = tmp_path / "template.xlsx"
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.cell(1, 1, "姓名")
        ws.cell(2, 1, "旧数据1")
        ws.cell(3, 1, "旧数据2")
        ws.cell(4, 1, "旧数据3")
        wb.save(template_path)

        # 准备新数据
        data = [{"姓名": "新数据1"}, {"姓名": "新数据2"}]

        # 字段映射
        field_mappings = {"姓名": "姓名"}

        # 输出路径
        output_path = tmp_path / "output.xlsx"

        # 写入文件
        writer = ExcelWriter()
        writer.write_excel(
            template_path=str(template_path),
            data=data,
            field_mappings=field_mappings,
            output_path=str(output_path),
            header_row=1,
            start_row=2,
            mapping_mode="column_name",
        )

        # 验证旧数据被清除
        wb_result = openpyxl.load_workbook(output_path)
        ws_result = wb_result.active
        assert ws_result.cell(1, 1).value == "姓名"
        assert ws_result.cell(2, 1).value == "新数据1"
        assert ws_result.cell(3, 1).value == "新数据2"
        assert ws_result.cell(4, 1).value is None  # 旧数据被清除

        wb_result.close()

    def test_config_validation_invalid_start_row(self, tmp_path):
        """测试配置验证 - 无效的start_row"""
        # 创建模板文件
        template_path = tmp_path / "template.xlsx"
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.cell(1, 1, "姓名")
        wb.save(template_path)

        # 准备数据
        data = [{"姓名": "张三"}]

        # 字段映射
        field_mappings = {"姓名": "姓名"}

        # 输出路径
        output_path = tmp_path / "output.xlsx"

        # 写入文件（start_row <= header_row，应该抛出异常）
        writer = ExcelWriter()
        with pytest.raises(Exception):  # ConfigError
            writer.write_excel(
                template_path=str(template_path),
                data=data,
                field_mappings=field_mappings,
                output_path=str(output_path),
                header_row=2,
                start_row=2,  # 无效：start_row 必须大于 header_row
                mapping_mode="column_name",
            )

    def test_unsupported_format(self, tmp_path):
        """测试不支持的文件格式"""
        # 创建不支持的格式文件
        template_path = tmp_path / "template.txt"
        template_path.write_text("test data", encoding="utf-8")

        # 准备数据
        data = [{"姓名": "张三"}]

        # 字段映射
        field_mappings = {"姓名": "姓名"}

        # 输出路径
        output_path = tmp_path / "output.txt"

        # 写入文件（应该抛出异常）
        writer = ExcelWriter()
        with pytest.raises(ExcelError):
            writer.write_excel(
                template_path=str(template_path),
                data=data,
                field_mappings=field_mappings,
                output_path=str(output_path),
                header_row=1,
                start_row=2,
                mapping_mode="column_name",
            )

    def test_template_not_found(self, tmp_path):
        """测试模板文件未找到"""
        # 准备数据
        data = [{"姓名": "张三"}]

        # 字段映射
        field_mappings = {"姓名": "姓名"}

        # 输出路径
        output_path = tmp_path / "output.xlsx"

        # 写入文件（模板文件不存在）
        writer = ExcelWriter()
        with pytest.raises(FileNotFoundError):
            writer.write_excel(
                template_path="nonexistent.xlsx",
                data=data,
                field_mappings=field_mappings,
                output_path=str(output_path),
                header_row=1,
                start_row=2,
                mapping_mode="column_name",
            )

    def test_preserve_header_format_xlsx(self, tmp_path):
        """测试保留.xlsx文件的表头格式"""
        # 创建模板文件并设置格式
        template_path = tmp_path / "template.xlsx"
        wb = openpyxl.Workbook()
        ws = wb.active

        # 设置表头样式（加粗）
        from openpyxl.styles import Font

        header_font = Font(bold=True)

        ws.cell(1, 1, "姓名").font = header_font
        ws.cell(1, 2, "年龄").font = header_font
        ws.cell(2, 1, "旧数据")
        wb.save(template_path)

        # 准备数据
        data = [{"姓名": "张三", "年龄": 25}]

        # 字段映射
        field_mappings = {"姓名": "姓名", "年龄": "年龄"}

        # 输出路径
        output_path = tmp_path / "output.xlsx"

        # 写入文件
        writer = ExcelWriter()
        writer.write_excel(
            template_path=str(template_path),
            data=data,
            field_mappings=field_mappings,
            output_path=str(output_path),
            header_row=1,
            start_row=2,
            mapping_mode="column_name",
        )

        # 验证表头格式被保留
        wb_result = openpyxl.load_workbook(output_path)
        ws_result = wb_result.active
        assert ws_result.cell(1, 1).font.bold  # 表头格式被保留
        assert ws_result.cell(1, 2).font.bold  # 表头格式被保留

        wb_result.close()
