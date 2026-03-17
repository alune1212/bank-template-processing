"""config_loader 边界与失败路径补充测试。"""

from __future__ import annotations

from typing import TypedDict

import pytest

from bank_template_processing.config_loader import (
    ConfigError,
    _validate_clear_rows,
    _validate_legacy_unit_config,
    _validate_reader_options,
    _validate_rule_group_config,
    _validate_template_selector,
    _validate_validation_rules,
    get_unit_config,
    validate_config,
)


class UnitConfigSample(TypedDict):
    template_path: object
    header_row: object
    start_row: object
    field_mappings: object
    transformations: object


def _make_base_unit_config() -> UnitConfigSample:
    return {
        "template_path": "a.xlsx",
        "header_row": 1,
        "start_row": 2,
        "field_mappings": {"姓名": {"source_column": "姓名"}},
        "transformations": {},
    }


def test_validate_config_organization_units_must_be_dict():
    with pytest.raises(ConfigError, match="organization_units 必须是字典"):
        validate_config({"version": "2.0", "organization_units": []})


def test_get_unit_config_multi_group_default_and_explicit_group():
    config = {
        "organization_units": {
            "单位A": {
                "default": {"template_path": "a.xlsx"},
                "crossbank": {"template_path": "b.xlsx"},
            }
        }
    }

    assert get_unit_config(config, "单位A") == {"template_path": "a.xlsx"}
    assert get_unit_config(config, "单位A", "crossbank") == {"template_path": "b.xlsx"}

    with pytest.raises(ConfigError, match="未找到规则组 'not-exists'"):
        get_unit_config(config, "单位A", "not-exists")


def test_get_unit_config_legacy_with_template_key_warns(caplog):
    config = {
        "organization_units": {
            "单位A": {
                "template_path": "a.xlsx",
                "header_row": 1,
                "field_mappings": {},
                "transformations": {},
            }
        }
    }
    resolved = get_unit_config(config, "单位A", "default")
    assert resolved["template_path"] == "a.xlsx"
    assert "使用旧配置结构，忽略 template_key" in caplog.text


def test_get_unit_config_missing_unit_raises():
    with pytest.raises(ConfigError, match="未找到单位配置"):
        get_unit_config({"organization_units": {}}, "不存在单位")


def test_validate_validation_rules_error_paths():
    with pytest.raises(ConfigError, match="validation_rules 必须是字典"):
        _validate_validation_rules("单位A", "bad")  # type: ignore[arg-type]

    with pytest.raises(ConfigError, match="required_fields 必须是字符串列表"):
        _validate_validation_rules("单位A", {"required_fields": [1, 2]})

    with pytest.raises(ConfigError, match="data_types 必须是字典"):
        _validate_validation_rules("单位A", {"data_types": []})

    with pytest.raises(ConfigError, match="必须是字符串类型名"):
        _validate_validation_rules("单位A", {"data_types": {"金额": 1}})

    with pytest.raises(ConfigError, match="value_ranges 必须是字典"):
        _validate_validation_rules("单位A", {"value_ranges": []})

    with pytest.raises(ConfigError, match="value_ranges 中 '金额' 必须是字典"):
        _validate_validation_rules("单位A", {"value_ranges": {"金额": 1}})

    with pytest.raises(ConfigError, match="min_length 必须是 >= 0 的整数"):
        _validate_validation_rules("单位A", {"value_ranges": {"金额": {"min_length": -1}}})

    with pytest.raises(ConfigError, match="min.*无效"):
        _validate_validation_rules("单位A", {"value_ranges": {"金额": {"min": "abc"}}})

    with pytest.raises(ConfigError, match="min/max 必须同为数值或同为日期"):
        _validate_validation_rules(
            "单位A",
            {"value_ranges": {"金额": {"min": 1, "max": "2024-01-01"}}},
        )


def test_validate_legacy_unit_config_error_paths():
    base = _make_base_unit_config()

    cfg = {**base, "template_path": 123}
    with pytest.raises(ConfigError, match="template_path 必须是字符串"):
        _validate_legacy_unit_config("单位A", cfg)

    cfg = {**base, "header_row": "1"}
    with pytest.raises(ConfigError, match="header_row 必须是整数"):
        _validate_legacy_unit_config("单位A", cfg)

    cfg = {**base, "start_row": "2"}
    with pytest.raises(ConfigError, match="start_row 必须是整数"):
        _validate_legacy_unit_config("单位A", cfg)

    cfg = {**base, "field_mappings": {"姓名": {"target_column": "A"}}}
    with pytest.raises(ConfigError, match="缺少 source_column"):
        _validate_legacy_unit_config("单位A", cfg)

    cfg = {**base, "transformations": []}
    with pytest.raises(ConfigError, match="transformations 必须是字典"):
        _validate_legacy_unit_config("单位A", cfg)


def test_validate_rule_group_config_error_paths_and_default_start_row(caplog):
    with pytest.raises(ConfigError, match="缺少必填字段"):
        _validate_rule_group_config("单位A", "default", {"header_row": 1, "field_mappings": {}, "transformations": {}})

    base = _make_base_unit_config()

    with pytest.raises(ConfigError, match="template_path 必须须是字符串"):
        _validate_rule_group_config("单位A", "default", {**base, "template_path": 123})

    with pytest.raises(ConfigError, match="header_row 必须须是整数"):
        _validate_rule_group_config("单位A", "default", {**base, "header_row": "1"})

    with pytest.raises(ConfigError, match="header_row 必须须大于或等于 0"):
        _validate_rule_group_config("单位A", "default", {**base, "header_row": -1})

    with pytest.raises(ConfigError, match="start_row 必须须是整数"):
        _validate_rule_group_config("单位A", "default", {**base, "start_row": "2"})

    with pytest.raises(ConfigError, match="start_row .*必须大于 header_row"):
        _validate_rule_group_config("单位A", "default", {**base, "start_row": 1})

    cfg = {
        "template_path": "a.xlsx",
        "header_row": 2,
        "field_mappings": {"姓名": "A"},
        "transformations": {},
    }
    _validate_rule_group_config("单位A", "default", cfg)
    assert cfg["start_row"] == 3
    assert "使用旧格式，建议迁移" in caplog.text

    with pytest.raises(ConfigError, match="field_mappings 必须须是字典"):
        _validate_rule_group_config("单位A", "default", {**base, "field_mappings": []})

    with pytest.raises(ConfigError, match="缺少 source_column"):
        _validate_rule_group_config(
            "单位A",
            "default",
            {**base, "field_mappings": {"姓名": {"target_column": "A"}}},
        )

    with pytest.raises(ConfigError, match="配置必须是字典或字符串"):
        _validate_rule_group_config("单位A", "default", {**base, "field_mappings": {"姓名": []}})

    with pytest.raises(ConfigError, match="transformations 必须须是字典"):
        _validate_rule_group_config("单位A", "default", {**base, "transformations": []})


def test_validate_template_selector_error_paths():
    with pytest.raises(ConfigError, match="template_selector 必须是字典"):
        _validate_template_selector("单位A", [])

    with pytest.raises(ConfigError, match="template_selector.enabled 必须是布尔值"):
        _validate_template_selector("单位A", {"enabled": "yes"})

    with pytest.raises(ConfigError, match="enabled=true 时必须配置 default_bank"):
        _validate_template_selector("单位A", {"enabled": True})

    with pytest.raises(ConfigError, match="template_selector.default_bank 必须是非空字符串"):
        _validate_template_selector("单位A", {"enabled": True, "default_bank": ""})

    with pytest.raises(ConfigError, match="template_selector.special_template 必须是非空字符串"):
        _validate_template_selector("单位A", {"special_template": []})


def test_validate_config_rejects_invalid_template_selector():
    with pytest.raises(ConfigError, match="template_selector.bank_column 必须是非空字符串"):
        validate_config(
            {
                "version": "2.0",
                "organization_units": {
                    "单位A": {
                        "template_selector": {
                            "enabled": True,
                            "default_bank": "农业银行",
                            "bank_column": 123,
                        },
                        "default": {
                            "template_path": "a.xlsx",
                            "header_row": 1,
                            "field_mappings": {},
                            "transformations": {},
                        },
                        "crossbank": {
                            "template_path": "b.xlsx",
                            "header_row": 1,
                            "field_mappings": {},
                            "transformations": {},
                        },
                    }
                },
            }
        )


def test_validate_config_requires_crossbank_when_template_selector_enabled():
    with pytest.raises(ConfigError, match="启用 template_selector 时必须配置规则组 'crossbank'"):
        validate_config(
            {
                "version": "2.0",
                "organization_units": {
                    "单位A": {
                        "template_selector": {
                            "enabled": True,
                            "default_bank": "农业银行",
                            "bank_column": "银行",
                        },
                        "default": {
                            "template_path": "a.xlsx",
                            "header_row": 1,
                            "field_mappings": {},
                            "transformations": {},
                        },
                    }
                },
            }
        )


def test_validate_reader_options_error_paths():
    with pytest.raises(ConfigError, match="规则组 'default' 的 reader_options 必须是字典"):
        _validate_reader_options("单位A", {"reader_options": []}, rule_name="default")

    with pytest.raises(ConfigError, match="reader_options.data_only 必须是布尔值"):
        _validate_reader_options("单位A", {"reader_options": {"data_only": "yes"}}, rule_name="default")

    with pytest.raises(ConfigError, match="reader_options.header_row 必须是 >= 1 的整数"):
        _validate_reader_options("单位A", {"reader_options": {"header_row": 0}}, rule_name="default")


def test_validate_clear_rows_error_paths_with_rule_name():
    with pytest.raises(ConfigError, match="规则组 'default' 的 clear_rows 必须是字典"):
        _validate_clear_rows("单位A", [], rule_name="default")  # type: ignore[arg-type]

    with pytest.raises(ConfigError, match="必须包含 end_row 或 data_end_row"):
        _validate_clear_rows("单位A", {}, rule_name="default")

    with pytest.raises(ConfigError, match="clear_rows.end_row 必须是 >= 1 的整数"):
        _validate_clear_rows("单位A", {"end_row": 0}, rule_name="default")

    with pytest.raises(ConfigError, match="clear_rows.start_row 必须是 >= 1 的整数"):
        _validate_clear_rows("单位A", {"end_row": 10, "start_row": 0}, rule_name="default")

    with pytest.raises(ConfigError, match="clear_rows.start_row 不能大于 end_row"):
        _validate_clear_rows("单位A", {"end_row": 10, "start_row": 11}, rule_name="default")
