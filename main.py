"""银行卡进卡模板处理系统 - 主CLI模块"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

from config_loader import load_config, validate_config, ConfigError
from excel_reader import ExcelReader, ExcelError
from validator import Validator, ValidationError
from transformer import Transformer, TransformError
from excel_writer import ExcelWriter
from template_selector import TemplateSelector


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
    # 关键字格式
    if month in ["年终奖", "补偿金"]:
        return month

    # 数字格式：1-12 或 01-09
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

    parser.add_argument(
        "excel_path", help="输入Excel文件路径（支持.xlsx, .csv, .xls格式）"
    )

    parser.add_argument("unit_name", help="组织单位名称（必须在配置文件中定义）")

    parser.add_argument("month", help="月份参数（1-12、01-09、'年终奖'或'补偿金'）")

    parser.add_argument(
        "--output-dir", default="output/", help="输出目录（默认：output/）"
    )

    parser.add_argument(
        "--config", default="config.json", help="配置文件路径（默认：config.json）"
    )

    parser.add_argument(
        "--output-filename-template",
        default="{unit_name}_{month}",
        help="输出文件名模板（默认：{unit_name}_{month}）",
    )

    return parser.parse_args(argv)


def generate_timestamp() -> str:
    """
    生成紧凑格式的时间戳

    Returns:
        时间戳字符串，格式：YYYYMMDD_HHMMSS
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def generate_output_filename(
    unit_name: str,
    month: str,
    template_name: str | None,
    timestamp: str,
    template_path: str,
) -> str:
    """
    生成输出文件名

    Args:
        unit_name: 单位名称
        month: 月份参数
        template_name: 模板名称（可选）
        timestamp: 时间戳字符串
        template_path: 模板文件路径（用于获取文件扩展名）

    Returns:
        输出文件名（包含与模板相同的扩展名）
    """
    from pathlib import Path

    template_ext = Path(template_path).suffix

    if template_name:
        return f"{unit_name}_{template_name}_{month}_{timestamp}{template_ext}"
    else:
        return f"{unit_name}_{month}_{timestamp}{template_ext}"


def setup_logging() -> None:
    """配置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def apply_transformations(data: list, transformations: dict) -> list:
    """
    应用转换规则到数据

    Args:
        data: 数据列表
        transformations: 转换配置

    Returns:
        转换后的数据列表
    """
    transformer = Transformer()
    result = []

    for row in data:
        new_row = row.copy()
        for field, transform_config in transformations.items():
            transform_type = transform_config.get("type")

            if transform_type == "date":
                value = new_row.get(field, "")
                if value:
                    new_row[field] = transformer.transform_date(value)
            elif transform_type == "amount":
                value = new_row.get(field, "")
                if value:
                    decimal_places = transform_config.get("decimal_places", 2)
                    new_row[field] = transformer.transform_amount(value, decimal_places)
            elif transform_type == "card_number":
                value = new_row.get(field, "")
                if value:
                    new_row[field] = transformer.transform_card_number(value)

        result.append(new_row)

    return result


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
        logger.info(
            f"开始处理：{args.excel_path}，单位：{args.unit_name}，月份：{args.month}"
        )

        validated_month = validate_month(args.month)
        logger.info(f"月份参数验证通过：{validated_month}")

        logger.info(f"加载配置文件：{args.config}")
        config = load_config(args.config)
        validate_config(config)
        logger.info(f"配置版本：{config['version']}")

        if args.unit_name not in config["organization_units"]:
            raise ConfigError(f"配置文件中未找到单位配置：{args.unit_name}")

        unit_config = config["organization_units"][args.unit_name]
        logger.info(f"加载单位配置：{args.unit_name}")

        logger.info(f"读取输入文件：{args.excel_path}")

        # 获取行过滤配置
        row_filter = unit_config.get("row_filter", {})
        reader = ExcelReader(row_filter=row_filter)
        data = reader.read_excel(args.excel_path)
        logger.info(f"读取到 {len(data)} 行数据")

        validation_rules = unit_config.get("validation_rules", {})
        if validation_rules:
            logger.info("验证输入数据")

            for row in data:
                if "required_fields" in validation_rules:
                    Validator.validate_required(
                        row, validation_rules["required_fields"]
                    )
                if "type_rules" in validation_rules:
                    Validator.validate_data_types(row, validation_rules["type_rules"])
                if "range_rules" in validation_rules:
                    Validator.validate_value_ranges(
                        row, validation_rules["range_rules"]
                    )

            logger.info("数据验证通过")

        transformations = unit_config.get("transformations", {})
        if transformations:
            logger.info("转换数据")
            data = apply_transformations(data, transformations)
            logger.info("数据转换完成")

        template_selection_rules = config.get("template_selection_rules", {})
        selector_enabled = template_selection_rules.get("enabled", False)

        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        field_mappings = unit_config.get("field_mappings", {})
        header_row = unit_config.get("header_row", 1)
        start_row = unit_config.get("start_row", header_row + 1)
        mapping_mode = "column_name"
        fixed_values = unit_config.get("fixed_values", {})
        auto_number = unit_config.get("auto_number", {"enabled": False})
        bank_branch_mapping = unit_config.get("bank_branch_mapping", {"enabled": False})
        month_type_mapping = unit_config.get("month_type_mapping", {"enabled": False})

        if not selector_enabled:
            logger.info("使用默认模板（未启用模板选择）")

            template_path = unit_config["template_path"]
            output_filename = generate_output_filename(
                args.unit_name,
                validated_month,
                None,
                generate_timestamp(),
                template_path,
            )
            output_path = output_dir / output_filename

            logger.info(f"写入输出文件：{output_path}")
            writer = ExcelWriter()
            writer.write_excel(
                template_path=template_path,
                data=data,
                field_mappings=field_mappings,
                output_path=str(output_path),
                header_row=header_row,
                start_row=start_row,
                mapping_mode=mapping_mode,
                fixed_values=fixed_values,
                auto_number=auto_number,
                bank_branch_mapping=bank_branch_mapping,
                month_type_mapping=month_type_mapping,
                month_param=validated_month,
            )
            logger.info(f"输出文件已保存：{output_path}")
        else:
            logger.info("启用动态模板选择")
            selector = TemplateSelector(template_selection_rules)

            default_bank = template_selection_rules.get("default_bank", "")
            bank_column = template_selection_rules.get("bank_column", "开户银行")

            groups = selector.group_data(data, default_bank, bank_column)
            logger.info(f"数据分组完成，共 {len(groups)} 个组")

            for group_key, group_info in groups.items():
                group_data = group_info["data"]

                if not group_data:
                    logger.info(f"跳过空组：{group_key}")
                    continue

                template_path = group_info["template"]
                template_name = group_info["group_name"]

                output_filename = generate_output_filename(
                    args.unit_name,
                    validated_month,
                    template_name,
                    generate_timestamp(),
                    template_path,
                )
                output_path = output_dir / output_filename

                logger.info(
                    f"处理组：{group_key}，模板：{template_name}，数据行数：{len(group_data)}"
                )
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
                    month_param=validated_month,
                )
                logger.info(f"输出文件已保存：{output_path}")

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
