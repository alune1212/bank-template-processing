"""
配置加载器模块

负责从JSON文件加载配置并验证配置结构的正确性。
"""

import json
import logging

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """配置错误异常类"""

    pass


def load_config(config_path: str) -> dict:
    """
    从JSON文件加载配置

    Args:
        config_path: 配置文件路径

    Returns:
        配置字典

    Raises:
        FileNotFoundError: 配置文件不存在
        json.JSONDecodeError: JSON语法错误
    """
    logger.info(f"加载配置文件: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    logger.info("配置文件加载成功")
    return config


def validate_config(config: dict) -> None:
    """
    验证配置结构的完整性

    Args:
        config: 配置字典

    Raises:
        ConfigError: 配置无效时抛出
    """
    logger.info("开始验证配置")

    # 验证必填字段：version
    if "version" not in config:
        raise ConfigError("缺少必填字段: version")
    logger.info(f"配置版本: {config['version']}")

    # 验证必填字段：organization_units
    if "organization_units" not in config:
        raise ConfigError("缺少必填字段: organization_units")

    org_units = config["organization_units"]
    if not isinstance(org_units, dict):
        raise ConfigError("organization_units 必须是字典")

    if not org_units:
        raise ConfigError("organization_units 不能为空")

    logger.info(f"验证 {len(org_units)} 个组织单位配置")

    # 验证每个单位配置
    for unit_name, unit_config in org_units.items():
        _validate_unit_config(unit_name, unit_config)

    logger.info("配置验证成功")


def _validate_unit_config(unit_name: str, unit_config: dict) -> None:
    """
    验证单个单位配置

    Args:
        unit_name: 单位名称
        unit_config: 单位配置字典

    Raises:
        ConfigError: 配置无效时抛出
    """
    logger.debug(f"验证单位配置: {unit_name}")

    # 验证必填字段
    required_fields = [
        "template_path",
        "header_row",
        "field_mappings",
        "transformations",
    ]
    for field in required_fields:
        if field not in unit_config:
            raise ConfigError(f"单位 '{unit_name}' 缺少必填字段: {field}")

    # 验证template_path是字符串
    if not isinstance(unit_config["template_path"], str):
        raise ConfigError(f"单位 '{unit_name}' 的 template_path 必须是字符串")

    # 验证header_row是整数且≥1
    header_row = unit_config["header_row"]
    if not isinstance(header_row, int):
        raise ConfigError(f"单位 '{unit_name}' 的 header_row 必须是整数")

    if header_row < 1:
        raise ConfigError(
            f"单位 '{unit_name}' 的 header_row 必须大于或等于 1，当前值: {header_row}"
        )

    # 验证start_row（如果指定）
    if "start_row" in unit_config:
        start_row = unit_config["start_row"]
        if not isinstance(start_row, int):
            raise ConfigError(f"单位 '{unit_name}' 的 start_row 必须是整数")

        if start_row <= header_row:
            raise ConfigError(
                f"单位 '{unit_name}' 的 start_row ({start_row}) 必须大于 header_row ({header_row})"
            )
    else:
        # 设置默认值：start_row = header_row + 1
        unit_config["start_row"] = header_row + 1
        logger.debug(
            f"单位 '{unit_name}' 使用默认 start_row: {unit_config['start_row']}"
        )

    # 验证field_mappings是字典
    if not isinstance(unit_config["field_mappings"], dict):
        raise ConfigError(f"单位 '{unit_name}' 的 field_mappings 必须是字典")

    # 验证transformations是字典
    if not isinstance(unit_config["transformations"], dict):
        raise ConfigError(f"单位 '{unit_name}' 的 transformations 必须是字典")

    logger.debug(f"单位 '{unit_name}' 配置验证通过")
