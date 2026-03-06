"""主处理流程共享管线。"""

from __future__ import annotations

import logging
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, cast

from .config_types import FieldMappings, ReaderOptions, RuleGroupConfig, ValidationRules
from .excel_reader import ExcelReader
from .excel_writer import ExcelWriter
from .transformer import TransformError, Transformer
from .validator import ValidationError, Validator


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProcessingContext:
    """处理上下文。"""

    unit_name: str | None = None
    rule_group: str | None = None
    template_name: str | None = None
    source_file: str | None = None

    def with_source_file(self, source_file: str | None) -> "ProcessingContext":
        """返回带来源文件的新上下文。"""
        return replace(self, source_file=source_file)

    def describe(self, row_number: int | None = None) -> str:
        """格式化上下文说明。"""
        parts: list[str] = []
        if self.unit_name:
            parts.append(f"单位={self.unit_name}")
        if self.rule_group:
            parts.append(f"规则组={self.rule_group}")
        if self.template_name:
            parts.append(f"模板={self.template_name}")
        if self.source_file:
            parts.append(f"来源文件={self.source_file}")
        if row_number is not None:
            parts.append(f"第{row_number}条数据")
        return "，".join(parts)


def enrich_error_context(
    exc: Exception,
    stage: str,
    context: ProcessingContext | None = None,
    row_number: int | None = None,
) -> Exception:
    """为已知异常补充处理上下文。"""
    context_label = context.describe(row_number) if context else ""
    if context_label:
        message = f"{stage}失败（{context_label}）：{exc}"
    else:
        message = f"{stage}失败：{exc}"
    return exc.__class__(message)


def build_reader(
    group_config: RuleGroupConfig | dict[str, Any],
    logger_instance: logging.Logger | None = None,
    reader_cls: type[ExcelReader] = ExcelReader,
) -> ExcelReader:
    """按规则组配置创建读取器。"""
    active_logger = logger_instance or logger
    row_filter = group_config.get("row_filter", {})
    reader_options = group_config.get("reader_options", {})
    if not isinstance(reader_options, dict):
        active_logger.warning("reader_options 配置无效，已忽略")
        reader_options = {}

    header_row = reader_options.get("header_row", 1)
    if not isinstance(header_row, int) or header_row < 1:
        active_logger.warning("reader_options.header_row 配置无效，已使用默认值 1")
        header_row = 1

    options = ReaderOptions(
        data_only=bool(reader_options.get("data_only", False)),
        header_row=header_row,
    )
    return reader_cls(
        row_filter=row_filter,
        data_only=options["data_only"],
        header_row=options["header_row"],
    )


def validate_rows(
    data: list[dict],
    validation_rules: ValidationRules | dict,
    *,
    context: ProcessingContext | None = None,
    source_file_field: str | None = None,
) -> None:
    """逐行执行校验。"""
    if not validation_rules:
        return

    required_fields = validation_rules.get("required_fields")
    data_types = validation_rules.get("data_types")
    value_ranges = validation_rules.get("value_ranges")

    for row_number, row in enumerate(data, start=1):
        row_context = _row_context(context, row, source_file_field)
        try:
            if required_fields:
                Validator.validate_required(row, required_fields)
            if data_types:
                Validator.validate_data_types(row, data_types)
            if value_ranges:
                Validator.validate_value_ranges(row, cast(dict[str, dict[str, Any]], value_ranges))
        except ValidationError as exc:
            raise enrich_error_context(exc, "数据校验", row_context, row_number) from exc


def needs_transformations(field_mappings: FieldMappings | dict) -> bool:
    """判断字段映射中是否包含转换规则。"""
    for mapping in field_mappings.values():
        if not isinstance(mapping, dict):
            continue
        transform_type = mapping.get("transform", "none")
        if transform_type and transform_type != "none":
            return True
    return False


def apply_transformations(
    data: list[dict],
    transformations: dict,
    field_mappings: FieldMappings | dict,
    *,
    context: ProcessingContext | None = None,
    source_file_field: str | None = None,
) -> list[dict]:
    """按字段映射执行数据转换。"""
    transformer = Transformer()
    warned_old_format = False
    result: list[dict] = []

    for row_number, row in enumerate(data, start=1):
        row_context = _row_context(context, row, source_file_field)
        new_row = row.copy()

        for template_field, mapping_config in field_mappings.items():
            if not isinstance(mapping_config, dict):
                if transformations and not warned_old_format:
                    logger.warning("检测到旧格式 field_mappings，转换规则将被忽略，请迁移到字典格式")
                    warned_old_format = True
                continue

            source_field = mapping_config.get("source_column", template_field)
            transform_type = mapping_config.get("transform", "none")
            value = new_row.get(source_field, "")

            if value is None:
                continue
            if isinstance(value, str) and not value.strip():
                continue

            try:
                if transform_type == "amount_decimal":
                    transform_config = transformations.get("amount_decimal", {})
                    decimal_places = transform_config.get("decimal_places", 2)
                    rounding = transform_config.get("rounding", "round")
                    new_row[source_field] = transformer.transform_amount(value, decimal_places, rounding=rounding)
                elif transform_type == "card_number":
                    transform_config = transformations.get("card_number", {})
                    remove_formatting = transform_config.get("remove_formatting", True)
                    luhn_validation = transform_config.get("luhn_validation", True)
                    new_row[source_field] = transformer.transform_card_number(
                        value,
                        remove_formatting=remove_formatting,
                        luhn_validation=luhn_validation,
                    )
                elif transform_type == "date_format":
                    transform_config = transformations.get("date_format", {})
                    output_format = transform_config.get("output_format", "YYYY-MM-DD")
                    new_row[source_field] = transformer.transform_date(value, output_format)
            except TransformError as exc:
                raise enrich_error_context(exc, "数据转换", row_context, row_number) from exc

        result.append(new_row)

    return result


def transform_rows(
    data: list[dict],
    transformations: dict,
    field_mappings: FieldMappings | dict,
    *,
    context: ProcessingContext | None = None,
    source_file_field: str | None = None,
) -> list[dict]:
    """在需要时执行转换。"""
    if not needs_transformations(field_mappings):
        return data
    return apply_transformations(
        data,
        transformations,
        field_mappings,
        context=context,
        source_file_field=source_file_field,
    )


def calculate_stats(data: list[dict], field_mappings: FieldMappings | dict, transformations: dict) -> tuple[int, float]:
    """计算输出文件名所需统计信息。"""
    del transformations  # 保留兼容签名
    count = len(data)
    total_amount = 0.0

    amount_column = None
    for mapping in field_mappings.values():
        if not isinstance(mapping, dict):
            continue
        if mapping.get("transform") == "amount_decimal":
            amount_column = mapping.get("source_column")
            break

    if amount_column:
        for row in data:
            value = row.get(amount_column)
            if isinstance(value, (int, float)):
                total_amount += float(value)
            elif isinstance(value, str) and value.strip():
                try:
                    total_amount += float(value)
                except (ValueError, TypeError):
                    pass

    return count, total_amount


def write_group_output(
    group_data: list[dict],
    group_config: RuleGroupConfig | dict,
    template_path: str,
    output_path: Path,
    month_param: str,
    logger_instance: logging.Logger,
    writer_cls: type[ExcelWriter] = ExcelWriter,
) -> None:
    """将处理后的分组数据写入模板。"""
    field_mappings = group_config.get("field_mappings", {})
    header_row = group_config.get("header_row", 1)
    start_row = group_config.get("start_row", header_row + 1)
    fixed_values = group_config.get("fixed_values", {})
    auto_number = group_config.get("auto_number", {"enabled": False})
    bank_branch_mapping = group_config.get("bank_branch_mapping", {"enabled": False})
    month_type_mapping = group_config.get("month_type_mapping", {"enabled": False})
    clear_rows = group_config.get("clear_rows")

    logger_instance.info(f"写入输出文件：{output_path}")
    writer = writer_cls()
    writer.write_excel(
        template_path=template_path,
        data=group_data,
        field_mappings=field_mappings,
        output_path=str(output_path),
        header_row=header_row,
        start_row=start_row,
        mapping_mode="column_name",
        fixed_values=fixed_values,
        auto_number=auto_number,
        bank_branch_mapping=bank_branch_mapping,
        month_type_mapping=month_type_mapping,
        month_param=month_param,
        clear_rows=clear_rows,
    )
    logger_instance.info(f"输出文件已保存：{output_path}")


def describe_template_name(template_path: str, template_name: str | None = None) -> str:
    """从显式名称或模板路径中推断模板名。"""
    if template_name:
        return template_name
    return Path(template_path).stem


def _row_context(
    context: ProcessingContext | None,
    row: dict,
    source_file_field: str | None,
) -> ProcessingContext | None:
    if context is None or source_file_field is None:
        return context
    source_file = row.get(source_file_field)
    if source_file is None:
        return context
    return context.with_source_file(str(source_file))
