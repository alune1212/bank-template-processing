"""
配置加载器模块测试
"""

import json
from typing import Any, Dict

import pytest

from bank_template_processing.config_loader import ConfigError, load_config, validate_config


class TestLoadConfig:
    """测试配置加载功能"""

    def test_load_valid_config(self, tmp_path):
        """测试加载有效配置文件"""
        config_data = {
            "version": "1.0",
            "organization_units": {
                "test_unit": {
                    "template_path": "templates/test.xlsx",
                    "header_row": 1,
                    "start_row": 2,
                    "field_mappings": {"姓名": {"source_column": "name"}},
                    "transformations": {},
                }
            },
        }
        config_file = tmp_path / "valid_config.json"
        config_file.write_text(json.dumps(config_data), encoding="utf-8")

        config = load_config(str(config_file))
        assert config == config_data

    def test_load_nonexistent_file(self):
        """测试加载不存在的文件"""
        with pytest.raises(FileNotFoundError):
            load_config("nonexistent_config.json")

    def test_load_invalid_json(self, tmp_path):
        """测试加载无效的JSON语法"""
        config_file = tmp_path / "invalid.json"
        config_file.write_text("{ invalid json }", encoding="utf-8")

        with pytest.raises(json.JSONDecodeError):
            load_config(str(config_file))


class TestValidateConfig:
    """测试配置验证功能"""

    def test_validate_valid_config(self):
        """测试验证有效配置"""
        config = {
            "version": "1.0",
            "organization_units": {
                "test_unit": {
                    "template_path": "templates/test.xlsx",
                    "header_row": 1,
                    "start_row": 2,
                    "field_mappings": {"姓名": {"source_column": "name"}},
                    "transformations": {},
                }
            },
        }
        validate_config(config)  # 不应抛出异常

    def test_validate_old_validation_rules_keys(self):
        """测试旧键名 type_rules/range_rules 触发错误"""
        config = {
            "version": "1.0",
            "organization_units": {
                "test_unit": {
                    "template_path": "templates/test.xlsx",
                    "header_row": 1,
                    "start_row": 2,
                    "field_mappings": {"姓名": {"source_column": "name"}},
                    "transformations": {},
                    "validation_rules": {
                        "type_rules": {"金额": "numeric"},
                        "range_rules": {"金额": {"min": 0}},
                    },
                }
            },
        }
        with pytest.raises(ConfigError, match="仅支持 data_types/value_ranges"):
            validate_config(config)

    def test_validate_invalid_data_types(self):
        """测试 data_types 非法类型名触发错误"""
        config = {
            "version": "1.0",
            "organization_units": {
                "test_unit": {
                    "template_path": "templates/test.xlsx",
                    "header_row": 1,
                    "start_row": 2,
                    "field_mappings": {"姓名": {"source_column": "name"}},
                    "transformations": {},
                    "validation_rules": {
                        "data_types": {"金额": "unknown_type"},
                    },
                }
            },
        }
        with pytest.raises(ConfigError, match="类型不支持"):
            validate_config(config)

    def test_validate_missing_version(self):
        """测试缺失version字段"""
        config = {
            "organization_units": {
                "test_unit": {
                    "template_path": "templates/test.xlsx",
                    "header_row": 1,
                    "start_row": 2,
                    "field_mappings": {"姓名": {"source_column": "name"}},
                    "transformations": {},
                }
            }
        }
        with pytest.raises(ConfigError, match="缺少必填字段.*version"):
            validate_config(config)

    def test_validate_missing_organization_units(self):
        """测试缺失organization_units字段"""
        config = {"version": "1.0"}
        with pytest.raises(ConfigError, match="缺少必填字段.*organization_units"):
            validate_config(config)

    def test_validate_missing_unit_template_path(self):
        """测试缺失单位的template_path字段"""
        config = {
            "version": "1.0",
            "organization_units": {
                "test_unit": {
                    "header_row": 1,
                    "start_row": 2,
                    "field_mappings": {"姓名": {"source_column": "name"}},
                    "transformations": {},
                }
            },
        }
        with pytest.raises(ConfigError, match="缺少必填字段.*template_path"):
            validate_config(config)

    def test_validate_missing_unit_header_row(self):
        """测试缺失单位的header_row字段"""
        config = {
            "version": "1.0",
            "organization_units": {
                "test_unit": {
                    "template_path": "templates/test.xlsx",
                    "start_row": 2,
                    "field_mappings": {"姓名": {"source_column": "name"}},
                    "transformations": {},
                }
            },
        }
        with pytest.raises(ConfigError, match="缺少必填字段.*header_row"):
            validate_config(config)

    def test_validate_missing_unit_field_mappings(self):
        """测试缺失单位的field_mappings字段"""
        config = {
            "version": "1.0",
            "organization_units": {
                "test_unit": {
                    "template_path": "templates/test.xlsx",
                    "header_row": 1,
                    "start_row": 2,
                    "transformations": {},
                }
            },
        }
        with pytest.raises(ConfigError, match="缺少必填字段.*field_mappings"):
            validate_config(config)

    def test_validate_missing_unit_transformations(self):
        """测试缺失单位的transformations字段"""
        config = {
            "version": "1.0",
            "organization_units": {
                "test_unit": {
                    "template_path": "templates/test.xlsx",
                    "header_row": 1,
                    "start_row": 2,
                    "field_mappings": {"姓名": {"source_column": "name"}},
                }
            },
        }
        with pytest.raises(ConfigError, match="缺少必填字段.*transformations"):
            validate_config(config)

    def test_validate_valid_header_row_zero(self):
        """测试header_row为0（模板无表头，使用列标识符）"""
        config: Dict[str, Any] = {
            "version": "1.0",
            "organization_units": {
                "test_unit": {
                    "template_path": "templates/test.xlsx",
                    "header_row": 0,
                    "start_row": 1,
                    "field_mappings": {"姓名": {"source_column": "name"}},
                    "transformations": {},
                }
            },
        }
        validate_config(config)
        assert config["organization_units"]["test_unit"]["start_row"] == 1

    def test_validate_invalid_header_row_negative(self):
        """测试header_row为负数"""
        config = {
            "version": "1.0",
            "organization_units": {
                "test_unit": {
                    "template_path": "templates/test/test.xlsx",
                    "header_row": -1,
                    "start_row": 0,
                    "field_mappings": {"姓名": {"source_column": "name"}},
                    "transformations": {},
                }
            },
        }
        with pytest.raises(ConfigError, match=r"header_row.*必须大于或等于 0"):
            validate_config(config)

    def test_validate_invalid_start_row_equal_to_header(self):
        """测试start_row等于header_row（必须>header_row）"""
        config = {
            "version": "1.0",
            "organization_units": {
                "test_unit": {
                    "template_path": "templates/test.xlsx",
                    "header_row": 1,
                    "start_row": 1,
                    "field_mappings": {"姓名": {"source_column": "name"}},
                    "transformations": {},
                }
            },
        }
        with pytest.raises(ConfigError, match=r"start_row.*必须大于 header_row"):
            validate_config(config)

    def test_validate_invalid_start_row_less_than_header(self):
        """测试start_row小于header_row"""
        config = {
            "version": "1.0",
            "organization_units": {
                "test_unit": {
                    "template_path": "templates/test.xlsx",
                    "header_row": 5,
                    "start_row": 3,
                    "field_mappings": {"姓名": {"source_column": "name"}},
                    "transformations": {},
                }
            },
        }
        with pytest.raises(ConfigError, match=r"start_row.*必须大于 header_row"):
            validate_config(config)

    def test_validate_invalid_field_mappings_not_dict(self):
        """测试field_mappings不是字典类型"""
        config = {
            "version": "1.0",
            "organization_units": {
                "test_unit": {
                    "template_path": "templates/test.xlsx",
                    "header_row": 1,
                    "start_row": 2,
                    "field_mappings": "invalid",
                    "transformations": {},
                }
            },
        }
        with pytest.raises(ConfigError, match="field_mappings.*必须是字典"):
            validate_config(config)

    def test_validate_field_mappings_old_format(self, caplog):
        """测试field_mappings旧格式（字符串映射）允许通过并记录警告"""
        config = {
            "version": "1.0",
            "organization_units": {
                "test_unit": {
                    "template_path": "templates/test.xlsx",
                    "header_row": 1,
                    "start_row": 2,
                    "field_mappings": {"name": "姓名", "age": "年龄"},
                    "transformations": {},
                }
            },
        }
        validate_config(config)
        assert any("旧格式" in record.message for record in caplog.records)

    def test_validate_field_mappings_invalid_value(self):
        """测试field_mappings值类型不合法"""
        config = {
            "version": "1.0",
            "organization_units": {
                "test_unit": {
                    "template_path": "templates/test.xlsx",
                    "header_row": 1,
                    "start_row": 2,
                    "field_mappings": {"name": ["姓名"]},
                    "transformations": {},
                }
            },
        }
        with pytest.raises(ConfigError, match="field_mappings.*必须是字典或字符串"):
            validate_config(config)

    def test_validate_default_start_row(self):
        """测试start_row默认值（未指定时为header_row+1）"""
        config: Dict[str, Any] = {
            "version": "1.0",
            "organization_units": {
                "test_unit": {
                    "template_path": "templates/test.xlsx",
                    "header_row": 3,
                    "field_mappings": {"姓名": {"source_column": "name"}},
                    "transformations": {},
                }
            },
        }
        validate_config(config)  # 验证不应抛出异常
        # 验证默认值已设置
        assert config["organization_units"]["test_unit"]["start_row"] == 4

    def test_validate_multiple_units(self):
        """测试多个单位的配置验证"""
        config: Dict[str, Any] = {
            "version": "1.0",
            "organization_units": {
                "unit1": {
                    "template_path": "templates/unit1.xlsx",
                    "header_row": 1,
                    "start_row": 2,
                    "field_mappings": {"姓名": {"source_column": "name"}},
                    "transformations": {},
                },
                "unit2": {
                    "template_path": "templates/unit2.xlsx",
                    "header_row": 2,
                    "field_mappings": {"卡号": {"source_column": "card"}},
                    "transformations": {},
                },
            },
        }
        validate_config(config)  # 不应抛出异常
        # 验证unit2的start_row默认值
        assert config["organization_units"]["unit2"]["start_row"] == 3

    def test_validate_reader_options_valid(self):
        """测试reader_options合法配置"""
        config = {
            "version": "1.0",
            "organization_units": {
                "test_unit": {
                    "template_path": "templates/test.xlsx",
                    "header_row": 1,
                    "start_row": 2,
                    "field_mappings": {"姓名": {"source_column": "name"}},
                    "transformations": {},
                    "reader_options": {"data_only": True},
                }
            },
        }
        validate_config(config)

    def test_validate_reader_options_invalid_type(self):
        """测试reader_options类型非法"""
        config = {
            "version": "1.0",
            "organization_units": {
                "test_unit": {
                    "template_path": "templates/test.xlsx",
                    "header_row": 1,
                    "start_row": 2,
                    "field_mappings": {"姓名": {"source_column": "name"}},
                    "transformations": {},
                    "reader_options": "invalid",
                }
            },
        }
        with pytest.raises(ConfigError, match="reader_options 必须是字典"):
            validate_config(config)

    def test_validate_reader_options_invalid_data_only(self):
        """测试reader_options.data_only类型非法"""
        config = {
            "version": "1.0",
            "organization_units": {
                "test_unit": {
                    "template_path": "templates/test.xlsx",
                    "header_row": 1,
                    "start_row": 2,
                    "field_mappings": {"姓名": {"source_column": "name"}},
                    "transformations": {},
                    "reader_options": {"data_only": "yes"},
                }
            },
        }
        with pytest.raises(ConfigError, match="reader_options.data_only 必须是布尔值"):
            validate_config(config)

    def test_validate_empty_organization_units(self):
        """测试空的organization_units"""
        config = {"version": "1.0", "organization_units": {}}
        with pytest.raises(ConfigError, match="organization_units.*不能为空"):
            validate_config(config)


class TestConfigError:
    """测试ConfigError异常类"""

    def test_config_error_message(self):
        """测试ConfigError消息"""
        error = ConfigError("测试错误消息")
        assert str(error) == "测试错误消息"
        assert isinstance(error, Exception)
