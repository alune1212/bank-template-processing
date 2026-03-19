"""测试中复用的配置工厂。"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping


def make_field_mapping(
    *,
    source_column: str = "name",
    target_column: str | None = None,
    transform: str | None = None,
) -> dict[str, str]:
    mapping = {"source_column": source_column}
    if target_column is not None:
        mapping["target_column"] = target_column
    if transform is not None:
        mapping["transform"] = transform
    return mapping


def make_basic_unit_config(
    *,
    template_path: str = "templates/test.xlsx",
    header_row: int = 1,
    start_row: int = 2,
    field_mappings: object | None = None,
    transformations: object | None = None,
    **extra: Any,
) -> dict[str, Any]:
    config: dict[str, Any] = {
        "template_path": template_path,
        "header_row": header_row,
        "start_row": start_row,
        "field_mappings": deepcopy(field_mappings) if field_mappings is not None else {"姓名": make_field_mapping()},
        "transformations": deepcopy(transformations) if transformations is not None else {},
    }
    config.update(deepcopy(extra))
    return config


def make_multi_group_unit_config(
    rule_groups: Mapping[str, Mapping[str, object]],
    **extra: Any,
) -> dict[str, Any]:
    unit_config = {group_name: deepcopy(group_config) for group_name, group_config in rule_groups.items()}
    unit_config.update(deepcopy(extra))
    return unit_config


def make_config(
    *,
    unit_config: Mapping[str, object] | None = None,
    unit_name: str = "test_unit",
    organization_units: Mapping[str, object] | None = None,
    version: str = "1.0",
) -> dict[str, Any]:
    if organization_units is None:
        resolved_units: dict[str, object] = {}
        if unit_config is not None:
            resolved_units[unit_name] = deepcopy(unit_config)
    else:
        resolved_units = deepcopy(dict(organization_units))

    return {
        "version": version,
        "organization_units": resolved_units,
    }
