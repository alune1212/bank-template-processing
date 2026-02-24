"""批量合并目录模式实现。"""

from __future__ import annotations

import csv
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import openpyxl
import xlrd

from .config_loader import ConfigError, get_unit_config
from .excel_writer import ExcelWriter
from .validator import Validator


MERGE_FILE_PATTERN = re.compile(
    r"^(?P<prefix>.+)_(?P<count>\d+)人_金额(?P<amount>-?\d+(?:\.\d+)?)元$"
)
SUPPORTED_EXTENSIONS = {".xlsx", ".xls", ".csv"}


class MergeFolderError(Exception):
    """批量合并模式错误。"""

    pass


@dataclass(frozen=True)
class MergeInputFile:
    """待合并输入文件元信息。"""

    path: Path
    unit_name: str
    template_name: str
    count: int
    amount: float


@dataclass
class MergeTask:
    """单个汇总文件的执行任务。"""

    unit_name: str
    template_name: str
    rule_group: str
    group_config: dict
    template_path: str
    group_data: list[dict]
    month_param: str
    count: int
    amount: float


def parse_merge_filename(file_path: Path, unit_names: list[str]) -> MergeInputFile:
    """解析合并输入文件名并提取元信息。"""
    if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise MergeFolderError(f"不支持的合并文件格式: {file_path.name}")

    match = MERGE_FILE_PATTERN.match(file_path.stem)
    if not match:
        raise MergeFolderError(f"文件名不符合合并命名规则: {file_path.name}")

    prefix = match.group("prefix")
    count = int(match.group("count"))
    amount = float(match.group("amount"))

    unit_name, template_name = _split_prefix_to_unit_and_template(prefix, unit_names)
    return MergeInputFile(
        path=file_path,
        unit_name=unit_name,
        template_name=template_name,
        count=count,
        amount=amount,
    )


def resolve_rule_group_for_template(config: dict, unit_name: str, template_name: str) -> tuple[str, dict]:
    """
    根据“单位+模板名”解析规则组。

    优先级：
    1. template_selector.default_group_name/special_group_name
    2. 规则组 template_path 的 stem
    """
    org_units = config.get("organization_units", {})
    if unit_name not in org_units:
        raise ConfigError(f"配置文件中未找到单位配置：{unit_name}")

    unit_config = org_units[unit_name]

    # 第一步：按组名匹配（优先）
    selector_config = unit_config.get("template_selector", {}) if isinstance(unit_config, dict) else {}
    default_group_name = selector_config.get("default_group_name")
    special_group_name = selector_config.get("special_group_name")

    group_name_candidates: list[str] = []
    if template_name == default_group_name:
        group_name_candidates.append("default")
    if template_name == special_group_name:
        group_name_candidates.append("crossbank")

    if group_name_candidates:
        unique_candidates = sorted(set(group_name_candidates))
        if len(unique_candidates) != 1:
            raise MergeFolderError(
                f"模板名称 '{template_name}' 同时命中多个组名配置: {', '.join(unique_candidates)}"
            )
        rule_group = unique_candidates[0]
        return rule_group, get_unit_config(config, unit_name, rule_group)

    # 第二步：按模板文件名 stem 回退匹配
    stem_candidates: list[str] = []
    if isinstance(unit_config, dict) and "default" in unit_config:
        for rule_name, rule_config in unit_config.items():
            if rule_name == "template_selector":
                continue
            if not isinstance(rule_config, dict):
                continue
            template_path = rule_config.get("template_path")
            if isinstance(template_path, str) and Path(template_path).stem == template_name:
                stem_candidates.append(rule_name)
    else:
        template_path = unit_config.get("template_path") if isinstance(unit_config, dict) else None
        if isinstance(template_path, str) and Path(template_path).stem == template_name:
            stem_candidates.append("default")

    unique_stem_candidates = sorted(set(stem_candidates))
    if not unique_stem_candidates:
        raise MergeFolderError(
            f"无法为单位 '{unit_name}' 的模板名称 '{template_name}' 匹配规则组，请检查组名或模板路径配置"
        )
    if len(unique_stem_candidates) > 1:
        raise MergeFolderError(
            f"单位 '{unit_name}' 的模板名称 '{template_name}' 匹配到多个规则组: {', '.join(unique_stem_candidates)}"
        )

    rule_group = unique_stem_candidates[0]
    return rule_group, get_unit_config(config, unit_name, rule_group)


def infer_month_param_from_values(month_values: set[str], month_type_mapping: dict) -> str:
    """根据文件中月类型列值推断 month 参数。"""
    if not month_values:
        raise MergeFolderError("month_type_mapping 已启用，但未在输入文件中读取到月类型值")

    inferred_params = {_infer_month_param_from_single_value(value, month_type_mapping) for value in month_values}
    if len(inferred_params) != 1:
        raise MergeFolderError(
            f"同一分组存在冲突的月类型值: {sorted(month_values)}，推断结果: {sorted(inferred_params)}"
        )
    return inferred_params.pop()


def prepare_merge_tasks(
    merge_folder_path: str,
    config: dict,
    resolve_path_fn: Callable[[str], str],
    apply_transformations_fn: Callable[[list, dict, dict], list],
    needs_transformations_fn: Callable[[dict], bool],
    calculate_stats_fn: Callable[[list, dict, dict], tuple[int, float]],
    logger: logging.Logger,
) -> list[MergeTask]:
    """扫描并准备批量合并任务。"""
    merge_folder = Path(merge_folder_path)
    if not merge_folder.exists():
        raise FileNotFoundError(f"合并目录不存在: {merge_folder}")
    if not merge_folder.is_dir():
        raise MergeFolderError(f"合并路径不是目录: {merge_folder}")

    organization_units = config.get("organization_units", {})
    if not isinstance(organization_units, dict) or not organization_units:
        raise ConfigError("配置缺少 organization_units，无法执行批量合并")

    unit_names = list(organization_units.keys())
    input_files = _scan_merge_input_files(merge_folder, unit_names)
    logger.info("批量合并扫描完成：目录 %s 共发现 %s 个输入文件", merge_folder, len(input_files))

    grouped_files: dict[tuple[str, str], list[MergeInputFile]] = {}
    for input_file in input_files:
        group_key = (input_file.unit_name, input_file.template_name)
        grouped_files.setdefault(group_key, []).append(input_file)

    logger.info("按单位+模板分组完成：共 %s 组", len(grouped_files))
    merge_tasks: list[MergeTask] = []

    for unit_name, template_name in sorted(grouped_files.keys()):
        files = sorted(grouped_files[(unit_name, template_name)], key=lambda item: item.path.name)
        logger.info("处理合并分组：%s_%s（%s 个文件）", unit_name, template_name, len(files))

        rule_group, group_config = resolve_rule_group_for_template(config, unit_name, template_name)
        template_path_raw = group_config.get("template_path", "")
        if not template_path_raw:
            raise ConfigError(f"单位 '{unit_name}' 的规则组 '{rule_group}' 未配置 template_path")
        template_path = resolve_path_fn(template_path_raw)

        merged_group_data: list[dict] = []
        merged_month_values: set[str] = set()
        count_from_name = 0
        amount_from_name = 0.0

        for file_meta in files:
            file_rows, month_values = _read_generated_file_rows(file_meta.path, group_config)
            merged_group_data.extend(file_rows)
            merged_month_values.update(month_values)
            count_from_name += file_meta.count
            amount_from_name += file_meta.amount
            logger.info(
                "已读取文件 %s：提取 %s 行，文件名统计 人数=%s 金额=%.2f",
                file_meta.path.name,
                len(file_rows),
                file_meta.count,
                file_meta.amount,
            )

        validation_rules = group_config.get("validation_rules", {})
        if validation_rules:
            logger.info("分组 %s_%s 开始数据校验", unit_name, template_name)
            for row in merged_group_data:
                if "required_fields" in validation_rules:
                    Validator.validate_required(row, validation_rules["required_fields"])
                if "data_types" in validation_rules:
                    Validator.validate_data_types(row, validation_rules["data_types"])
                if "value_ranges" in validation_rules:
                    Validator.validate_value_ranges(row, validation_rules["value_ranges"])

        field_mappings = group_config.get("field_mappings", {})
        transformations = group_config.get("transformations", {})
        if needs_transformations_fn(field_mappings):
            logger.info("分组 %s_%s 开始数据转换", unit_name, template_name)
            merged_group_data = apply_transformations_fn(merged_group_data, transformations, field_mappings)

        count_from_data, amount_from_data = calculate_stats_fn(merged_group_data, field_mappings, transformations)

        if count_from_data != count_from_name:
            raise MergeFolderError(
                f"分组 '{unit_name}_{template_name}' 人数校验失败：文件名累加={count_from_name}，数据重算={count_from_data}"
            )
        if abs(amount_from_data - amount_from_name) > 0.01:
            raise MergeFolderError(
                "分组 '{0}_{1}' 金额校验失败：文件名累加={2:.2f}，数据重算={3:.2f}".format(
                    unit_name,
                    template_name,
                    amount_from_name,
                    amount_from_data,
                )
            )

        month_param = ""
        month_type_mapping = group_config.get("month_type_mapping", {})
        if isinstance(month_type_mapping, dict) and month_type_mapping.get("enabled"):
            month_param = infer_month_param_from_values(merged_month_values, month_type_mapping)
            logger.info("分组 %s_%s 月份参数推断成功：%s", unit_name, template_name, month_param)

        merge_tasks.append(
            MergeTask(
                unit_name=unit_name,
                template_name=template_name,
                rule_group=rule_group,
                group_config=group_config,
                template_path=template_path,
                group_data=merged_group_data,
                month_param=month_param,
                count=count_from_data,
                amount=amount_from_data,
            )
        )

    return merge_tasks


def _scan_merge_input_files(merge_folder: Path, unit_names: list[str]) -> list[MergeInputFile]:
    excel_files = sorted(
        path for path in merge_folder.iterdir() if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )
    if not excel_files:
        raise MergeFolderError(f"目录中未找到可合并的 Excel 文件: {merge_folder}")

    parsed_files: list[MergeInputFile] = []
    for file_path in excel_files:
        parsed_files.append(parse_merge_filename(file_path, unit_names))
    return parsed_files


def _split_prefix_to_unit_and_template(prefix: str, unit_names: list[str]) -> tuple[str, str]:
    for unit_name in sorted(unit_names, key=len, reverse=True):
        marker = f"{unit_name}_"
        if prefix.startswith(marker):
            template_name = prefix[len(marker) :]
            if not template_name:
                raise MergeFolderError(f"文件名前缀缺少模板名称: {prefix}")
            return unit_name, template_name

    raise MergeFolderError(f"文件名前缀无法匹配单位名称: {prefix}")


def _read_generated_file_rows(file_path: Path, group_config: dict) -> tuple[list[dict], set[str]]:
    rows = _read_all_rows(file_path)
    max_columns = max((len(row) for row in rows), default=0)

    header_row = group_config.get("header_row", 1)
    start_row = group_config.get("start_row", header_row + 1)
    if not isinstance(start_row, int) or start_row < 1:
        raise MergeFolderError(f"文件 {file_path.name} 的 start_row 配置无效: {start_row}")

    headers = _extract_headers(rows, header_row, file_path)
    field_mappings = group_config.get("field_mappings", {})

    writer = ExcelWriter()
    bindings = _build_field_bindings(field_mappings, headers, max_columns, writer, file_path)
    month_col_idx = _resolve_month_column(group_config, headers, max_columns, writer, file_path)

    data_rows: list[dict] = []
    month_values: set[str] = set()

    for row_number in range(start_row, len(rows) + 1):
        row_values = rows[row_number - 1]
        row_dict: dict[str, Any] = {}
        has_data = False

        for source_column, col_idx in bindings:
            value = _get_cell_value(row_values, col_idx)
            row_dict[source_column] = value
            if not _is_empty_value(value):
                has_data = True

        if not has_data:
            continue

        if month_col_idx is not None:
            month_value = _get_cell_value(row_values, month_col_idx)
            if not _is_empty_value(month_value):
                month_values.add(str(month_value).strip())

        data_rows.append(row_dict)

    return data_rows, month_values


def _build_field_bindings(
    field_mappings: dict,
    headers: dict[str, int],
    max_columns: int,
    writer: ExcelWriter,
    file_path: Path,
) -> list[tuple[str, int]]:
    bindings: list[tuple[str, int]] = []
    for template_column, mapping_config in field_mappings.items():
        if isinstance(mapping_config, dict):
            source_column = mapping_config.get("source_column")
            target_column = mapping_config.get("target_column", template_column)
        else:
            source_column = template_column
            target_column = mapping_config

        if not source_column:
            raise MergeFolderError(f"文件 {file_path.name} 的字段映射缺少 source_column: {template_column}")

        try:
            col_idx = writer._resolve_column_index_by_mode(
                target_column,
                headers,
                max_columns,
                "column_name",
            )
        except ValueError as e:
            raise MergeFolderError(
                f"文件 {file_path.name} 无法解析字段 '{template_column}' 的目标列 '{target_column}': {e}"
            ) from e

        bindings.append((str(source_column), col_idx))

    return bindings


def _resolve_month_column(
    group_config: dict,
    headers: dict[str, int],
    max_columns: int,
    writer: ExcelWriter,
    file_path: Path,
) -> int | None:
    month_type_mapping = group_config.get("month_type_mapping", {})
    if not isinstance(month_type_mapping, dict) or not month_type_mapping.get("enabled"):
        return None

    target_column = month_type_mapping.get("target_column", "C")
    try:
        return writer._resolve_column_index_by_mode(target_column, headers, max_columns, "column_name")
    except ValueError as e:
        raise MergeFolderError(
            f"文件 {file_path.name} 无法解析 month_type_mapping.target_column '{target_column}': {e}"
        ) from e


def _extract_headers(rows: list[list[Any]], header_row: int, file_path: Path) -> dict[str, int]:
    if not isinstance(header_row, int) or header_row < 0:
        raise MergeFolderError(f"文件 {file_path.name} 的 header_row 配置无效: {header_row}")
    if header_row == 0:
        return {}
    if header_row > len(rows):
        raise MergeFolderError(f"文件 {file_path.name} 的 header_row 超出文件行数: {header_row}")

    header_values = rows[header_row - 1]
    headers: dict[str, int] = {}
    for col_idx, value in enumerate(header_values, start=1):
        if _is_empty_value(value):
            continue
        headers[str(value).strip()] = col_idx
    return headers


def _read_all_rows(file_path: Path) -> list[list[Any]]:
    ext = file_path.suffix.lower()
    if ext == ".xlsx":
        return _read_xlsx_rows(file_path)
    if ext == ".csv":
        return _read_csv_rows(file_path)
    if ext == ".xls":
        return _read_xls_rows(file_path)
    raise MergeFolderError(f"不支持的文件格式: {file_path.name}")


def _read_xlsx_rows(file_path: Path) -> list[list[Any]]:
    workbook = openpyxl.load_workbook(str(file_path), read_only=True, data_only=True)
    try:
        worksheet = workbook.active
        if worksheet is None:
            raise MergeFolderError(f"Excel 文件没有工作表: {file_path.name}")
        return [list(row) for row in worksheet.iter_rows(values_only=True)]
    finally:
        workbook.close()


def _read_csv_rows(file_path: Path) -> list[list[Any]]:
    with open(file_path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.reader(file)
        return [list(row) for row in reader]


def _read_xls_rows(file_path: Path) -> list[list[Any]]:
    workbook = xlrd.open_workbook(str(file_path))
    sheet = workbook.sheet_by_index(0)
    rows: list[list[Any]] = []
    for row_idx in range(sheet.nrows):
        row_values: list[Any] = []
        for col_idx in range(sheet.ncols):
            cell = sheet.cell(row_idx, col_idx)
            row_values.append(_convert_xls_cell(cell, workbook.datemode))
        rows.append(row_values)
    return rows


def _convert_xls_cell(cell: Any, datemode: int) -> Any:
    empty_types = [getattr(xlrd, "XL_CELL_EMPTY", -1), getattr(xlrd, "XL_CELL_BLANK", -1)]
    if cell.ctype in empty_types:
        return None

    if cell.ctype == getattr(xlrd, "XL_CELL_DATE", -1):
        try:
            return xlrd.xldate_as_datetime(cell.value, datemode)
        except Exception:
            return cell.value

    if cell.ctype == getattr(xlrd, "XL_CELL_NUMBER", -1):
        try:
            if float(cell.value).is_integer():
                return int(cell.value)
        except Exception:
            pass
        return cell.value

    if cell.ctype == getattr(xlrd, "XL_CELL_BOOLEAN", -1):
        return bool(cell.value)

    return cell.value


def _get_cell_value(row_values: list[Any], column_index: int) -> Any:
    if column_index < 1:
        return None
    pos = column_index - 1
    if pos >= len(row_values):
        return None
    return row_values[pos]


def _is_empty_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    return False


def _infer_month_param_from_single_value(value: str, month_type_mapping: dict) -> str:
    normalized_value = str(value).strip()
    bonus_value = str(month_type_mapping.get("bonus_value", "年终奖"))
    compensation_value = str(month_type_mapping.get("compensation_value", "补偿金"))

    if normalized_value == bonus_value:
        return "年终奖"
    if normalized_value == compensation_value:
        return "补偿金"

    month_format = month_type_mapping.get("month_format", "{month}月收入")
    if not isinstance(month_format, str):
        raise MergeFolderError(f"month_format 必须是字符串，当前值: {month_format}")

    matched_months: list[str] = []
    for month in range(1, 13):
        month_token = f"{month:02d}"
        try:
            formatted = month_format.format(month=month_token)
        except KeyError as e:
            raise MergeFolderError(f"month_format 缺少变量: {e}") from e
        except Exception as e:
            raise MergeFolderError(f"month_format 格式错误: {e}") from e

        if formatted == normalized_value:
            matched_months.append(month_token)

    if len(matched_months) == 1:
        return matched_months[0]
    if len(matched_months) > 1:
        raise MergeFolderError(
            f"月类型值 '{normalized_value}' 对 month_format 匹配到多个月份: {matched_months}"
        )
    raise MergeFolderError(f"无法从月类型值推断月份参数: '{normalized_value}'")
