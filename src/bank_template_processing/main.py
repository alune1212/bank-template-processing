"""银行卡进卡模板处理系统 - 主CLI模块"""

import argparse
import logging
import os
import sys
from pathlib import Path

from .config_loader import load_config, validate_config, ConfigError, get_unit_config
from .excel_reader import ExcelReader, ExcelError
from .validator import Validator, ValidationError
from .transformer import Transformer, TransformError
from .excel_writer import ExcelWriter
from .template_selector import TemplateSelector


def get_executable_dir() -> Path:
    """
    获取可执行文件所在目录

    在 PyInstaller 打包的应用中，需要获取可执行文件所在目录
    而不是当前工作目录，以确保能找到同目录下的配置文件。

    Returns:
        可执行文件所在目录的 Path 对象
    """
    if getattr(sys, "frozen", False):
        # PyInstaller 打包后的应用
        return Path(os.path.dirname(sys.executable))
    else:
        # 开发环境：返回项目根目录（从 src/bank_template_processing/main.py 向上两级）
        # __file__ = .../src/bank_template_processing/main.py
        # parents[0] = .../src/bank_template_processing
        # parents[1] = .../src
        # parents[2] = .../ (project root)
        return Path(__file__).parents[2].resolve()


def resolve_path(path: str, base_dir: Path | None = None) -> str:
    """
    解析文件路径，如果是相对路径则相对于可执行文件所在目录

    Args:
        path: 文件路径（可以是绝对路径或相对路径）
        base_dir: 基础目录，如果为 None 则使用可执行文件所在目录

    Returns:
        解析后的绝对路径字符串
    """
    path_obj = Path(path)
    if path_obj.is_absolute():
        return str(path_obj)

    if base_dir is None:
        base_dir = get_executable_dir()

    resolved = base_dir / path_obj
    return str(resolved.resolve())


def validate_month(month: str) -> str:
    """
    验证月份参数

    支持的格式：
    - 数字格式：1-12 或 01-09
    - 关键字格式："年终奖" 或 "补偿金"

    Args:
        month: 月份字符串

    Returns:
        验证通过的月份字符串

    Raises:
        ValueError: 月份格式无效
    """
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
    """
    解析命令行参数

    Args:
        argv: 参数列表，默认使用 sys.argv

    Returns:
        解析后的参数命名空间
    """
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
        """,
    )

    parser.add_argument("excel_path", help="输入Excel文件路径（支持.xlsx, .csv, .xls格式）")

    parser.add_argument("unit_name", help="组织单位名称（必须在配置文件中定义）")

    parser.add_argument("month", help="月份参数（1-12、01-09、'年终奖'或'补偿金'）")

    parser.add_argument("--output-dir", default="output/", help="输出目录（默认：output/）")

    parser.add_argument("--config", default="config.json", help="配置文件路径（默认：config.json）")

    parser.add_argument(
        "--output-filename-template",
        default="{unit_name}_{month}",
        help="输出文件名模板（默认：{unit_name}_{month}）",
    )

    return parser.parse_args(argv)


def generate_output_filename(
    unit_name: str,
    month: str,
    template_name: str | None,
    template_path: str,
    count: int,
    amount: float,
) -> str:
    """
    生成输出文件名

    Args:
        unit_name: 单位名称
        month: 月份参数
        template_name: 模板名称（可选，如果为None则从template_path提取）
        template_path: 模板文件路径（用于获取文件扩展名和模板名称）
        count: 行数
        amount: 总金额

    Returns:
        输出文件名（包含与模板相同的扩展名）
    """
    from pathlib import Path

    template_path_obj = Path(template_path)
    template_ext = template_path_obj.suffix

    # 如果未显式提供template_name，则从template_path中提取模板名称
    if template_name is None:
        template_name = template_path_obj.stem  # 获取不含扩展名的文件名

    return f"{unit_name}_{template_name}_{count}人_金额{amount:.2f}元{template_ext}"


def _calculate_stats(data: list, field_mappings: dict, transformations: dict) -> tuple[int, float]:
    """
    计算统计数据：行数和总金额

    Args:
        data: 数据列表
        field_mappings: 字段映射配置
        transformations: 转换配置

    Returns:
        (行数, 总金额) 的元组
    """
    count = len(data)
    total_amount = 0.0

    # 查找金额列
    amount_column = None
    for _, mapping in field_mappings.items():
        if mapping.get("transform") == "amount_decimal":
            amount_column = mapping.get("source_column")
            break

    if amount_column:
        for row in data:
            val = row.get(amount_column)
            # 处理已转换的浮点数或原始字符串
            if isinstance(val, (int, float)):
                total_amount += float(val)
            elif isinstance(val, str) and val.strip():
                try:
                    total_amount += float(val)
                except (ValueError, TypeError):
                    pass

    return count, total_amount


def setup_logging() -> None:
    """配置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def apply_transformations(data: list, transformations: dict, field_mappings: dict) -> list:
    """
    应用转换规则到数据

    Args:
        data: 数据列表
        transformations: 转换配置（定义转换参数，如 decimal_places）
        field_mappings: 字段映射配置（定义哪些字段需要转换，及转换类型）

    Returns:
        转换后的数据列表
    """
    transformer = Transformer()
    result = []

    for row in data:
        new_row = row.copy()

        # 遍历字段映射，找到需要转换的字段
        for template_field, mapping_config in field_mappings.items():
            # 仅支持新格式
            source_field = mapping_config.get("source_column", template_field)
            transform_type = mapping_config.get("transform", "none")

            value = new_row.get(source_field, "")
            if not value:
                continue

            # 根据转换类型和配置应用转换
            if transform_type == "amount_decimal":
                transform_config = transformations.get("amount_decimal", {})
                decimal_places = transform_config.get("decimal_places", 2)
                new_row[source_field] = transformer.transform_amount(value, decimal_places)
            elif transform_type == "card_number":
                new_row[source_field] = transformer.transform_card_number(value)
            elif transform_type == "date_format":
                transform_config = transformations.get("date_format", {})
                output_format = transform_config.get("output_format", "YYYY-MM-DD")
                new_row[source_field] = transformer.transform_date(value, output_format)

        result.append(new_row)

    return result


def process_group(
    group_data: list,
    group_config: dict,
    template_path: str,
    output_path: Path,
    month_param: str,
    logger,
) -> None:
    """
    处理单个分组的数据

    Args:
        group_data: 分组数据
        group_config: 分组配置
        template_path: 模板路径
        output_path: 输出路径
        month_param: 月份参数
        logger: 日志记录器
    """
    field_mappings = group_config.get("field_mappings", {})
    header_row = group_config.get("header_row", 1)
    start_row = group_config.get("start_row", header_row + 1)
    mapping_mode = "column_name"
    fixed_values = group_config.get("fixed_values", {})
    auto_number = group_config.get("auto_number", {"enabled": False})
    bank_branch_mapping = group_config.get("bank_branch_mapping", {"enabled": False})
    month_type_mapping = group_config.get("month_type_mapping", {"enabled": False})

    logger.info(f"写入输出文件：{output_path}")
    writer = ExcelWriter()
    writer.write_excel(
        template_path=template_path,
        data=group_data,
        field_mappings=field_mappings,
        output_path=str(output_path),
        header_row=header_row,
        start_row=start_row,
        mapping_mode=mapping_mode,
        fixed_values=fixed_values,
        auto_number=auto_number,
        bank_branch_mapping=bank_branch_mapping,
        month_type_mapping=month_type_mapping,
        month_param=month_param,
    )
    logger.info(f"输出文件已保存：{output_path}")


def main(argv=None) -> None:
    """
    主函数

    Args:
        argv: 命令行参数列表，默认使用 sys.argv
    """
    logger = None
    try:
        setup_logging()
        logger = logging.getLogger(__name__)

        args = parse_args(argv)
        logger.info(f"开始处理：{args.excel_path}，单位：{args.unit_name}，月份：{args.month}")

        validated_month = validate_month(args.month)
        logger.info(f"月份参数验证通过：{validated_month}")

        # 处理配置文件路径：如果是相对路径，则相对于可执行文件所在目录
        config_path = Path(args.config)
        if not config_path.is_absolute():
            # 相对路径：相对于可执行文件所在目录
            executable_dir = get_executable_dir()
            config_path = executable_dir / config_path
            logger.info(f"配置文件相对路径已解析为：{config_path}")

        logger.info(f"加载配置文件：{config_path}")
        config = load_config(str(config_path))
        validate_config(config)
        logger.info(f"配置版本：{config['version']}")

        if args.unit_name not in config["organization_units"]:
            raise ConfigError(f"配置文件中未找到单位配置：{args.unit_name}")

        logger.info(f"加载单位配置：{args.unit_name}")

        # 获取原始配置以检查模板选择器设置
        raw_unit_config = config["organization_units"][args.unit_name]
        template_selection_rules = raw_unit_config.get("template_selector", config.get("template_selection_rules", {}))
        selector_enabled = template_selection_rules.get("enabled", False)

        # 获取默认配置用于单模板模式或作为基础配置
        default_unit_config = get_unit_config(config, args.unit_name, "default")
        row_filter = default_unit_config.get("row_filter", {})

        reader = ExcelReader(row_filter=row_filter)
        data = reader.read_excel(args.excel_path)
        logger.info(f"读取到 {len(data)} 行数据")

        if not selector_enabled:
            logger.info("使用默认模板（未启用模板选择）")

            template_path = default_unit_config["template_path"]
            # 处理模板路径：如果是相对路径，则相对于可执行文件所在目录
            original_template_path = template_path
            template_path = resolve_path(template_path)
            if template_path != original_template_path:
                logger.info(f"模板路径相对路径已解析为：{template_path}")

            validation_rules = default_unit_config.get("validation_rules", {})
            if validation_rules:
                logger.info("验证输入数据")

                for row in data:
                    if "required_fields" in validation_rules:
                        Validator.validate_required(row, validation_rules["required_fields"])
                    if "type_rules" in validation_rules:
                        Validator.validate_data_types(row, validation_rules["type_rules"])
                    if "range_rules" in validation_rules:
                        Validator.validate_value_ranges(row, validation_rules["range_rules"])

                logger.info("数据验证通过")

            transformations = default_unit_config.get("transformations", {})
            field_mappings = default_unit_config.get("field_mappings", {})
            if transformations:
                logger.info("转换数据")
                data = apply_transformations(data, transformations, field_mappings)
                logger.info("数据转换完成")

            count, amount = _calculate_stats(data, field_mappings, transformations)
            output_filename = generate_output_filename(
                args.unit_name,
                validated_month,
                None,
                template_path,
                count,
                amount,
            )
            output_path = Path(args.output_dir) / output_filename
            Path(args.output_dir).mkdir(parents=True, exist_ok=True)

            process_group(
                data,
                default_unit_config,
                template_path,
                output_path,
                validated_month,
                logger,
            )
        else:
            logger.info("启用动态模板选择")
            # TemplateSelector 期望接收包含 "template_selector" 键的配置字典
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

                template_path = group_info["template"]
                template_name = group_info["group_name"]

                logger.info(f"处理组：{group_key}，模板：{template_name}，数据行数：{len(group_data)}")

                rule_group = "crossbank" if group_key == "special" else group_key

                group_config = get_unit_config(config, args.unit_name, rule_group)
                logger.info(f"使用规则组配置：{rule_group}")

                if not template_path:
                    template_path = group_config.get("template_path", "")
                    if not template_path:
                        raise ConfigError(f"规则组 '{rule_group}' 未配置 template_path")
                    # 处理模板路径：如果是相对路径，则相对于可执行文件所在目录
                    original_template_path = template_path
                    template_path = resolve_path(template_path)
                    if template_path != original_template_path:
                        logger.info(f"模板路径相对路径已解析为：{template_path}")
                    logger.info(f"使用规则组配置中的模板路径：{template_path}")
                else:
                    # 处理模板路径：如果是相对路径，则相对于可执行文件所在目录
                    original_template_path = template_path
                    template_path = resolve_path(template_path)
                    if template_path != original_template_path:
                        logger.info(f"模板路径相对路径已解析为：{template_path}")

                validation_rules = group_config.get("validation_rules", {})
                if validation_rules:
                    logger.info("验证输入数据")

                    for row in group_data:
                        if "required_fields" in validation_rules:
                            Validator.validate_required(row, validation_rules["required_fields"])
                        if "type_rules" in validation_rules:
                            Validator.validate_data_types(row, validation_rules["type_rules"])
                        if "range_rules" in validation_rules:
                            Validator.validate_value_ranges(row, validation_rules["range_rules"])

                    logger.info("数据验证通过")

                transformations = group_config.get("transformations", {})
                field_mappings = group_config.get("field_mappings", {})
                if transformations:
                    logger.info("转换数据")
                    group_data = apply_transformations(group_data, transformations, field_mappings)
                    logger.info("数据转换完成")

                count, amount = _calculate_stats(group_data, field_mappings, transformations)
                output_filename = generate_output_filename(
                    args.unit_name,
                    validated_month,
                    template_name,
                    template_path,
                    count,
                    amount,
                )
                output_path = output_dir / output_filename

                process_group(
                    group_data,
                    group_config,
                    template_path,
                    output_path,
                    validated_month,
                    logger,
                )

        logger.info("处理完成")

    except (
        ConfigError,
        ExcelError,
        ValidationError,
        TransformError,
        ValueError,
        FileNotFoundError,
    ) as e:
        if logger:
            logger.error(f"错误：{e}")
        else:
            print(f"错误：{e}")
        sys.exit(1)
    except Exception as e:
        if logger:
            logger.error(f"未知错误：{e}")
        else:
            print(f"未知错误：{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
