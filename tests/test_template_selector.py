"""
模板选择器模块测试
"""

import pytest
from template_selector import TemplateSelector, ValidationError


class TestIsEnabled:
    """测试 is_enabled() 方法"""

    def test_enabled_true(self):
        """enabled=true 返回 True"""
        config = {
            "template_selector": {
                "enabled": True,
                "default_bank": "农业银行",
                "default_template": "templates/农业银行.xlsx",
                "special_template": "templates/农业银行-特殊.xlsx",
            }
        }
        selector = TemplateSelector(config)

        assert selector.is_enabled() is True

    def test_enabled_false(self):
        """enabled=false 返回 False"""
        config = {
            "template_selector": {
                "enabled": False,
                "default_bank": "农业银行",
                "default_template": "templates/农业银行.xlsx",
                "special_template": "templates/农业银行-特殊.xlsx",
            }
        }
        selector = TemplateSelector(config)

        assert selector.is_enabled() is False

    def test_enabled_config_not_exist(self):
        """template_selector 配置不存在返回 False"""
        config = {}
        selector = TemplateSelector(config)

        assert selector.is_enabled() is False

    def test_enabled_key_not_exist(self):
        """enabled key 不存在返回 False"""
        config = {
            "template_selector": {
                "default_bank": "农业银行",
                "default_template": "templates/农业银行.xlsx",
                "special_template": "templates/农业银行-特殊.xlsx",
            }
        }
        selector = TemplateSelector(config)

        assert selector.is_enabled() is False


class TestGroupData:
    """测试 group_data() 方法"""

    def test_mixed_banks(self):
        """混合银行数据，返回两个组"""
        config = {
            "template_selector": {
                "enabled": True,
                "default_bank": "农业银行",
                "default_template": "templates/农业银行.xlsx",
                "special_template": "templates/农业银行-特殊.xlsx",
                "default_group_name": "农业银行",
                "special_group_name": "农业银行-特殊",
            }
        }
        selector = TemplateSelector(config)

        data = [
            {"开户银行": "农业银行", "姓名": "张三", "金额": 1000},
            {"开户银行": "工商银行", "姓名": "李四", "金额": 2000},
            {"开户银行": "农业银行", "姓名": "王五", "金额": 3000},
            {"开户银行": "建设银行", "姓名": "赵六", "金额": 4000},
        ]

        result = selector.group_data(data, default_bank="农业银行")

        assert "default" in result
        assert "special" in result

        assert len(result["default"]["data"]) == 2
        assert result["default"]["data"][0]["姓名"] == "张三"
        assert result["default"]["data"][1]["姓名"] == "王五"
        assert result["default"]["template"] == "templates/农业银行.xlsx"
        assert result["default"]["group_name"] == "农业银行"

        assert len(result["special"]["data"]) == 2
        assert result["special"]["data"][0]["姓名"] == "李四"
        assert result["special"]["data"][1]["姓名"] == "赵六"
        assert result["special"]["template"] == "templates/农业银行-特殊.xlsx"
        assert result["special"]["group_name"] == "农业银行-特殊"

    def test_all_default_bank(self):
        """所有数据都是默认银行，只有默认组"""
        config = {
            "template_selector": {
                "enabled": True,
                "default_bank": "农业银行",
                "default_template": "templates/农业银行.xlsx",
                "special_template": "templates/农业银行-特殊.xlsx",
            }
        }
        selector = TemplateSelector(config)

        data = [
            {"开户银行": "农业银行", "姓名": "张三", "金额": 1000},
            {"开户银行": "农业银行", "姓名": "李四", "金额": 2000},
            {"开户银行": "农业银行", "姓名": "王五", "金额": 3000},
        ]

        result = selector.group_data(data, default_bank="农业银行")

        assert "default" in result
        assert "special" in result

        # 默认组应该有 3 条数据
        assert len(result["default"]["data"]) == 3

        # 特殊组应该为空
        assert len(result["special"]["data"]) == 0

    def test_all_special_bank(self):
        """所有数据都不是默认银行，只有特殊组"""
        config = {
            "template_selector": {
                "enabled": True,
                "default_bank": "农业银行",
                "default_template": "templates/农业银行.xlsx",
                "special_template": "templates/农业银行-特殊.xlsx",
            }
        }
        selector = TemplateSelector(config)

        data = [
            {"开户银行": "工商银行", "姓名": "张三", "金额": 1000},
            {"开户银行": "建设银行", "姓名": "李四", "金额": 2000},
            {"开户银行": "交通银行", "姓名": "王五", "金额": 3000},
        ]

        result = selector.group_data(data, default_bank="农业银行")

        assert "default" in result
        assert "special" in result

        # 默认组应该为空
        assert len(result["default"]["data"]) == 0

        # 特殊组应该有 3 条数据
        assert len(result["special"]["data"]) == 3

    def test_bank_column_not_exist(self):
        """开户银行列不存在，抛出 ValidationError"""
        config = {
            "template_selector": {
                "enabled": True,
                "default_bank": "农业银行",
                "default_template": "templates/农业银行.xlsx",
                "special_template": "templates/农业银行-特殊.xlsx",
            }
        }
        selector = TemplateSelector(config)

        data = [
            {"姓名": "张三", "金额": 1000},
            {"姓名": "李四", "金额": 2000},
        ]

        with pytest.raises(ValidationError) as exc_info:
            selector.group_data(data, default_bank="农业银行")

        assert "缺少'开户银行'列" in str(exc_info.value)

    def test_bank_column_empty_string(self):
        """开户银行为空字符串，抛出 ValidationError"""
        config = {
            "template_selector": {
                "enabled": True,
                "default_bank": "农业银行",
                "default_template": "templates/农业银行.xlsx",
                "special_template": "templates/农业银行-特殊.xlsx",
            }
        }
        selector = TemplateSelector(config)

        data = [
            {"开户银行": "农业银行", "姓名": "张三", "金额": 1000},
            {"开户银行": "", "姓名": "李四", "金额": 2000},
            {"开户银行": "工商银行", "姓名": "王五", "金额": 3000},
        ]

        with pytest.raises(ValidationError) as exc_info:
            selector.group_data(data, default_bank="农业银行")

        assert "第2行的'开户银行'字段为空" in str(exc_info.value)

    def test_bank_column_none(self):
        """开户银行为 None，抛出 ValidationError"""
        config = {
            "template_selector": {
                "enabled": True,
                "default_bank": "农业银行",
                "default_template": "templates/农业银行.xlsx",
                "special_template": "templates/农业银行-特殊.xlsx",
            }
        }
        selector = TemplateSelector(config)

        data = [
            {"开户银行": "农业银行", "姓名": "张三", "金额": 1000},
            {"开户银行": None, "姓名": "李四", "金额": 2000},
        ]

        with pytest.raises(ValidationError) as exc_info:
            selector.group_data(data, default_bank="农业银行")

        assert "第2行的'开户银行'字段为空" in str(exc_info.value)

    def test_single_row(self):
        """单行数据"""
        config = {
            "template_selector": {
                "enabled": True,
                "default_bank": "农业银行",
                "default_template": "templates/农业银行.xlsx",
                "special_template": "templates/农业银行-特殊.xlsx",
            }
        }
        selector = TemplateSelector(config)

        data = [{"开户银行": "农业银行", "姓名": "张三", "金额": 1000}]

        result = selector.group_data(data, default_bank="农业银行")

        assert len(result["default"]["data"]) == 1
        assert len(result["special"]["data"]) == 0

    def test_empty_data(self):
        """空数据列表"""
        config = {
            "template_selector": {
                "enabled": True,
                "default_bank": "农业银行",
                "default_template": "templates/农业银行.xlsx",
                "special_template": "templates/农业银行-特殊.xlsx",
            }
        }
        selector = TemplateSelector(config)

        data = []

        result = selector.group_data(data, default_bank="农业银行")

        assert len(result["default"]["data"]) == 0
        assert len(result["special"]["data"]) == 0

    def test_multiple_special_banks_all_in_special_group(self):
        """多个不同银行都归入特殊组"""
        config = {
            "template_selector": {
                "enabled": True,
                "default_bank": "农业银行",
                "default_template": "templates/农业银行.xlsx",
                "special_template": "templates/农业银行-特殊.xlsx",
            }
        }
        selector = TemplateSelector(config)

        data = [
            {"开户银行": "工商银行", "姓名": "张三", "金额": 1000},
            {"开户银行": "建设银行", "姓名": "李四", "金额": 2000},
            {"开户银行": "交通银行", "姓名": "王五", "金额": 3000},
            {"开户银行": "招商银行", "姓名": "赵六", "金额": 4000},
        ]

        result = selector.group_data(data, default_bank="农业银行")

        # 所有数据都应该在特殊组
        assert len(result["default"]["data"]) == 0
        assert len(result["special"]["data"]) == 4

        # 验证所有数据都在特殊组
        bank_names = [row["开户银行"] for row in result["special"]["data"]]
        assert "工商银行" in bank_names
        assert "建设银行" in bank_names
        assert "交通银行" in bank_names
        assert "招商银行" in bank_names

    def test_custom_bank_column(self):
        """使用自定义银行列名"""
        config = {
            "template_selector": {
                "enabled": True,
                "default_bank": "农业银行",
                "default_template": "templates/农业银行.xlsx",
                "special_template": "templates/农业银行-特殊.xlsx",
            }
        }
        selector = TemplateSelector(config)

        data = [
            {"银行名称": "农业银行", "姓名": "张三", "金额": 1000},
            {"银行名称": "工商银行", "姓名": "李四", "金额": 2000},
        ]

        result = selector.group_data(
            data, default_bank="农业银行", bank_column="银行名称"
        )

        assert len(result["default"]["data"]) == 1
        assert len(result["special"]["data"]) == 1
