"""配置相关的静态类型定义。"""

from __future__ import annotations

from typing import Any, NotRequired, TypedDict


class ReaderOptions(TypedDict, total=False):
    """输入读取选项。"""

    data_only: bool
    header_row: int


class ClearRowsConfig(TypedDict, total=False):
    """输出数据区清理范围。"""

    start_row: int
    end_row: int
    data_end_row: int


class ValidationRangeRule(TypedDict, total=False):
    """单字段范围校验规则。"""

    min: Any
    max: Any
    min_length: int
    max_length: int
    allowed_values: list[Any]


class ValidationRules(TypedDict, total=False):
    """数据校验规则集合。"""

    required_fields: list[str]
    data_types: dict[str, str]
    value_ranges: dict[str, ValidationRangeRule]


class FieldMappingConfig(TypedDict, total=False):
    """单字段映射配置。"""

    source_column: str
    target_column: str | int
    transform: str
    required: bool


FieldMappingValue = FieldMappingConfig | str | int
FieldMappings = dict[str, FieldMappingValue]


class AutoNumberConfig(TypedDict, total=False):
    """自动编号配置。"""

    enabled: bool
    column: str | int
    column_name: str | int
    start_from: int | None


class MonthTypeMappingConfig(TypedDict, total=False):
    """月份类型映射配置。"""

    enabled: bool
    target_column: str | int
    month_format: str
    bonus_value: str
    compensation_value: str


class TemplateSelectorConfig(TypedDict, total=False):
    """动态模板选择配置。"""

    enabled: bool
    default_bank: str
    special_template: str
    bank_column: str
    default_group_name: str
    special_group_name: str


class InputFilenameRouteConfig(TypedDict):
    """输入文件名路由规则。"""

    project_code: str
    rule_group: str


class InputFilenameRoutingConfig(TypedDict, total=False):
    """输入文件名路由配置。"""

    enabled: bool
    routes: list[InputFilenameRouteConfig]


class RuleGroupConfig(TypedDict, total=False):
    """规则组配置。"""

    template_path: str
    header_row: int
    start_row: int
    reader_options: ReaderOptions
    clear_rows: ClearRowsConfig
    row_filter: dict[str, Any]
    field_mappings: FieldMappings
    fixed_values: dict[str, Any]
    auto_number: AutoNumberConfig
    bank_branch_mapping: dict[str, Any]
    month_type_mapping: MonthTypeMappingConfig
    transformations: dict[str, dict[str, Any]]
    validation_rules: ValidationRules


class MultiRuleUnitConfig(TypedDict, total=False):
    """多规则组单位配置。"""

    template_selector: TemplateSelectorConfig
    input_filename_routing: InputFilenameRoutingConfig
    default: RuleGroupConfig
    crossbank: RuleGroupConfig

    # 允许更多自定义规则组
    __extra_items__: NotRequired[dict[str, Any]]


class AppConfig(TypedDict, total=False):
    """应用顶层配置。"""

    version: str
    organization_units: dict[str, Any]
