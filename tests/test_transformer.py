"""
数据转换器测试模块

测试 Transformer 类的日期、金额、卡号转换功能
"""

import pytest
from transformer import Transformer, TransformError


class TestTransformDate:
    """测试日期转换功能"""

    def test_transform_date_yyyy_mm_dd(self):
        """测试 YYYY-MM-DD 格式转换"""
        transformer = Transformer()
        result = transformer.transform_date("2024-01-15")
        assert result == "2024-01-15"

    def test_transform_date_dd_mm_yyyy(self):
        """测试 DD/MM/YYYY 格式转换"""
        transformer = Transformer()
        result = transformer.transform_date("15/01/2024")
        assert result == "2024-01-15"

    def test_transform_date_mm_dd_yyyy(self):
        """测试 MM/DD/YYYY 格式转换"""
        transformer = Transformer()
        result = transformer.transform_date("01/15/2024")
        assert result == "2024-01-15"

    def test_transform_date_chinese_format(self):
        """测试中文格式 YYYY年MM月DD日 转换"""
        transformer = Transformer()
        result = transformer.transform_date("2024年01月15日")
        assert result == "2024-01-15"

    def test_transform_date_single_digit(self):
        """测试 YYYY-M-D 格式（单数字月日）转换"""
        transformer = Transformer()
        result = transformer.transform_date("2024-1-5")
        assert result == "2024-01-05"

    def test_transform_date_empty_value(self):
        """测试空值转换失败"""
        transformer = Transformer()
        with pytest.raises(TransformError, match="日期值为空"):
            transformer.transform_date("")

    def test_transform_date_invalid_format(self):
        """测试无效日期格式转换失败"""
        transformer = Transformer()
        with pytest.raises(TransformError, match="无法解析日期"):
            transformer.transform_date("2024/01/15")  # 斜杠在错误的位置

    def test_transform_date_invalid_date(self):
        """测试无效日期（如 2月30日）转换失败"""
        transformer = Transformer()
        with pytest.raises(TransformError, match="无法解析日期"):
            transformer.transform_date("2024-02-30")


class TestTransformAmount:
    """测试金额转换功能"""

    def test_transform_amount_integer(self):
        """测试整数金额转换"""
        transformer = Transformer()
        result = transformer.transform_amount(100)
        assert result == 100.0

    def test_transform_amount_decimal(self):
        """测试带小数的金额转换"""
        transformer = Transformer()
        result = transformer.transform_amount(100.123)
        assert result == 100.12  # 四舍五入

    def test_transform_amount_round_up(self):
        """测试四舍五入（向上）"""
        transformer = Transformer()
        result = transformer.transform_amount(100.125)
        assert result == 100.13

    def test_transform_amount_round_down(self):
        """测试四舍五入（向下）"""
        transformer = Transformer()
        result = transformer.transform_amount(100.124)
        assert result == 100.12

    def test_transform_amount_string(self):
        """测试字符串金额转换"""
        transformer = Transformer()
        result = transformer.transform_amount("100.567")
        assert result == 100.57

    def test_transform_amount_negative(self):
        """测试负数金额转换"""
        transformer = Transformer()
        result = transformer.transform_amount(-100.456)
        assert result == -100.46

    def test_transform_amount_custom_decimal_places(self):
        """测试自定义小数位数"""
        transformer = Transformer()
        result = transformer.transform_amount(100.123456, decimal_places=4)
        assert result == 100.1235

    def test_transform_amount_empty_value(self):
        """测试空值转换失败"""
        transformer = Transformer()
        with pytest.raises(TransformError, match="金额值为空"):
            transformer.transform_amount("")

    def test_transform_amount_none_value(self):
        """测试 None 值转换失败"""
        transformer = Transformer()
        with pytest.raises(TransformError, match="金额值为空"):
            transformer.transform_amount(None)

    def test_transform_amount_invalid_string(self):
        """测试无效字符串转换失败"""
        transformer = Transformer()
        with pytest.raises(TransformError, match="金额转换失败"):
            transformer.transform_amount("invalid")


class TestTransformCardNumber:
    """测试卡号转换功能"""

    # 中国工商银行测试卡号（通过 Luhn 验证）
    VALID_CARD_ICBC = "6222021234567890128"

    def test_transform_card_number_clean_spaces(self):
        """测试移除空格"""
        transformer = Transformer()
        result = transformer.transform_card_number("6222 0212 3456 7890 128")
        assert result == "6222021234567890128"

    def test_transform_card_number_clean_dashes(self):
        """测试移除横杠"""
        transformer = Transformer()
        result = transformer.transform_card_number("6222-0212-3456-7890-128")
        assert result == "6222021234567890128"

    def test_transform_card_number_clean_mixed(self):
        """测试移除混合非数字字符"""
        transformer = Transformer()
        result = transformer.transform_card_number("6222 0212-3456 7890-128")
        assert result == "6222021234567890128"

    def test_transform_card_number_valid_luhn(self):
        """测试有效卡号通过 Luhn 验证"""
        transformer = Transformer()
        # 这个卡号是有效的，通过了 Luhn 算法验证
        result = transformer.transform_card_number(self.VALID_CARD_ICBC)
        assert result == self.VALID_CARD_ICBC

    def test_transform_card_number_invalid_luhn(self):
        """测试无效卡号 Luhn 验证失败"""
        transformer = Transformer()
        # 最后一位改成 4，使 Luhn 验证失败
        invalid_card = "6222021234567890124"
        with pytest.raises(TransformError, match="Luhn 验证失败"):
            transformer.transform_card_number(invalid_card)

    def test_transform_card_number_too_short(self):
        """测试卡号过短"""
        transformer = Transformer()
        with pytest.raises(TransformError, match="卡号长度不符合要求"):
            transformer.transform_card_number("123456789012")

    def test_transform_card_number_too_long(self):
        """测试卡号过长"""
        transformer = Transformer()
        with pytest.raises(TransformError, match="卡号长度不符合要求"):
            transformer.transform_card_number("12345678901234567890")

    def test_transform_card_number_empty_value(self):
        """测试空值转换失败"""
        transformer = Transformer()
        with pytest.raises(TransformError, match="卡号值为空"):
            transformer.transform_card_number("")

    def test_transform_card_number_no_digits(self):
        """测试无数字转换失败"""
        transformer = Transformer()
        with pytest.raises(TransformError, match="卡号不包含任何数字"):
            transformer.transform_card_number("abcd-efgh")


class TestLuhnAlgorithm:
    """测试 Luhn 算法"""

    def test_luhn_valid_cards(self):
        """测试通过 Luhn 验证的卡号"""
        transformer = Transformer()
        valid_cards = [
            "4532015112830366",  # Visa
            "6222021234567890128",  # 中国工商银行
            "4111111111111111",  # Visa 测试卡号
        ]
        for card in valid_cards:
            assert transformer._luhn_check(card), f"卡号 {card} 应该通过 L通过验证"

    def test_luhn_invalid_cards(self):
        """测试未通过 Luhn 验证的卡号"""
        transformer = Transformer()
        invalid_cards = [
            "4532015112830367",  # 最后一位错误
            "4111111111111112",  # 最后一位错误
            "1234567890123456",  # 完全无效
        ]
        for card in invalid_cards:
            assert not transformer._luhn_check(card), (
                f"卡号 {card} 不应该通过 Luhn 验证"
            )


class TestTransformerIntegration:
    """集成测试"""

    def test_full_transform_workflow(self):
        """测试完整的转换工作流"""
        transformer = Transformer()

        # 日期转换
        date = transformer.transform_date("15/01/2024")
        assert date == "2024-01-15"

        # 金额转换
        amount = transformer.transform_amount("1000.456")
        assert amount == 1000.46

        # 卡号转换
        card = transformer.transform_card_number("6222-0212-3456-7890-128")
        assert card == "6222021234567890128"
