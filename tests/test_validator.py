"""
验证器模块测试
"""

import pytest
from datetime import datetime
from bank_template_processing.validator import Validator, ValidationError


class TestValidateRequired:
    """测试必填字段验证"""

    def test_all_required_fields_present(self):
        """所有必填字段存在且非空 → 通过"""
        row = {"name": "张三", "age": 25, "address": "北京市朝阳区"}
        required_fields = ["name", "age", "address"]

        # 应该不抛出异常
        Validator.validate_required(row, required_fields)

    def test_missing_required_field(self):
        """缺失必填字段 → ValidationError"""
        row = {"name": "张三", "age": 25}
        required_fields = ["name", "age", "address"]

        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_required(row, required_fields)

        assert "必填字段 'address' 不存在" in str(exc_info.value)

    def test_required_field_is_none(self):
        """必填字段值为 None → ValidationError"""
        row = {"name": "张三", "age": None, "address": "北京市朝阳区"}
        required_fields = ["name", "age", "address"]

        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_required(row, required_fields)

        assert "必填字段 'age' 的值为 None" in str(exc_info.value)

    def test_required_field_is_empty_string(self):
        """必填字段值为空字符串 → ValidationError"""
        row = {"name": "张三", "age": 25, "address": ""}
        required_fields = ["name", "age", "address"]

        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_required(row, required_fields)

        assert "必填字段 'address' 的值为空字符串" in str(exc_info.value)

    def test_required_field_is_whitespace_only(self):
        """必填字段值为空格字符串 → ValidationError"""
        row = {"name": "张三", "age": 25, "address": "   "}
        required_fields = ["name", "age", "address"]

        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_required(row, required_fields)

        assert "必填字段 'address' 的值为空字符串" in str(exc_info.value)

    def test_required_field_is_empty_list(self):
        """必填字段值为空列表列表 → ValidationError"""
        row = {"name": "张三", "age": 25, "tags": []}
        required_fields = ["name", "age", "tags"]

        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_required(row, required_fields)

        assert "必填字段 'tags' 的值为空 list" in str(exc_info.value)

    def test_required_field_is_empty_dict(self):
        """必填字段值为空字典 → ValidationError"""
        row = {"name": "张三", "age": 25, "metadata": {}}
        required_fields = ["name", "age", "metadata"]

        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_required(row, required_fields)

        assert "必填字段 'metadata' 的值为空 dict" in str(exc_info.value)


class TestValidateDataTypes:
    """测试数据类型验证"""

    def test_correct_types(self):
        """所有字段类型正确 → 通过"""
        row = {
            "name": "张三",
            "age": 25,
            "score": 95.5,
            "is_active": True,
            "tags": ["tag1", "tag2"],
            "metadata": {"key": "value"},
            "created_at": datetime(2024, 1, 1),
        }
        type_rules = {
            "name": "string",
            "age": "int",
            "score": "float",
            "is_active": "boolean",
            "tags": "list",
            "metadata": "dict",
            "created_at": "datetime",
        }

        # 应该不抛出异常
        Validator.validate_data_types(row, type_rules)

    def test_wrong_type_string_instead_of_int(self):
        """字段类型错误：字符串替代整数 → ValidationError"""
        row = {"name": "张三", "age": "25a"}
        type_rules = {"name": "string", "age": "int"}

        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_data_types(row, type_rules)

        assert "字段 'age' 的值 25a 不是有效数值" in str(exc_info.value)

    def test_wrong_type_int_instead_of_float(self):
        """字段类型错误：整数替代浮点数 → ValidationError"""
        row = {"score": 95}
        type_rules = {"score": "float"}

        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_data_types(row, type_rules)

        assert "字段 'score' 的类型应为 float，实际为 int" in str(exc_info.value)

    def test_wrong_type_dict_instead_of_datetime(self):
        """字段类型错误：字典替代datetime → ValidationError"""
        row = {"created_at": {"year": 2024}}
        type_rules = {"created_at": "datetime"}

        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_data_types(row, type_rules)

        assert "字段 'created_at' 的类型应为 datetime，实际为 dict" in str(exc_info.value)

    def test_field_not_in_row_skip_validation(self):
        """字段不存在 → 跳过验证（不抛出异常）"""
        row = {"name": "张三"}
        type_rules = {
            "name": "string",
            "age": "int",  # age 不存在，跳过验证
        }

        # 应该不抛出异常
        Validator.validate_data_types(row, type_rules)

    def test_numeric_string_value(self):
        """数值字符串通过 numeric 校验"""
        row = {"amount": "123.45"}
        type_rules = {"amount": "numeric"}
        Validator.validate_data_types(row, type_rules)

    def test_date_string_value(self):
        """日期字符串通过 date 校验"""
        row = {"date": "2024-01-05"}
        type_rules = {"date": "date"}
        Validator.validate_data_types(row, type_rules)

    def test_numeric_string_invalid(self):
        """无效数值字符串 → ValidationError"""
        row = {"amount": "abc"}
        type_rules = {"amount": "numeric"}
        with pytest.raises(ValidationError, match="不是有效数值"):
            Validator.validate_data_types(row, type_rules)

    def test_integer_string_value(self):
        """整数数字字符串通过 integer 校验"""
        row = {"card": "6228481329039402872"}
        type_rules = {"card": "integer"}
        Validator.validate_data_types(row, type_rules)

    def test_type_validation_empty_string_skip(self):
        """空字符串应跳过类型验证"""
        row = {"card": ""}
        type_rules = {"card": "integer"}
        Validator.validate_data_types(row, type_rules)


class TestValidateValueRanges:
    """测试值范围验证"""

    def test_value_in_range(self):
        """值在范围内 → 通过"""
        row = {"age": 25, "score": 85.5, "name": "张三", "status": "active"}
        range_rules = {
            "age": {"min": 18, "max": 60},
            "score": {"min": 0, "max": 100},
            "name": {"min_length": 2, "max_length": 10},
            "status": {"allowed_values": ["active", "inactive"]},
        }

        # 应该不抛出异常
        Validator.validate_value_ranges(row, range_rules)

    def test_value_less_than_min(self):
        """值小于最小值 → ValidationError"""
        row = {"age": 15}
        range_rules = {"age": {"min": 18, "max": 60}}

        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_value_ranges(row, range_rules)

        assert "字段 'age' 的值 15 小于最小值 18" in str(exc_info.value)

    def test_value_greater_than_max(self):
        """值大于最大值 → ValidationError"""
        row = {"age": 65}
        range_rules = {"age": {"min": 18, "max": 60}}

        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_value_ranges(row, range_rules)

        assert "字段 'age' 的值 65 大于最大值 60" in str(exc_info.value)

    def test_length_less_than_min_length(self):
        """长度小于最小长度 → ValidationError"""
        row = {"name": "张"}
        range_rules = {"name": {"min_length": 2, "max_length": 10}}

        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_value_ranges(row, range_rules)

        assert "字段 'name' 的长度 1 小于最小长度 2" in str(exc_info.value)

    def test_length_greater_than_max_length(self):
        """长度大于最大长度 → ValidationError"""
        row = {"name": "张三李四王五六七八九十十一"}
        range_rules = {"name": {"min_length": 2, "max_length": 10}}

        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_value_ranges(row, range_rules)

        assert "字段 'name' 的长度 13 大于最大长度 10" in str(exc_info.value)

    def test_value_not_in_allowed_values(self):
        """值不在允许的值列表中 → ValidationError"""
        row = {"status": "pending"}
        range_rules = {"status": {"allowed_values": ["active", "inactive"]}}

        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_value_ranges(row, range_rules)

        assert "字段 'status' 的值 pending 不在允许的值列表中" in str(exc_info.value)

    def test_list_length_validation(self):
        """列表长度验证 → 通过"""
        row = {"tags": ["tag1", "tag2", "tag3"]}
        range_rules = {"tags": {"min_length": 1, "max_length": 5}}

        # 应该不抛出异常
        Validator.validate_value_ranges(row, range_rules)

    def test_dict_length_validation(self):
        """字典长度验证 → 通过"""
        row = {"metadata": {"key1": "value1", "key2": "value2"}}
        range_rules = {"metadata": {"min_length": 1, "max_length": 5}}

        # 应该不抛出异常
        Validator.validate_value_ranges(row, range_rules)

    def test_field_not_in_row_skip_validation(self):
        """字段不存在 → 跳过验证（不抛出异常）"""
        row = {"age": 25}
        range_rules = {
            "age": {"min": 18, "max": 60},
            "score": {"min": 0, "max": 100},  # score 不存在，跳过验证
        }

        # 应该不抛出异常
        Validator.validate_value_ranges(row, range_rules)

    def test_value_none_skip(self):
        """None 值应跳过范围验证"""
        row = {"age": None}
        range_rules = {"age": {"min": 18, "max": 60}}
        Validator.validate_value_ranges(row, range_rules)

    def test_value_empty_string_skip(self):
        """空字符串应跳过范围验证"""
        row = {"age": ""}
        range_rules = {"age": {"min": 18, "max": 60}}
        Validator.validate_value_ranges(row, range_rules)


class TestValidationErrorValidation:
    """测试 ValidationError 异常类"""

    def test_validation_error_message(self):
        """验证异常消息正确"""
        message = "字段 'name' 不能为空"
        error = ValidationError(message)

        assert str(error) == message
        assert error.message == message
