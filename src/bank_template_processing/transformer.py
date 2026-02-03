"""
数据转换器模块

提供日期、金额、卡号等数据类型转换功能，包括格式验证和标准化处理。
"""

import logging
import re
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation


# 配置日志
logger = logging.getLogger(__name__)


class TransformError(Exception):
    """数据转换失败异常"""

    pass


class Transformer:
    """数据转换器，提供日期、金额、卡号等转换功能"""

    # 支持的日期输入格式（按优先级顺序）
    DATE_INPUT_FORMATS = [
        "%Y-%m-%d",  # YYYY-MM-DD
        "%d/%m/%Y",  # DD/MM/YYYY
        "%m/%d/%Y",  # MM/DD/YYYY
        "%Y年%m月%d日",  # 中文格式 YYYY年MM月DD日
        "%Y-%m-%d",  # YYYY-MM-DD (支持单数字月日)
    ]

    def __init__(self):
        """初始化转换器"""
        logger.debug("Transformer 初始化")

    def transform_date(self, value, output_format="YYYY-MM-DD") -> str:
        """
        日期转换：解析输入日期并格式化为指定格式

        支持的输入格式：
        - YYYY-MM-DD
        - DD/MM/YYYY
        - MM/DD/YYYY
        - YYYY年MM月DD日
        - YYYY-M-D（支持单数字月日）

        Args:
            value: 输入日期（字符串）
            output_format: 输出格式，默认为 "YYYY-MM-DD"

        Returns:
            str: 格式化后的日期字符串

        Raises:
            TransformError: 如果日期解析失败
        """
        logger.debug(f"开始日期转换: value={value}, output_format={output_format}")

        if not value:
            error_msg = "日期值为空"
            logger.error(error_msg)
            raise TransformError(error_msg)

        # 将输出格式转换为 Python datetime 格式
        if output_format == "YYYY-MM-DD":
            python_output_format = "%Y-%m-%d"
        else:
            # 目前仅支持 YYYY-MM-DD 输出格式
            error_msg = f"不支持的输出格式: {output_format}"
            logger.error(error_msg)
            raise TransformError(error_msg)

        # 支持 datetime/date 直接格式化
        if isinstance(value, (datetime, date)):
            result = value.strftime(python_output_format)
            logger.debug(f"日期转换成功: {value} -> {result} (datetime/date)")
            return result

        # 尝试各种输入格式
        for fmt in self.DATE_INPUT_FORMATS:
            try:
                parsed_date = datetime.strptime(str(value), fmt)
                result = parsed_date.strftime(python_output_format)
                logger.debug(f"日期转换成功: {value} -> {result} (使用格式: {fmt})")
                return result
            except ValueError:
                logger.debug(f"日期格式 '{fmt}' 解析失败: {value}")
                continue

        # 所有格式都失败
        error_msg = f"无法解析日期: {value}，已尝试所有格式"
        logger.error(error_msg)
        raise TransformError(error_msg)

    def transform_amount(self, value, decimal_places=2) -> float:
        """
        金额转换：使用标准舍入到指定小数位

        使用 Decimal 模块进行精确的浮点数运算，避免精度问题

        Args:
            value: 输入金额（数字或字符串）
            decimal_places: 小数位数，默认为 2

        Returns:
            float: 舍入后的金额

        Raises:
            TransformError: 如果金额转换失败
        """
        logger.debug(f"开始金额转换: value={value}, decimal_places={decimal_places}")

        if value is None or value == "":
            error_msg = "金额值为空"
            logger.error(error_msg)
            raise TransformError(error_msg)

        try:
            # 使用 Decimal 进行精确运算
            decimal_value = Decimal(str(value))

            # 使用四舍五入
            rounded_value = decimal_value.quantize(Decimal(f"1.{'0' * decimal_places}"), rounding=ROUND_HALF_UP)

            result = float(rounded_value)
            logger.debug(f"金额转换成功: {value} -> {result}")
            return result

        except (InvalidOperation, ValueError, TypeError) as e:
            error_msg = f"金额转换失败: {value}, 错误: {e}"
            logger.error(error_msg)
            raise TransformError(error_msg) from e

    def _luhn_check(self, card_number: str) -> bool:
        """
        Luhn 算法验证银行卡号

        算法步骤：
        1. 从右向左遍历
        2. 奇数位（从右数）乘以 2
        3. 如果乘积大于 9，则减去 9
        4. 将所有数字相加
        5. 总和能被 10 整除则有效

        Args:
            card_number: 卡号字符串（仅包含数字）

        Returns:
            bool: 卡号是否通过 Luhn 验证
        """
        logger.debug(f"开始 Luhn 验证: {card_number}")

        total = 0
        # 从右向左遍历，index=0 是最右边的一位（校验位）
        for index, digit_char in enumerate(reversed(card_number)):
            digit = int(digit_char)

            # 从右数，偶数位（索引为奇数，即第 2, 4, 6... 位）乘以 2
            if index % 2 == 1:  # 这是第 2, 4, 6... 位（从右数）
                doubled = digit * 2
                # 如果乘积大于 9，减去 9（等同于各位数字相加）
                if doubled > 9:
                    doubled -= 9
                total += doubled
            else:  # 奇数位（从右数，即第 1, 3, 5... 位），直接相加
                total += digit

        result = total % 10 == 0
        logger.debug(f"Luhn 验证结果: {result} (总和: {total})")
        return result

    def transform_card_number(self, value) -> str:
        """
        卡号转换：移除非数字字符，并进行 Luhn 验证

        处理步骤：
        1. 移除所有非数字字符
        2. 验证卡号长度（中国银行卡号通常为 13-19 位）
        3. 执行 Luhn 算法验证

        Args:
            value: 输入卡号（字符串）

        Returns:
            str: 清理后的卡号（仅数字）

        Raises:
            TransformError: 如果卡号无效或验证失败
        """
        logger.debug(f"开始卡号转换: value={value}")

        if not value:
            error_msg = "卡号值为空"
            logger.error(error_msg)
            raise TransformError(error_msg)

        # 预处理数值类型，避免科学计数法
        if isinstance(value, Decimal):
            if value == value.to_integral_value():
                value_str = format(value, "f").split(".")[0]
            else:
                value_str = format(value, "f")
        elif isinstance(value, int):
            value_str = str(value)
        elif isinstance(value, float):
            if value.is_integer():
                value_str = format(value, ".0f")
            else:
                value_str = str(value)
        else:
            value_str = str(value)

        # 移除所有非数字字符
        cleaned = re.sub(r"[^\d]", "", value_str)

        if not cleaned:
            error_msg = f"卡号不包含任何数字: {value}"
            logger.error(error_msg)
            raise TransformError(error_msg)

        # 验证卡号长度（中国银行卡号通常为 13-19 位）
        if len(cleaned) < 13 or len(cleaned) > 19:
            error_msg = f"卡号长度不符合要求: {len(cleaned)} 位（应为 13-19 位）"
            logger.error(error_msg)
            raise TransformError(error_msg)

        # 执行 Luhn 验证
        if not self._luhn_check(cleaned):
            error_msg = f"卡号 Luhn 验证失败: {cleaned}"
            logger.error(error_msg)
            raise TransformError(error_msg)

        logger.debug(f"卡号转换成功: {value} -> {cleaned}")
        return cleaned
