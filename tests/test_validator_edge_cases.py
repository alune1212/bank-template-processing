"""Validator 边界与失败路径补充测试。"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import pytest

from bank_template_processing.validator import ValidationError, Validator


def test_parse_date_string_invalid_raises():
    with pytest.raises(ValidationError, match="不是有效日期"):
        Validator._parse_date_string("入职日期", "2026/13/40")


def test_coerce_numeric_value_and_bound_error_branches():
    assert Validator._coerce_numeric_value("金额", Decimal("1.23")) == Decimal("1.23")
    with pytest.raises(TypeError, match="bool 不作为数值处理"):
        Validator._coerce_numeric_value("金额", True)
    with pytest.raises(TypeError, match="无法转换为数值"):
        Validator._coerce_numeric_value("金额", object())

    assert Validator._coerce_numeric_bound(Decimal("2.34")) == Decimal("2.34")
    with pytest.raises(TypeError, match="bool 不作为数值处理"):
        Validator._coerce_numeric_bound(False)
    with pytest.raises(TypeError, match="无法转换为数值: abc"):
        Validator._coerce_numeric_bound("abc")
    with pytest.raises(TypeError, match="无法转换为数值"):
        Validator._coerce_numeric_bound(object())


def test_coerce_date_value_and_bound_error_branches():
    now = datetime(2026, 1, 2, 3, 4, 5)
    today = date(2026, 1, 2)

    assert Validator._coerce_date_value("日期", now, "datetime") == now
    assert Validator._coerce_date_value("日期", now, "date") == today
    assert Validator._coerce_date_value("日期", today, "date") == today
    assert Validator._coerce_date_value("日期", today, "datetime") == datetime(2026, 1, 2, 0, 0, 0)
    with pytest.raises(TypeError, match="无法转换为日期"):
        Validator._coerce_date_value("日期", 123, "date")

    assert Validator._coerce_date_bound(today, "datetime") == datetime(2026, 1, 2, 0, 0, 0)
    with pytest.raises(TypeError, match="不是有效日期"):
        Validator._coerce_date_bound("bad-date", "date")
    with pytest.raises(TypeError, match="无法转换为日期"):
        Validator._coerce_date_bound(object(), "date")


def test_coerce_for_comparison_uses_date_branch():
    value_cmp, min_cmp, max_cmp = Validator._coerce_for_comparison(
        "日期",
        "2026-01-10",
        date(2026, 1, 1),
        date(2026, 1, 31),
    )
    assert value_cmp == date(2026, 1, 10)
    assert min_cmp == date(2026, 1, 1)
    assert max_cmp == date(2026, 1, 31)


def test_normalize_allowed_values_non_list_returns_raw():
    value, allowed, use_normalized = Validator._normalize_allowed_values("状态", "A", {"A": 1})
    assert value == "A"
    assert allowed == {"A": 1}
    assert use_normalized is False


def test_normalize_allowed_values_date_item_parse_fallback():
    normalized_value, normalized_allowed, use_normalized = Validator._normalize_allowed_values(
        "日期",
        "2026-01-10",
        ["2026-01-10", "not-a-date"],
    )
    assert use_normalized is True
    assert normalized_value == date(2026, 1, 10)
    assert normalized_allowed[0] == date(2026, 1, 10)
    assert normalized_allowed[1] == "not-a-date"


def test_normalize_allowed_values_numeric_fallbacks():
    # value 可归一化，但 allowed_values 中无任何可转数值项 -> 回退原值比较
    value, allowed, use_normalized = Validator._normalize_allowed_values("金额", "100", ["A", "B"])
    assert value == "100"
    assert allowed == ["A", "B"]
    assert use_normalized is False

    # value 不可归一化 -> 直接回退原值比较
    value, allowed, use_normalized = Validator._normalize_allowed_values("金额", "ABC", [100, 200])
    assert value == "ABC"
    assert allowed == [100, 200]
    assert use_normalized is False


def test_validate_data_types_extra_error_paths():
    with pytest.raises(ValidationError, match="类型配置必须为字符串"):
        Validator.validate_data_types({"字段": 1}, {"字段": 123})

    with pytest.raises(ValidationError, match="类型应为 numeric"):
        Validator.validate_data_types({"字段": []}, {"字段": "numeric"})

    with pytest.raises(ValidationError, match="类型应为 integer，实际为 bool"):
        Validator.validate_data_types({"字段": True}, {"字段": "integer"})

    # float 且为整数值、Decimal 整数值都应通过 integer 校验
    Validator.validate_data_types({"字段": 1.0}, {"字段": "integer"})
    Validator.validate_data_types({"字段": Decimal("2")}, {"字段": "integer"})

    with pytest.raises(ValidationError, match="类型应为 integer"):
        Validator.validate_data_types({"字段": "1.2"}, {"字段": "integer"})

    with pytest.raises(ValidationError, match="类型不支持"):
        Validator.validate_data_types({"字段": "x"}, {"字段": "unsupported"})


def test_validate_value_ranges_value_type_error_skip_and_max_only_paths():
    # 值本身无法比较（TypeError）应跳过，不抛异常
    Validator.validate_value_ranges({"字段": []}, {"字段": {"min": 1, "max": 10}})

    with pytest.raises(ValidationError, match="大于最大值"):
        Validator.validate_value_ranges({"字段": 11}, {"字段": {"max": 10}})

    # max-only 值无法比较（TypeError）应跳过
    Validator.validate_value_ranges({"字段": []}, {"字段": {"max": 10}})


def test_validate_value_ranges_invalid_rule_raises():
    with pytest.raises(ValidationError, match="范围规则无效"):
        Validator.validate_value_ranges({"字段": "50"}, {"字段": {"min": "abc", "max": 100}})

    with pytest.raises(ValidationError, match="min/max 必须同为数值或同为日期"):
        Validator.validate_value_ranges({"字段": "50"}, {"字段": {"min": 1, "max": "2024-01-01"}})


def test_validate_value_ranges_length_type_error_and_allowed_normalized_error():
    # len() 不支持时，min_length/max_length 分支应跳过
    Validator.validate_value_ranges({"字段": 123}, {"字段": {"min_length": 1, "max_length": 2}})

    with pytest.raises(ValidationError, match="不在允许的值列表"):
        Validator.validate_value_ranges({"字段": "101"}, {"字段": {"allowed_values": [100, 200]}})
