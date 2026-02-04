"""
数据验证器模块

提供数据验证功能，包括必填字段验证、数据类型验证和值范围验证。
"""

from datetime import datetime, date, time
from decimal import Decimal, InvalidOperation
from typing import List, Any, Dict
import logging

from .transformer import Transformer

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
    def _parse_date_string(field: str, value: str) -> datetime:
        for fmt in Transformer.DATE_INPUT_FORMATS:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        raise ValidationError(f"字段 '{field}' 的值 {value} 不是有效日期")

    @staticmethod
    def _parse_numeric_string(field: str, value: str) -> Decimal:
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError) as e:
            raise ValidationError(f"字段 '{field}' 的值 {value} 不是有效数值") from e

    @staticmethod
    def _try_parse_date(value: Any) -> datetime | date | None:
        if isinstance(value, (datetime, date)):
            return value
        if isinstance(value, str):
            for fmt in Transformer.DATE_INPUT_FORMATS:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
        return None

    @staticmethod
    def _is_numeric_value(value: Any) -> bool:
        return isinstance(value, (int, float, Decimal)) and not isinstance(value, bool)

    @staticmethod
    def _coerce_numeric_value(field: str, value: Any) -> Decimal:
        if isinstance(value, Decimal):
            return value
        if isinstance(value, bool):
            raise TypeError("bool 不作为数值处理")
        if isinstance(value, (int, float)):
            return Decimal(str(value))
        if isinstance(value, str):
            return Validator._parse_numeric_string(field, value)
        raise TypeError("无法转换为数值")

    @staticmethod
    def _coerce_numeric_bound(value: Any) -> Decimal:
        if isinstance(value, Decimal):
            return value
        if isinstance(value, bool):
            raise TypeError("bool 不作为数值处理")
        if isinstance(value, (int, float)):
            return Decimal(str(value))
        if isinstance(value, str):
            try:
                return Decimal(str(value))
            except (InvalidOperation, ValueError, TypeError) as e:
                raise TypeError(f"无法转换为数值: {value}") from e
        raise TypeError("无法转换为数值")

    @staticmethod
    def _coerce_date_value(field: str, value: Any, date_mode: str) -> Any:
        if isinstance(value, datetime):
            return value if date_mode == "datetime" else value.date()
        if isinstance(value, date):
            if date_mode == "datetime":
                return datetime.combine(value, time.min)
            return value
        if isinstance(value, str):
            parsed = Validator._parse_date_string(field, value)
            return parsed if date_mode == "datetime" else parsed.date()
        raise TypeError("无法转换为日期")

    @staticmethod
    def _coerce_date_bound(value: Any, date_mode: str) -> Any:
        if isinstance(value, datetime):
            return value if date_mode == "datetime" else value.date()
        if isinstance(value, date):
            if date_mode == "datetime":
                return datetime.combine(value, time.min)
            return value
        if isinstance(value, str):
            try:
                parsed = Validator._parse_date_string("边界", value)
            except ValidationError as e:
                raise TypeError(str(e)) from e
            return parsed if date_mode == "datetime" else parsed.date()
        raise TypeError("无法转换为日期")

    @staticmethod
    def _coerce_for_comparison(field: str, value: Any, min_val: Any, max_val: Any) -> tuple[Any, Any, Any]:
        has_datetime = isinstance(min_val, datetime) or isinstance(max_val, datetime)
        has_date = isinstance(min_val, date) or isinstance(max_val, date)
        if has_datetime or has_date:
            date_mode = "datetime" if has_datetime else "date"
            value_cmp = Validator._coerce_date_value(field, value, date_mode)
            min_cmp = Validator._coerce_date_bound(min_val, date_mode) if min_val is not None else None
            max_cmp = Validator._coerce_date_bound(max_val, date_mode) if max_val is not None else None
            return value_cmp, min_cmp, max_cmp

        value_cmp = Validator._coerce_numeric_value(field, value)
        min_cmp = Validator._coerce_numeric_bound(min_val) if min_val is not None else None
        max_cmp = Validator._coerce_numeric_bound(max_val) if max_val is not None else None
        return value_cmp, min_cmp, max_cmp

    @staticmethod
    def _normalize_allowed_values(
        field: str, value: Any, allowed_values: Any
    ) -> tuple[Any, Any, bool]:
        """
        归一化 allowed_values 以便比较

        Returns:
            (normalized_value, normalized_allowed_values, use_normalized)
        """
        if not isinstance(allowed_values, list):
            return value, allowed_values, False

        value_date = Validator._try_parse_date(value)
        allowed_dates = [Validator._try_parse_date(item) for item in allowed_values]
        if value_date is not None and any(item is not None for item in allowed_dates):
            date_mode = "datetime" if isinstance(value, datetime) or any(
                isinstance(item, datetime) for item in allowed_values
            ) else "date"
            try:
                normalized_value = Validator._coerce_date_value(field, value, date_mode)
            except TypeError as e:
                logger.warning(f"字段 '{field}' 的 allowed_values 日期归一化失败，已回退原值比较: {e}")
                return value, allowed_values, False

            normalized_allowed = []
            for item in allowed_values:
                try:
                    normalized_allowed.append(Validator._coerce_date_bound(item, date_mode))
                except TypeError as e:
                    logger.warning(
                        f"字段 '{field}' 的 allowed_values 日期值无法解析，已保留原值: {e}"
                    )
                    normalized_allowed.append(item)

            return normalized_value, normalized_allowed, True

        try:
            normalized_value = Validator._coerce_numeric_value(field, value)
        except (TypeError, ValidationError) as e:
            logger.warning(f"字段 '{field}' 的 allowed_values 数值归一化失败，已回退原值比较: {e}")
            return value, allowed_values, False

        normalized_allowed = []
        any_numeric = False
        for item in allowed_values:
            try:
                normalized_allowed.append(Validator._coerce_numeric_bound(item))
                any_numeric = True
            except TypeError as e:
                logger.warning(
                    f"字段 '{field}' 的 allowed_values 数值无法解析，已保留原值: {e}"
                )
                normalized_allowed.append(item)

        if not any_numeric:
            return value, allowed_values, False

        return normalized_value, normalized_allowed, True

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
    def validate_data_types(row: Dict[str, Any], type_rules: Dict[str, str]) -> None:
        """
        验证数据类型

        检查字段值是否匹配预期的类型
        支持类型：numeric, date, datetime, string/str, int/integer, float, bool/boolean, list, dict

        Args:
            row: 数据行（字典）
            type_rules: 类型规则字典，格式为 {字段名: 类型名字符串}

        Raises:
            ValidationError: 当字段值类型不匹配时抛出
        """
        logger.debug(f"开始验证数据类型: {type_rules}")

        type_map = {
            "string": str,
            "str": str,
            "int": int,
            "integer": int,
            "float": float,
            "bool": bool,
            "boolean": bool,
            "list": list,
            "dict": dict,
        }

        for field, expected_type in type_rules.items():
            if field not in row:
                # 字段不存在，跳过验证（可选）
                logger.warning(f"字段 '{field}' 不存在，跳过类型验证")
                continue

            value = row[field]
            if value is None or (isinstance(value, str) and not value.strip()):
                logger.debug(f"字段 '{field}' 值为空，跳过类型验证")
                continue

            if not isinstance(expected_type, str):
                error_msg = f"字段 '{field}' 的类型配置必须为字符串"
                logger.error(error_msg)
                raise ValidationError(error_msg)

            type_name = expected_type.strip().lower()

            if type_name == "numeric":
                if Validator._is_numeric_value(value):
                    continue
                if isinstance(value, str):
                    Validator._parse_numeric_string(field, value)
                    continue
                error_msg = f"字段 '{field}' 的类型应为 numeric，实际为 {type(value).__name__}"
                logger.error(error_msg)
                raise ValidationError(error_msg)

            if type_name in ("int", "integer"):
                if isinstance(value, bool):
                    error_msg = f"字段 '{field}' 的类型应为 integer，实际为 bool"
                    logger.error(error_msg)
                    raise ValidationError(error_msg)
                if isinstance(value, int):
                    continue
                if isinstance(value, float) and value.is_integer():
                    continue
                if isinstance(value, Decimal) and value == value.to_integral_value():
                    continue
                if isinstance(value, str):
                    numeric_value = Validator._parse_numeric_string(field, value)
                    if numeric_value == numeric_value.to_integral_value():
                        continue
                error_msg = f"字段 '{field}' 的类型应为 integer，实际为 {type(value).__name__}"
                logger.error(error_msg)
                raise ValidationError(error_msg)

            if type_name in ("date", "datetime"):
                if isinstance(value, (datetime, date)):
                    continue
                if isinstance(value, str):
                    Validator._parse_date_string(field, value)
                    continue
                error_msg = f"字段 '{field}' 的类型应为 {type_name}，实际为 {type(value).__name__}"
                logger.error(error_msg)
                raise ValidationError(error_msg)

            expected_py_type = type_map.get(type_name)
            if expected_py_type is None:
                error_msg = f"字段 '{field}' 的类型不支持: {expected_type}"
                logger.error(error_msg)
                raise ValidationError(error_msg)

            if not isinstance(value, expected_py_type):
                error_msg = (
                    f"字段 '{field}' 的类型应为 {type_name}，实际为 {type(value).__name__}"
                )
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

            if value is None or (isinstance(value, str) and not value.strip()):
                logger.debug(f"字段 '{field}' 值为空，跳过范围验证")
                continue

            # 验证最小值
            if "min" in rules:
                min_val = rules["min"]
                max_val = rules.get("max")
                try:
                    value_cmp, min_cmp, max_cmp = Validator._coerce_for_comparison(field, value, min_val, max_val)
                except ValidationError:
                    raise
                except TypeError as e:
                    logger.warning(f"字段 '{field}' 的范围规则无法比较，已跳过: {e}")
                    continue

                if min_cmp is not None and value_cmp < min_cmp:
                    error_msg = f"字段 '{field}' 的值 {value} 小于最小值 {min_val}"
                    logger.error(error_msg)
                    raise ValidationError(error_msg)

                if max_cmp is not None and value_cmp > max_cmp:
                    error_msg = f"字段 '{field}' 的值 {value} 大于最大值 {max_val}"
                    logger.error(error_msg)
                    raise ValidationError(error_msg)

            # 验证最大值
            if "max" in rules and "min" not in rules:
                max_val = rules["max"]
                try:
                    value_cmp, min_cmp, max_cmp = Validator._coerce_for_comparison(field, value, None, max_val)
                except ValidationError:
                    raise
                except TypeError as e:
                    logger.warning(f"字段 '{field}' 的范围规则无法比较，已跳过: {e}")
                    continue

                if max_cmp is not None and value_cmp > max_cmp:
                    error_msg = f"字段 '{field}' 的值 {value} 大于最大值 {max_val}"
                    logger.error(error_msg)
                    raise ValidationError(error_msg)

            # 验证最小长度（用于字符串、列表、字典）
            if "min_length" in rules:
                min_len = rules["min_length"]
                try:
                    if len(value) < min_len:
                        error_msg = f"字段 '{field}' 的长度 {len(value)} 小于最小长度 {min_len}"
                        logger.error(error_msg)
                        raise ValidationError(error_msg)
                except TypeError:
                    logger.warning(f"字段 '{field}' 不支持长度校验，已跳过 min_length")

            # 验证最大长度（用于字符串、列表、字典）
            if "max_length" in rules:
                max_len = rules["max_length"]
                try:
                    if len(value) > max_len:
                        error_msg = f"字段 '{field}' 的长度 {len(value)} 大于最大长度 {max_len}"
                        logger.error(error_msg)
                        raise ValidationError(error_msg)
                except TypeError:
                    logger.warning(f"字段 '{field}' 不支持长度校验，已跳过 max_length")

            # 验证允许的值（枚举）
            if "allowed_values" in rules:
                allowed = rules["allowed_values"]
                normalized_value, normalized_allowed, use_normalized = Validator._normalize_allowed_values(
                    field, value, allowed
                )
                if use_normalized:
                    if normalized_value in normalized_allowed or value in allowed:
                        continue
                    error_msg = f"字段 '{field}' 的值 {value} 不在允许的值列表中: {allowed}"
                    logger.error(error_msg)
                    raise ValidationError(error_msg)
                else:
                    if value not in allowed:
                        error_msg = f"字段 '{field}' 的值 {value} 不在允许的值列表中: {allowed}"
                        logger.error(error_msg)
                        raise ValidationError(error_msg)

        logger.info("值范围验证通过")
