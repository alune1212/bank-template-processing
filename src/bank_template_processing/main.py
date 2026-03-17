"""银行卡进卡模板处理系统 - 主 CLI 模块。"""

from __future__ import annotations

import argparse
import logging
import os
import string
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping

from .config_loader import ConfigError, get_unit_config, load_config, validate_config
from .config_types import AppConfig, RuleGroupConfig
from .excel_reader import ExcelError, ExcelReader
from .excel_writer import ExcelWriter
from .merge_folder import MergeFolderError, prepare_merge_tasks
from .pipeline import (
    ProcessingContext,
    apply_transformations,
    build_reader,
    calculate_stats as _calculate_stats,
    enrich_error_context,
    needs_transformations as _needs_transformations,
    split_validation_rules,
    write_group_output,
)
from .template_selector import TemplateSelector
from .transformer import TransformError, Transformer as _Transformer
from .validator import ValidationError, Validator


Transformer = _Transformer


def get_executable_dir() -> Path:
    """获取可执行文件所在目录。"""
    if getattr(sys, "frozen", False):
        return Path(os.path.dirname(sys.executable))
    return Path(__file__).parents[2].resolve()


def resolve_path(path: str, base_dir: Path | None = None) -> str:
    """解析相对路径为绝对路径。"""
    path_obj = Path(path)
    if path_obj.is_absolute():
        return str(path_obj)

    if base_dir is None:
        base_dir = get_executable_dir()

    return str((base_dir / path_obj).resolve())


def validate_month(month: str) -> str:
    """验证月份参数。"""
    if month in ["年终奖", "补偿金"]:
        return month

    try:
        month_int = int(month)
        if 1 <= month_int <= 12:
            return month
    except ValueError:
        pass

    raise ValueError("月份参数必须是1-12的数字、01-09格式、'年终奖'或'补偿金'")


def parse_args(argv=None) -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        description="银行卡进卡模板处理系统 - 将OA系统数据处理为银行模板格式",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 处理1月份数据
  python main.py input.xlsx 单位名称 01

  # 处理年终奖数据
  python main.py input.xlsx 单位名称 年终奖

  # 自定义输出目录
  python main.py input.xlsx 单位名称 01 --output-dir custom_output/

  # 使用自定义配置文件
  python main.py input.xlsx 单位名称 01 --config custom_config.json

  # 批量合并目录中的已生成模板文件
  python main.py --merge-folder ./output --config config.json
        """,
    )
    parser.add_argument("excel_path", nargs="?", help="输入Excel文件路径（支持.xlsx, .csv, .xls格式）")
    parser.add_argument("unit_name", nargs="?", help="组织单位名称（必须在配置文件中定义）")
    parser.add_argument("month", nargs="?", help="月份参数（1-12、01-09、'年终奖'或'补偿金'）")
    parser.add_argument("--output-dir", default="output/", help="输出目录（默认：output/）")
    parser.add_argument("--config", default="config.json", help="配置文件路径（默认：config.json）")
    parser.add_argument(
        "--merge-folder",
        help="批量合并模式：输入目录路径（会读取目录内已生成模板文件并在 result/ 输出）",
    )
    parser.add_argument(
        "--output-filename-template",
        default="{unit_name}_{template_name}_{count}人_金额{amount:.2f}元{ext}",
        help="输出文件名模板（默认：{unit_name}_{template_name}_{count}人_金额{amount:.2f}元{ext}）",
    )
    return parser.parse_args(argv)


def validate_cli_mode_args(args: argparse.Namespace) -> None:
    """校验命令行模式参数组合是否正确。"""
    has_merge_folder = bool(args.merge_folder)
    has_any_positional = any([args.excel_path, args.unit_name, args.month])
    has_all_positional = all([args.excel_path, args.unit_name, args.month])

    if has_merge_folder:
        if has_any_positional:
            raise ValueError("使用 --merge-folder 时不能同时提供 excel_path/unit_name/month")
        return

    if not has_all_positional:
        raise ValueError("普通模式必须提供 excel_path、unit_name、month 三个参数")


def generate_output_filename(
    unit_name: str,
    month: str,
    template_name: str | None,
    template_path: str,
    count: int,
    amount: float,
    output_template: str | None = None,
) -> str:
    """生成输出文件名。"""
    template_path_obj = Path(template_path)
    template_ext = template_path_obj.suffix
    if template_name is None:
        template_name = template_path_obj.stem

    if output_template:
        try:
            filename = output_template.format(
                unit_name=unit_name,
                month=month,
                template_name=template_name,
                count=count,
                amount=amount,
                ext=template_ext,
            )
        except KeyError as exc:
            raise ValueError(f"输出文件名模板缺少变量: {exc}") from exc

        if "{ext" not in output_template and not filename.endswith(template_ext):
            filename = f"{filename}{template_ext}"
        return filename

    return f"{unit_name}_{template_name}_{count}人_金额{amount:.2f}元{template_ext}"


def _output_template_uses_month(output_template: str | None) -> bool:
    """判断输出文件名模板是否实际使用 month 变量。"""
    if not output_template:
        return False

    formatter = string.Formatter()
    for _, field_name, _, _ in formatter.parse(output_template):
        if field_name is None:
            continue
        root_field = field_name.split(".", 1)[0].split("[", 1)[0]
        if root_field == "month":
            return True

    return False


def setup_logging() -> None:
    """配置日志。"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def _is_zero_salary_value(value) -> bool:
    """判断“实发工资”是否为零值。"""
    if isinstance(value, bool):
        return False
    if value is None:
        return False
    if isinstance(value, (int, float, Decimal)):
        return value == 0
    if isinstance(value, str):
        normalized = value.strip().replace(",", "").replace("，", "")
        if not normalized:
            return False
        try:
            return Decimal(normalized) == 0
        except (InvalidOperation, ValueError):
            return False
    return False


def _filter_zero_salary_rows(data: list[dict], salary_column: str = "实发工资") -> list[dict]:
    """过滤“实发工资”为 0 的数据行。"""
    logger = logging.getLogger(__name__)

    if not data:
        logger.info("实发工资零值筛选完成：原始 0 行，过滤 0 行，保留 0 行")
        return data

    if not any(salary_column in row for row in data):
        raise ValidationError(f"缺少'{salary_column}'列")

    filtered_rows = [row for row in data if not _is_zero_salary_value(row.get(salary_column))]
    filtered_count = len(data) - len(filtered_rows)
    logger.info(
        "实发工资零值筛选完成：原始 %s 行，过滤 %s 行，保留 %s 行",
        len(data),
        filtered_count,
        len(filtered_rows),
    )
    return filtered_rows


def _resolve_runtime_path(path: str, logger: logging.Logger) -> str:
    """解析运行时路径并在相对路径被展开时记录日志。"""
    resolved = resolve_path(path)
    if resolved != path:
        logger.info(f"模板路径相对路径已解析为：{resolved}")
    return resolved


def _read_input_rows(
    excel_path: str,
    group_config: RuleGroupConfig | dict[str, Any],
    context: ProcessingContext,
    logger: logging.Logger,
) -> list[dict]:
    """读取并做零工资过滤。"""
    reader = build_reader(group_config, logger_instance=logger, reader_cls=ExcelReader)
    data = reader.read_excel(excel_path)
    logger.info(f"读取到 {len(data)} 行数据")
    try:
        return _filter_zero_salary_rows(data)
    except ValidationError as exc:
        raise enrich_error_context(exc, "零工资筛选", context) from exc


def _validate_rows(
    data: list[dict],
    validation_rules: Mapping[str, Any],
    context: ProcessingContext,
    logger: logging.Logger,
) -> None:
    """按现有 Validator 行为执行逐行校验。"""
    if not validation_rules:
        return

    logger.info("验证输入数据")
    for row_number, row in enumerate(data, start=1):
        try:
            if "required_fields" in validation_rules:
                Validator.validate_required(row, validation_rules["required_fields"])
            if "data_types" in validation_rules:
                Validator.validate_data_types(row, validation_rules["data_types"])
            if "value_ranges" in validation_rules:
                Validator.validate_value_ranges(row, validation_rules["value_ranges"])
        except ValidationError as exc:
            raise enrich_error_context(exc, "数据校验", context, row_number) from exc
    logger.info("数据验证通过")


def _prepare_group_rows(
    data: list[dict],
    group_config: RuleGroupConfig | dict[str, Any],
    context: ProcessingContext,
    logger: logging.Logger,
) -> tuple[list[dict], int, float]:
    """对单组数据执行校验、转换和统计。"""
    validation_rules = group_config.get("validation_rules", {})
    pre_transform_rules, post_transform_rules = split_validation_rules(validation_rules)
    _validate_rows(data, pre_transform_rules, context, logger)

    transformations = group_config.get("transformations", {})
    field_mappings = group_config.get("field_mappings", {})
    if _needs_transformations(field_mappings):
        logger.info("转换数据")
        try:
            data = apply_transformations(data, transformations, field_mappings, context=context)
        except TypeError as exc:
            if "unexpected keyword argument 'context'" not in str(exc):
                raise
            data = apply_transformations(data, transformations, field_mappings)
        logger.info("数据转换完成")

    _validate_rows(data, post_transform_rules, context, logger)
    count, amount = _calculate_stats(data, field_mappings, transformations)
    return data, count, amount


def process_group(
    group_data: list[dict],
    group_config: RuleGroupConfig | dict[str, Any],
    template_path: str,
    output_path: Path,
    month_param: str,
    logger: logging.Logger,
) -> None:
    """兼容旧测试入口，内部委托共享管线。"""
    write_group_output(
        group_data,
        group_config,
        template_path,
        output_path,
        month_param,
        logger,
        writer_cls=ExcelWriter,
    )


def _write_output_group(
    data: list[dict],
    group_config: RuleGroupConfig | dict[str, Any],
    unit_name: str,
    month: str,
    template_name: str | None,
    template_path: str,
    output_dir: Path,
    output_filename_template: str | None,
    logger: logging.Logger,
) -> None:
    """写出单个分组结果。"""
    count, amount = _calculate_stats(
        data,
        group_config.get("field_mappings", {}),
        group_config.get("transformations", {}),
    )
    output_filename = generate_output_filename(
        unit_name,
        month,
        template_name,
        template_path,
        count,
        amount,
        output_filename_template,
    )
    output_path = output_dir / output_filename
    process_group(data, group_config, template_path, output_path, month, logger)


def _resolve_input_filename_rule_group(
    unit_config: Mapping[str, Any],
    excel_path: str,
) -> str | None:
    """根据输入文件名匹配项目编码路由，返回命中的规则组。"""
    routing = unit_config.get("input_filename_routing")
    if not isinstance(routing, dict):
        return None
    if not routing.get("enabled", False):
        return None

    routes = routing.get("routes", [])
    if not isinstance(routes, list):
        return None

    file_name = Path(excel_path).name.casefold()
    matched_routes: list[tuple[str, str]] = []
    for route in routes:
        if not isinstance(route, dict):
            continue
        project_code = route.get("project_code")
        rule_group = route.get("rule_group")
        if not isinstance(project_code, str) or not project_code.strip():
            continue
        if not isinstance(rule_group, str) or not rule_group.strip():
            continue
        if project_code.strip().casefold() in file_name:
            matched_routes.append((project_code.strip(), rule_group.strip()))

    if not matched_routes:
        return None
    if len(matched_routes) > 1:
        matched_codes = "、".join(project_code for project_code, _ in matched_routes)
        raise ConfigError(f"输入文件名同时命中多个项目编码路由: {matched_codes}")

    return matched_routes[0][1]


def _handle_routed_rule_group_mode(
    args: argparse.Namespace,
    config: AppConfig | dict[str, Any],
    logger: logging.Logger,
    validated_month: str,
    data: list[dict],
    matched_rule_group: str,
) -> None:
    """处理输入文件名路由命中的单规则组输出模式。"""
    logger.info(f"输入文件名命中项目编码路由，使用规则组：{matched_rule_group}")
    matched_group_config = get_unit_config(config, args.unit_name, matched_rule_group)
    template_path = _resolve_runtime_path(matched_group_config["template_path"], logger)

    context = ProcessingContext(
        unit_name=args.unit_name,
        rule_group=matched_rule_group,
        template_name=Path(template_path).stem,
    )
    prepared_rows, _, _ = _prepare_group_rows(data, matched_group_config, context, logger)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_output_group(
        prepared_rows,
        matched_group_config,
        args.unit_name,
        validated_month,
        None,
        template_path,
        output_dir,
        args.output_filename_template,
        logger,
    )


def _handle_merge_mode(args: argparse.Namespace, config: AppConfig | dict[str, Any], logger: logging.Logger) -> None:
    """处理批量合并模式。"""
    logger.info(f"开始批量合并目录：{args.merge_folder}")
    needs_month_for_filename = _output_template_uses_month(args.output_filename_template)
    merge_tasks = prepare_merge_tasks(
        merge_folder_path=args.merge_folder,
        config=config,
        resolve_path_fn=resolve_path,
        apply_transformations_fn=apply_transformations,
        needs_transformations_fn=_needs_transformations,
        calculate_stats_fn=_calculate_stats,
        needs_month_for_filename=needs_month_for_filename,
        logger=logger,
    )

    result_dir = Path(args.merge_folder) / "result"
    result_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"批量合并准备完成，共 {len(merge_tasks)} 个分组，输出目录：{result_dir}")

    for task in merge_tasks:
        output_filename = generate_output_filename(
            task.unit_name,
            task.month_param,
            task.template_name,
            task.template_path,
            task.count,
            task.amount,
            args.output_filename_template,
        )
        process_group(
            task.group_data,
            task.group_config,
            task.template_path,
            result_dir / output_filename,
            task.month_param,
            logger,
        )

    logger.info("批量合并处理完成")


def _handle_default_mode(
    args: argparse.Namespace,
    logger: logging.Logger,
    validated_month: str,
    data: list[dict],
    default_unit_config: RuleGroupConfig | dict[str, Any],
) -> None:
    """处理单模板模式。"""
    logger.info("使用默认模板（未启用模板选择）")
    template_path = _resolve_runtime_path(default_unit_config["template_path"], logger)
    context = ProcessingContext(
        unit_name=args.unit_name,
        rule_group="default",
        template_name=Path(template_path).stem,
    )
    prepared_rows, _, _ = _prepare_group_rows(data, default_unit_config, context, logger)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_output_group(
        prepared_rows,
        default_unit_config,
        args.unit_name,
        validated_month,
        None,
        template_path,
        output_dir,
        args.output_filename_template,
        logger,
    )


def _handle_selector_mode(
    args: argparse.Namespace,
    config: AppConfig | dict[str, Any],
    logger: logging.Logger,
    validated_month: str,
    data: list[dict],
    template_selection_rules: dict,
) -> None:
    """处理动态模板选择模式。"""
    logger.info("启用动态模板选择")
    selector = TemplateSelector({"template_selector": template_selection_rules})
    default_bank = template_selection_rules.get("default_bank", "")
    bank_column = template_selection_rules.get("bank_column", "开户银行")

    groups = selector.group_data(data, default_bank, bank_column)
    logger.info(f"数据分组完成，共 {len(groups)} 个组")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for group_key, group_info in groups.items():
        group_data = group_info["data"]
        if not group_data:
            logger.info(f"跳过空组：{group_key}")
            continue

        rule_group = "crossbank" if group_key == "special" else group_key
        group_config = get_unit_config(config, args.unit_name, rule_group)
        template_name = group_info["group_name"]
        template_path = group_info["template"]

        logger.info(f"处理组：{group_key}，模板：{template_name}，数据行数：{len(group_data)}")
        logger.info(f"使用规则组配置：{rule_group}")

        if not template_path:
            template_path = group_config.get("template_path", "")
            if not template_path:
                raise ConfigError(f"规则组 '{rule_group}' 未配置 template_path")
            template_path = _resolve_runtime_path(template_path, logger)
            logger.info(f"使用规则组配置中的模板路径：{template_path}")
        else:
            template_path = _resolve_runtime_path(template_path, logger)

        context = ProcessingContext(
            unit_name=args.unit_name,
            rule_group=rule_group,
            template_name=template_name,
        )
        prepared_rows, _, _ = _prepare_group_rows(group_data, group_config, context, logger)
        _write_output_group(
            prepared_rows,
            group_config,
            args.unit_name,
            validated_month,
            template_name,
            template_path,
            output_dir,
            args.output_filename_template,
            logger,
        )


def main(argv=None) -> None:
    """CLI 主入口。"""
    logger = None
    try:
        setup_logging()
        logger = logging.getLogger(__name__)

        args = parse_args(argv)
        validate_cli_mode_args(args)

        config_path = Path(args.config)
        if not config_path.is_absolute():
            config_path = get_executable_dir() / config_path
            logger.info(f"配置文件相对路径已解析为：{config_path}")

        logger.info(f"加载配置文件：{config_path}")
        config = load_config(str(config_path))
        validate_config(config)
        logger.info(f"配置版本：{config['version']}")

        if args.merge_folder:
            _handle_merge_mode(args, config, logger)
            return

        logger.info(f"开始处理：{args.excel_path}，单位：{args.unit_name}，月份：{args.month}")
        validated_month = validate_month(args.month)
        logger.info(f"月份参数验证通过：{validated_month}")

        if args.unit_name not in config["organization_units"]:
            raise ConfigError(f"配置文件中未找到单位配置：{args.unit_name}")

        logger.info(f"加载单位配置：{args.unit_name}")
        raw_unit_config = config["organization_units"][args.unit_name]
        template_selection_rules = raw_unit_config.get("template_selector", config.get("template_selection_rules", {}))
        selector_enabled = template_selection_rules.get("enabled", False)
        matched_rule_group = _resolve_input_filename_rule_group(raw_unit_config, args.excel_path)

        if matched_rule_group:
            read_rule_group = matched_rule_group
            read_unit_config = get_unit_config(config, args.unit_name, matched_rule_group)
            default_unit_config = get_unit_config(config, args.unit_name, "default")
        else:
            read_rule_group = "default"
            default_unit_config = get_unit_config(config, args.unit_name, "default")
            read_unit_config = default_unit_config

        read_context = ProcessingContext(unit_name=args.unit_name, rule_group=read_rule_group)
        data = _read_input_rows(args.excel_path, read_unit_config, read_context, logger)

        if matched_rule_group:
            _handle_routed_rule_group_mode(args, config, logger, validated_month, data, matched_rule_group)
        elif not selector_enabled:
            _handle_default_mode(args, logger, validated_month, data, default_unit_config)
        else:
            _handle_selector_mode(args, config, logger, validated_month, data, template_selection_rules)

        logger.info("处理完成")

    except (
        ConfigError,
        ExcelError,
        ValidationError,
        TransformError,
        MergeFolderError,
        ValueError,
        FileNotFoundError,
    ) as exc:
        if logger:
            logger.error(f"错误：{exc}")
        else:
            print(f"错误：{exc}")
        sys.exit(1)
    except Exception as exc:
        if logger:
            logger.error(f"未知错误：{exc}")
        else:
            print(f"未知错误：{exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
