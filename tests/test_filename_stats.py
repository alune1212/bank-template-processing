import pytest
from bank_template_processing.main import generate_output_filename, _calculate_stats


def test_calculate_stats():
    data = [
        {"金额": 100.50, "姓名": "张三"},
        {"金额": 200.00, "姓名": "李四"},
        {"金额": "invalid", "姓名": "王五"},
        {"金额": None, "姓名": "赵六"},
    ]

    field_mappings = {"模板金额列": {"source_column": "金额", "transform": "amount_decimal"}}
    transformations = {}

    count, total_amount = _calculate_stats(data, field_mappings, transformations)

    assert count == 4
    assert total_amount == 300.50


def test_generate_output_filename_format():
    filename = generate_output_filename(
        unit_name="TestUnit",
        month="01",
        template_name="TestTemplate",
        template_path="templates/template.xlsx",
        count=10,
        amount=1234.56,
    )

    expected = "TestUnit_TestTemplate_10人_金额1234.56元.xlsx"
    assert filename == expected


def test_generate_output_filename_fallback_template_name():
    filename = generate_output_filename(
        unit_name="TestUnit",
        month="01",
        template_name=None,
        template_path="templates/fallback.xlsx",
        count=5,
        amount=500.00,
    )

    expected = "TestUnit_fallback_5人_金额500.00元.xlsx"
    assert filename == expected
