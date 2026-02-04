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


ALLOWED_DATA_TYPES = {
    "numeric",
    "date",
    "datetime",
    "string",
    "str",
    "int",
    "integer",
    "float",
    "bool",
    "boolean",
    "list",
    "dict",
}


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


def get_unit_config(config: dict, unit_name: str, template_key: str | None = None) -> dict:
    """
    获取单位配置，支持多规则组结构

    Args:
        config: 配置字典
        unit_name: 单位名称
        template_key: 模板标识符（如 "default", "crossbank"），用于多规则组结构

    Returns:
        单位配置字典

    说明:
        支持两种配置结构：
        1. 旧结构（向后兼容）：所有规则直接在单位配置下
        2. 新结构（多规则组）：规则在 default/crossbank 等子组下

        旧结构示例：
        {
          "organization_units": {
            "单位名": {
              "template_path": "...",
              "field_mappings": {...},
              ...
            }
          }
        }

        新结构示例：
        {
          "organization_units": {
            "单位名": {
              "default": {
                "template_path": "...",
                "field_mappings": {...},
                ...
              },
              "crossbank": {
                "template_path": "...",
                "field_mappings": {...},
                ...
              }
            }
          }
        }
    """
    org_units = config.get("organization_units", {})

    if unit_name not in org_units:
        raise ConfigError(f"配置文件中未找到单位配置：{unit_name}")

    unit_config = org_units[unit_name]

    # 检查是否为多规则组结构
    # 判断方法：单位配置下是否有 "default" 键
    if "default" in unit_config:
        # 多规则组结构
        if template_key is None:
            # 如果没有指定 template_key，返回默认规则组
            return unit_config["default"]
        else:
            # 返回指定的规则组
            if template_key in unit_config:
                return unit_config[template_key]
            else:
                logger.warning(f"单位 '{unit_name}' 中未找到规则组 '{template_key}'，使用默认规则组")
                return unit_config["default"]
    else:
        # 旧结构（向后兼容）
        if template_key is not None:
            logger.warning(f"单位 '{unit_name}' 使用旧配置结构，忽略 template_key 参数")
        return unit_config


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

    # 检查是否为多规则组结构
    # 判断方法：单位配置下是否有 "default" 键
    if "default" in unit_config:
        # 多规则组结构：验证每个规则组
        for rule_name, rule_config in unit_config.items():
            if rule_name == "template_selector":
                # template_selector 放在顶层，跳过验证
                continue
            _validate_rule_group_config(unit_name, rule_name, rule_config)
    else:
        # 旧结构（向后兼容）
        _validate_legacy_unit_config(unit_name, unit_config)


def _validate_validation_rules(unit_name: str, validation_rules: dict, rule_name: str | None = None) -> None:
    """
    验证 validation_rules 配置

    Args:
        unit_name: 单位名称
        validation_rules: 验证规则
        rule_name: 规则组名称（可选）
    """
    prefix = f"单位 '{unit_name}'"
    if rule_name:
        prefix = f"单位 '{unit_name}' 的规则组 '{rule_name}'"

    if not isinstance(validation_rules, dict):
        raise ConfigError(f"{prefix} 的 validation_rules 必须是字典")

    if "type_rules" in validation_rules or "range_rules" in validation_rules:
        raise ConfigError(f"{prefix} 的 validation_rules 仅支持 data_types/value_ranges，请勿使用旧键名")

    if "required_fields" in validation_rules:
        required_fields = validation_rules["required_fields"]
        if not isinstance(required_fields, list) or any(not isinstance(item, str) for item in required_fields):
            raise ConfigError(f"{prefix} 的 validation_rules.required_fields 必须是字符串列表")

    if "data_types" in validation_rules:
        data_types = validation_rules["data_types"]
        if not isinstance(data_types, dict):
            raise ConfigError(f"{prefix} 的 validation_rules.data_types 必须是字典")
        for field_name, type_name in data_types.items():
            if not isinstance(type_name, str):
                raise ConfigError(
                    f"{prefix} 的 validation_rules.data_types 中 '{field_name}' 必须是字符串类型名"
                )
            if type_name.strip().lower() not in ALLOWED_DATA_TYPES:
                raise ConfigError(
                    f"{prefix} 的 validation_rules.data_types 中 '{field_name}' 类型不支持: {type_name}"
                )

    if "value_ranges" in validation_rules:
        value_ranges = validation_rules["value_ranges"]
        if not isinstance(value_ranges, dict):
            raise ConfigError(f"{prefix} 的 validation_rules.value_ranges 必须是字典")
        for field_name, rules in value_ranges.items():
            if not isinstance(rules, dict):
                raise ConfigError(
                    f"{prefix} 的 validation_rules.value_ranges 中 '{field_name}' 必须是字典"
                )
            if "allowed_values" in rules and not isinstance(rules["allowed_values"], list):
                raise ConfigError(
                    f"{prefix} 的 validation_rules.value_ranges 中 '{field_name}'.allowed_values 必须是列表"
                )


def _validate_legacy_unit_config(unit_name: str, unit_config: dict) -> None:
    """
    验证旧结构的单位配置（向后兼容）

    Args:
        unit_name: 单位名称
        unit_config: 单位配置字典
    """
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

    # 验证header_row是整数且≥0
    header_row = unit_config["header_row"]
    if not isinstance(header_row, int):
        raise ConfigError(f"单位 '{unit_name}' 的 header_row 必须是整数")

    if header_row < 0:
        raise ConfigError(f"单位 '{unit_name}' 的 header_row 必须大于或等于 0，当前值: {header_row}")

    # 验证start_row（如果指定）
    if "start_row" in unit_config:
        start_row = unit_config["start_row"]
        if not isinstance(start_row, int):
            raise ConfigError(f"单位 '{unit_name}' 的 start_row 必须是整数")

        if start_row <= header_row:
            raise ConfigError(f"单位 '{unit_name}' 的 start_row ({start_row}) 必须大于 header_row ({header_row})")
    else:
        # 设置默认值：start_row = max(1, header_row + 1)
        unit_config["start_row"] = max(1, header_row + 1)
        logger.debug(f"单位 '{unit_name}' 使用默认 start_row: {unit_config['start_row']}")

    # 验证field_mappings是字典
    if not isinstance(unit_config["field_mappings"], dict):
        raise ConfigError(f"单位 '{unit_name}' 的 field_mappings 必须是字典")

    # 验证field_mappings的每一项允许新旧格式
    for field_name, field_config in unit_config["field_mappings"].items():
        if isinstance(field_config, dict):
            if "source_column" not in field_config:
                raise ConfigError(f"单位 '{unit_name}' 的 field_mappings 中 '{field_name}' 缺少 source_column")
        elif isinstance(field_config, (str, int)):
            logger.warning(
                f"单位 '{unit_name}' 的 field_mappings 中 '{field_name}' 使用旧格式，建议迁移为字典配置"
            )
        else:
            raise ConfigError(
                f"单位 '{unit_name}' 的 field_mappings 中 '{field_name}' 的配置必须是字典或字符串"
            )

    # 验证transformations是字典
    if not isinstance(unit_config["transformations"], dict):
        raise ConfigError(f"单位 '{unit_name}' 的 transformations 必须是字典")

    if "validation_rules" in unit_config:
        _validate_validation_rules(unit_name, unit_config["validation_rules"])

    if "clear_rows" in unit_config:
        _validate_clear_rows(unit_name, unit_config["clear_rows"])

    _validate_reader_options(unit_name, unit_config)


def _validate_rule_group_config(unit_name: str, rule_name: str, rule_config: dict) -> None:
    """
    验证规则组配置

    Args:
        unit_name: 单位名称
        rule_name: 规则组名称（如 "default", "crossbank"）
        rule_config: 规则组配置字典
    """
    logger.debug(f"验证单位 '{unit_name}' 的规则组 '{rule_name}'")

    # 验证必填字段
    required_fields = [
        "template_path",
        "header_row",
        "field_mappings",
        "transformations",
    ]
    for field in required_fields:
        if field not in rule_config:
            raise ConfigError(f"单位 '{unit_name}' 的规则组 '{rule_name}' 缺少必填字段: {field}")

    # 验证template_path是字符串
    if not isinstance(rule_config["template_path"], str):
        raise ConfigError(f"单位 '{unit_name}' 的规则组 '{rule_name}' 的 template_path 必须须是字符串")

    # 验证header_row是整数且≥0
    header_row = rule_config["header_row"]
    if not isinstance(header_row, int):
        raise ConfigError(f"单位 '{unit_name}' 的规则组 '{rule_name}' 的 header_row 必须须是整数")

    if header_row < 0:
        raise ConfigError(
            f"单位 '{unit_name}' 的规则组 '{rule_name}' 的 header_row 必须须大于或等于 0，当前值: {header_row}"
        )

    # 验证start_row（如果指定）
    if "start_row" in rule_config:
        start_row = rule_config["start_row"]
        if not isinstance(start_row, int):
            raise ConfigError(f"单位 '{unit_name}' 的规则组 '{rule_name}' 的 start_row 必须须是整数")

        if start_row <= header_row:
            raise ConfigError(
                f"单位 '{unit_name}' 的规则组 '{rule_name}' 的 start_row ({start_row}) 必须大于 header_row ({header_row})"
            )
    else:
        # 设置默认值：start_row = max(1, header_row + 1)
        rule_config["start_row"] = max(1, header_row + 1)
        logger.debug(f"单位 '{unit_name}' 的规则组 '{rule_name}' 使用默认 start_row: {rule_config['start_row']}")

    # 验证field_mappings是字典
    if not isinstance(rule_config["field_mappings"], dict):
        raise ConfigError(f"单位 '{unit_name}' 的规则组 '{rule_name}' 的 field_mappings 必须须是字典")

    # 验证field_mappings的每一项允许新旧格式
    for field_name, field_config in rule_config["field_mappings"].items():
        if isinstance(field_config, dict):
            if "source_column" not in field_config:
                raise ConfigError(
                    f"单位 '{unit_name}' 的规则组 '{rule_name}' 的 field_mappings 中 '{field_name}' 缺少 source_column"
                )
        elif isinstance(field_config, (str, int)):
            logger.warning(
                f"单位 '{unit_name}' 的规则组 '{rule_name}' 的 field_mappings 中 '{field_name}' 使用旧格式，建议迁移为字典配置"
            )
        else:
            raise ConfigError(
                f"单位 '{unit_name}' 的规则组 '{rule_name}' 的 field_mappings 中 '{field_name}' 的配置必须是字典或字符串"
            )

    # 验证transformations是字典
    if not isinstance(rule_config["transformations"], dict):
        raise ConfigError(f"单位 '{unit_name}' 的规则组 '{rule_name}' 的 transformations 必须须是字典")

    if "validation_rules" in rule_config:
        _validate_validation_rules(unit_name, rule_config["validation_rules"], rule_name=rule_name)

    if "clear_rows" in rule_config:
        _validate_clear_rows(unit_name, rule_config["clear_rows"], rule_name=rule_name)

    _validate_reader_options(unit_name, rule_config, rule_name=rule_name)


def _validate_reader_options(unit_name: str, config: dict, rule_name: str | None = None) -> None:
    """验证 reader_options 配置"""
    if "reader_options" not in config:
        return

    options = config["reader_options"]
    prefix = f"单位 '{unit_name}'"
    if rule_name:
        prefix = f"单位 '{unit_name}' 的规则组 '{rule_name}'"

    if not isinstance(options, dict):
        raise ConfigError(f"{prefix} 的 reader_options 必须是字典")

    if "data_only" in options and not isinstance(options["data_only"], bool):
        raise ConfigError(f"{prefix} 的 reader_options.data_only 必须是布尔值")

    if "header_row" in options:
        header_row = options["header_row"]
        if not isinstance(header_row, int) or header_row < 1:
            raise ConfigError(f"{prefix} 的 reader_options.header_row 必须是 >= 1 的整数")


def _validate_clear_rows(unit_name: str, clear_rows: dict, rule_name: str | None = None) -> None:
    """验证 clear_rows 配置"""
    prefix = f"单位 '{unit_name}'"
    if rule_name:
        prefix = f"单位 '{unit_name}' 的规则组 '{rule_name}'"

    if not isinstance(clear_rows, dict):
        raise ConfigError(f"{prefix} 的 clear_rows 必须是字典")

    if "end_row" in clear_rows and "data_end_row" in clear_rows:
        raise ConfigError(f"{prefix} 的 clear_rows 不能同时包含 end_row 与 data_end_row")

    end_row = clear_rows.get("end_row", clear_rows.get("data_end_row"))
    if end_row is None:
        raise ConfigError(f"{prefix} 的 clear_rows 必须包含 end_row 或 data_end_row")

    if not isinstance(end_row, int) or end_row < 1:
        raise ConfigError(f"{prefix} 的 clear_rows.end_row 必须是 >= 1 的整数")

    start_row = clear_rows.get("start_row")
    if start_row is not None:
        if not isinstance(start_row, int) or start_row < 1:
            raise ConfigError(f"{prefix} 的 clear_rows.start_row 必须是 >= 1 的整数")
        if start_row > end_row:
            raise ConfigError(f"{prefix} 的 clear_rows.start_row 不能大于 end_row")
