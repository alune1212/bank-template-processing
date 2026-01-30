"""
数据验证器模块

提供数据验证功能，包括必填字段验证、数据类型验证和值范围验证。
"""

from datetime import datetime
from typing import List, Any, Dict
import logging


# 配置日志
logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """验证错误异常类"""

    def __init__(self, message: str):
        """
        初始化验证错误

        Args:
            message: 错误消息
        """
        super().__init__(message)
        self.message = message
        logger.error(f"验证错误: {message}")

    def __str__(self) -> str:
        return self.message


class Validator:
    """数据验证器类"""

    @staticmethod
    def validate_required(row: Dict[str, Any], required_fields: List[str]) -> None:
        """
        验证必填字段

        检查必填字段是否存在且非空（None、空字符串、空列表等）

        Args:
            row: 数据行（字典）
            required_fields: 必填字段列表

        Raises:
            ValidationError: 当必填字段缺失或为空时抛出
        """
        logger.debug(f"开始验证必填字段: {required_fields}")

        for field in required_fields:
            if field not in row:
                error_msg = f"必填字段 '{field}' 不存在"
                logger.error(error_msg)
                raise ValidationError(error_msg)

            value = row[field]

            # 检查值为空的情况
            if value is None:
                error_msg = f"必填字段 '{field}' 的值为 None"
                logger.error(error_msg)
                raise ValidationError(error_msg)

            # 检查空字符串
            if isinstance(value, str) and not value.strip():
                error_msg = f"必填字段 '{field}' 的值为空字符串"
                logger.error(error_msg)
                raise ValidationError(error_msg)

            # 检查空列表/字典
            if isinstance(value, (list, dict)) and len(value) == 0:
                error_msg = f"必填字段 '{field}' 的值为空 {type(value).__name__}"
                logger.error(error_msg)
                raise ValidationError(error_msg)

        logger.info(f"必填字段验证通过: {required_fields}")

    @staticmethod
    def validate_data_types(row: Dict[str, Any], type_rules: Dict[str, type]) -> None:
        """
        验证数据类型

        检查字段值是否匹配预期的类型
        支持类型：str, int, float, bool, datetime, list, dict

        Args:
            row: 数据行（字典）
            type_rules: 类型规则字典，格式为 {字段名: 类型}

        Raises:
            ValidationError: 当字段值类型不匹配时抛出
        """
        logger.debug(f"开始验证数据类型: {type_rules}")

        for field, expected_type in type_rules.items():
            if field not in row:
                # 字段不存在，跳过验证（可选）
                logger.warning(f"字段 '{field}' 不存在，跳过类型验证")
                continue

            value = row[field]

            # 处理 datetime 类型
            if expected_type == datetime:
                if not isinstance(value, datetime):
                    error_msg = f"字段 '{field}' 的类型应为 datetime，实际为 {type(value).__name__}"
                    logger.error(error_msg)
                    raise ValidationError(error_msg)
            else:
                # 处理其他类型
                if not isinstance(value, expected_type):
                    error_msg = f"字段 '{field}' 的类型应为 {expected_type.__name__}，实际为 {type(value).__name__}"
                    logger.error(error_msg)
                    raise ValidationError(error_msg)

        logger.info("数据类型验证通过")

    @staticmethod
    def validate_value_ranges(row: Dict[str, Any], range_rules: Dict[str, Dict[str, Any]]) -> None:
        """
        验证值范围

        检查字段值是否在允许的范围内
        支持的范围规则：
        - min: 最小值（包含）
        - max: 最大值（包含）
        - min_length: 最小长度（用于字符串、列表、字典）
        - max_length: 最大长度（用于字符串、列表、字典）
        - allowed_values: 允许的值列表（枚举）

        Args:
            row: 数据行（字典）
            range_rules: 范围规则字典，格式为 {字段名: {规则名: 规则值}}

        Raises:
            ValidationError: 当字段值超出范围时抛出
        """
        logger.debug(f"开始验证值范围: {range_rules}")

        for field, rules in range_rules.items():
            if field not in row:
                # 字段不存在，跳过验证
                logger.warning(f"字段 '{field}' 不存在，跳过范围验证")
                continue

            value = row[field]

            # 验证最小值
            if "min" in rules:
                min_val = rules["min"]
                if value < min_val:
                    error_msg = f"字段 '{field}' 的值 {value} 小于最小值 {min_val}"
                    logger.error(error_msg)
                    raise ValidationError(error_msg)

            # 验证最大值
            if "max" in rules:
                max_val = rules["max"]
                if value > max_val:
                    error_msg = f"字段 '{field}' 的值 {value} 大于最大值 {max_val}"
                    logger.error(error_msg)
                    raise ValidationError(error_msg)

            # 验证最小长度（用于字符串、列表、字典）
            if "min_length" in rules:
                min_len = rules["min_length"]
                if len(value) < min_len:
                    error_msg = f"字段 '{field}' 的长度 {len(value)} 小于最小长度 {min_len}"
                    logger.error(error_msg)
                    raise ValidationError(error_msg)

            # 验证最大长度（用于字符串、列表、字典）
            if "max_length" in rules:
                max_len = rules["max_length"]
                if len(value) > max_len:
                    error_msg = f"字段 '{field}' 的长度 {len(value)} 大于最大长度 {max_len}"
                    logger.error(error_msg)
                    raise ValidationError(error_msg)

            # 验证允许的值（枚举）
            if "allowed_values" in rules:
                allowed = rules["allowed_values"]
                if value not in allowed:
                    error_msg = f"字段 '{field}' 的值 {value} 不在允许的值列表中: {allowed}"
                    logger.error(error_msg)
                    raise ValidationError(error_msg)

        logger.info("值范围验证通过")
