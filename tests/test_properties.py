"""Hypothesis 性质测试。"""

from __future__ import annotations

from datetime import date

from hypothesis import given, strategies as st

from bank_template_processing.main import _is_zero_salary_value, generate_output_filename
from bank_template_processing.validator import Validator


@given(st.integers(min_value=-10_000_000, max_value=10_000_000))
def test_is_zero_salary_value_integer_equivalence(value: int):
    assert _is_zero_salary_value(value) is (value == 0)


@given(st.integers(min_value=-10_000_000, max_value=10_000_000))
def test_is_zero_salary_value_string_separator_normalization(value: int):
    text = f" {value:,} ".replace(",", "，")
    assert _is_zero_salary_value(text) is (value == 0)


@given(
    unit_name=st.text(alphabet=st.characters(min_codepoint=0x4E00, max_codepoint=0x9FFF), min_size=1, max_size=4),
    month=st.sampled_from(["01", "02", "12", "年终奖", "补偿金"]),
    template_name=st.text(alphabet="ABCxyz", min_size=1, max_size=8),
    count=st.integers(min_value=0, max_value=9999),
    amount=st.decimals(min_value=-100000, max_value=100000, places=2, allow_nan=False, allow_infinity=False),
    ext=st.sampled_from([".xlsx", ".xls"]),
)
def test_generate_output_filename_extension_property(
    unit_name: str,
    month: str,
    template_name: str,
    count: int,
    amount,
    ext: str,
):
    filename = generate_output_filename(
        unit_name=unit_name,
        month=month,
        template_name=template_name,
        template_path=f"template{ext}",
        count=count,
        amount=float(amount),
        output_template="{unit_name}_{template_name}_{count}",
    )
    assert filename.endswith(ext)


@given(st.integers(min_value=-1_000_000, max_value=1_000_000))
def test_validator_numeric_allowed_values_normalization_property(value: int):
    Validator.validate_value_ranges(
        {"金额": str(value)},
        {"金额": {"allowed_values": [value]}},
    )


@given(st.dates(min_value=date(2000, 1, 1), max_value=date(2100, 12, 31)))
def test_validator_date_allowed_values_normalization_property(value: date):
    Validator.validate_value_ranges(
        {"日期": value.strftime("%Y-%m-%d")},
        {"日期": {"allowed_values": [value]}},
    )
