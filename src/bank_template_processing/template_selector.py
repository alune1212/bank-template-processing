"""
模板选择器模块

提供模板选择功能，根据数据中的银行列将数据分组为默认组和特殊组。
"""

import logging
from typing import List, Dict, Any
from .validator import ValidationError


# 配置日志
logger = logging.getLogger(__name__)


class TemplateSelector:
    """模板选择器类"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化模板选择器

        Args:
            config: 配置字典，包含 template_selector 配置
        """
        logger.debug("初始化模板选择器")
        self.config = config
        self.selector_config = config.get("template_selector", {})
        logger.debug(f"模板选择器配置: {self.selector_config}")

    def is_enabled(self) -> bool:
        """
        检查是否启用模板选择

        Returns:
            bool: True 表示启用，False 表示未启用
        """
        enabled = self.selector_config.get("enabled", False)
        logger.debug(f"模板选择器启用状态: {enabled}")
        return enabled

    def group_data(
        self,
        data: List[Dict[str, Any]],
        default_bank: str,
        bank_column: str = "开户银行",
    ) -> Dict[str, Any]:
        """
        根据银行列分组数据

        分组逻辑：
        1. 验证所有所有行包含 bank_column 字段
        2. 验证所有行的 bank_column 值非空
        3. 根据 bank_column 值分组：
           - bank_column == default_bank → 归入默认组
           - bank_column != default_bank → 归入特殊组

        Args:
            data: 数据列表
            default_bank: 默认银行名称
            bank_column: 银行列名，默认为"开户银行"

        Returns:
            分组结果字典，格式为：
            {
                "default": {
                    "data": [...],
                    "template": template_path,
                    "group_name": "default_group_name"
                },
                "special": {
                    "data": [...],
                    "template": special_template,
                    "group_name": "special_group_name"
                }
            }

            其中 default_group_name 和 special_group_name 从配置中的
            "template_selector.default_group_name" 和 "template_selector.special_group_name" 读取，
            如果未配置则分别使用默认值 "default" 和 "special"。

        Raises:
            ValidationError: 当缺少银行列或银行值为空时抛出
        """
        logger.info(f"开始分组数据，默认银行: {default_bank}, 银行列: {bank_column}")

        # 验证数据
        if not data:
            logger.warning("数据为空列表")
            return self._create_empty_result()

        # 验证第一行是否存在银行列
        if bank_column not in data[0]:
            error_msg = f"缺少'{bank_column}'列"
            logger.error(error_msg)
            raise ValidationError(error_msg)

        # 初始化分组
        default_data = []
        special_data = []

        # 遍历数据进行分组
        for index, row in enumerate(data, start=1):
            # 验证银行列存在
            if bank_column not in row:
                error_msg = f"缺少'{bank_column}'列"
                logger.error(error_msg)
                raise ValidationError(error_msg)

            bank_value = row[bank_column]

            # 验证银行值非空
            if bank_value is None or (isinstance(bank_value, str) and not bank_value.strip()):
                error_msg = f"第{index}行的'{bank_column}'字段为空"
                logger.error(error_msg)
                raise ValidationError(error_msg)

            # 根据银行值分组
            if bank_value == default_bank:
                default_data.append(row)
            else:
                special_data.append(row)

        logger.info(f"分组完成: 默认组 {len(default_data)} 条, 特殊组 {len(special_data)} 条")

        # 构建结果
        return self._build_result(default_data, special_data)

    def _create_empty_result(self) -> Dict[str, Any]:
        """
        创建空分组结果

        Returns:
            空分组结果字典
        """
        return {
            "default": {
                "data": [],
                "template": self.selector_config.get("default_template", ""),
                "group_name": self._extract_group_name(self.selector_config.get("default_template", "")),
            },
            "special": {
                "data": [],
                "template": self.selector_config.get("special_template", ""),
                "group_name": self._extract_group_name(self.selector_config.get("special_template", "")),
            },
        }

    def _build_result(self, default_data: List[Dict], special_data: List[Dict]) -> Dict[str, Any]:
        """
        构建分组结果

        Args:
            default_data: 默认组数据
            special_data: 特殊组数据

        Returns:
            分组结果字典
        """
        default_template = self.selector_config.get("default_template", "")
        special_template = self.selector_config.get("special_template", "")

        default_group_name = self.selector_config.get("default_group_name", "default")
        special_group_name = self.selector_config.get("special_group_name", "special")

        return {
            "default": {
                "data": default_data,
                "template": default_template,
                "group_name": default_group_name,
            },
            "special": {
                "data": special_data,
                "template": special_template,
                "group_name": special_group_name,
            },
        }

    def _extract_group_name(self, template_path: str) -> str:
        """
        从模板文件路径中提取组名

        Args:
            template_path: 模板文件路径，如 "templates/农业银行.xlsx"

        Returns:
            组名，如 "农业银行"
        """
        if not template_path:
            return ""

        # 获取文件名（去除扩展名）
        filename = template_path.split("/")[-1]
        group_name = filename.split(".")[0]

        logger.debug(f"从模板路径 '{template_path}' 提取组名: '{group_name}'")
        return group_name
