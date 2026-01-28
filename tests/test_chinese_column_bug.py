"""Test for Chinese column name bug fix"""

import pytest
from excel_writer import ExcelWriter


def test_chinese_column_name_not_treated_as_excel_letter():
    """Chinese column names should not be treated as Excel letters (A-Z)"""
    writer = ExcelWriter()

    # Test case 1: Valid Excel column letters should work
    for col_letter, expected_idx in [
        ("A", 1),
        ("B", 2),
        ("Z", 26),
        ("AA", 27),
        ("AB", 28),
    ]:
        result = writer._resolve_column_index(col_letter)
        assert result == expected_idx, (
            f"{col_letter} should be {expected_idx}, got {result}"
        )

    # Test case 2: Chinese column names should NOT be treated as Excel letters
    # They should raise ValueError if not in headers
    chinese_columns = ["收款方账号", "收款方户名", "开户行支行名称", "金额"]
    for chinese_col in chinese_columns:
        with pytest.raises(ValueError, match="无法解析列标识"):
            writer._resolve_column_index(chinese_col)

    # Test case 3: Mixed Chinese + letters should fail
    with pytest.raises(ValueError, match="无法解析列标识"):
        writer._resolve_column_index("A张B")

    # Test case 4: Chinese column names WITH headers should work
    headers = {
        "收款方账号": 1,
        "收款方户名": 2,
        "开户行支行名称": 3,
        "金额": 4,
        "姓名": 5,
    }
    for chinese_col, expected_idx in headers.items():
        result = writer._resolve_column_index(chinese_col, headers=headers)
        assert result == expected_idx, (
            f"{chinese_col} should be {expected_idx}, got {result}"
        )

    # Test case 5: Numeric strings should still work
    for num_str, expected_idx in [("1", 1), ("10", 10), ("100", 100)]:
        result = writer._resolve_column_index(num_str)
        assert result == expected_idx

    # Test case 6: Integers should still work
    for num_int, expected_idx in [(1, 1), (10, 10), (100, 100)]:
        result = writer._resolve_column_index(num_int)
        assert result == expected_idx


def test_column_letter_to_index_bounds():
    """Test that only A-Z are valid Excel column letters"""
    writer = ExcelWriter()

    # Valid letters
    valid_cases = [
        ("A", 1),
        ("Z", 26),
        ("AA", 27),
        ("AZ", 52),
        ("BA", 53),
        ("XFD", 16384),  # Excel max column
    ]

    for col, expected in valid_cases:
        result = writer._column_letter_to_index(col)
        assert result == expected

    # These should NOT be treated as Excel letters (mixed case, etc.)
    # The fix ensures only pure A-Z strings go through this function
    assert writer._column_letter_to_index("a") == 1  # Lowercase converted
    assert writer._column_letter_to_index("abc") == 731


def test_resolve_column_index_with_max_columns_validation():
    """Test that max_columns validation works correctly"""
    writer = ExcelWriter()

    # Test with max_columns=10
    max_columns = 10

    # Valid: within bounds
    assert writer._resolve_column_index("A", max_columns=max_columns) == 1
    assert writer._resolve_column_index(5, max_columns=max_columns) == 5
    assert writer._resolve_column_index("10", max_columns=max_columns) == 10

    # Invalid: exceed bounds
    with pytest.raises(ValueError, match="超出最大列数"):
        writer._resolve_column_index("K", max_columns=max_columns)  # Column 11

    with pytest.raises(ValueError, match="超出最大列数"):
        writer._resolve_column_index(15, max_columns=max_columns)

    with pytest.raises(ValueError, match="超出最大列数"):
        writer._resolve_column_index("20", max_columns=max_columns)

    # Headers within bounds should work
    headers = {"姓名": 1, "金额": 10}
    assert (
        writer._resolve_column_index("姓名", headers=headers, max_columns=max_columns)
        == 1
    )
    assert (
        writer._resolve_column_index("金额", headers=headers, max_columns=max_columns)
        == 10
    )

    # Headers exceeding bounds should fail
    headers_invalid = {"超限": 11}
    with pytest.raises(ValueError, match="超出最大列数"):
        writer._resolve_column_index(
            "超限", headers=headers_invalid, max_columns=max_columns
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
