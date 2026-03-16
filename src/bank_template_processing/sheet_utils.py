"""表格读写共享工具。"""

from __future__ import annotations

import logging
from typing import Any, Sequence

try:
    import xlrd
except ImportError:
    xlrd = None  # type: ignore


logger = logging.getLogger(__name__)


def encode_csv_text_value(value: Any) -> str:
    """将值编码为 Excel 可识别的 CSV 文本表达式。"""
    if value is None:
        return ""

    normalized = str(value)
    if normalized == "":
        return ""

    escaped = normalized.replace('"', '""')
    return f'="{escaped}"'


def decode_csv_text_value(value: Any) -> Any:
    """还原由 encode_csv_text_value 生成的文本表达式。"""
    if not isinstance(value, str):
        return value

    if len(value) >= 3 and value.startswith('="') and value.endswith('"'):
        inner = value[2:-1]
        return inner.replace('""', '"')
    return value


def is_empty_value(value: Any) -> bool:
    """判断值是否为空。"""
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    return False


def get_cell_value(row_values: Sequence[Any], column_index: int) -> Any:
    """按 1-based 列索引读取行值。"""
    if column_index < 1:
        return None
    position = column_index - 1
    if position >= len(row_values):
        return None
    return row_values[position]


def extract_headers_from_values(header_values: Sequence[Any]) -> dict[str, int]:
    """从一行表头值中提取列名映射。"""
    headers: dict[str, int] = {}
    for col_idx, value in enumerate(header_values, start=1):
        if is_empty_value(value):
            continue
        headers[str(value).strip()] = col_idx
    return headers


def extract_headers(rows: Sequence[Sequence[Any]], header_row: int) -> dict[str, int]:
    """从二维行数据中提取表头。"""
    if not isinstance(header_row, int) or header_row < 0:
        raise ValueError(f"header_row 配置无效: {header_row}")
    if header_row == 0:
        return {}
    if header_row > len(rows):
        raise ValueError(f"header_row 超出文件行数: {header_row}")
    return extract_headers_from_values(rows[header_row - 1])


def column_letter_to_index(column: str) -> int:
    """将 Excel 列字母转换为 1-based 索引。"""
    normalized = column.upper()
    index = 0
    for char in normalized:
        index = index * 26 + (ord(char) - ord("A") + 1)
    return index


def resolve_column_index(
    column_spec: Any,
    headers: dict[str, int] | None = None,
    max_columns: int | None = None,
    strict_bounds: bool = False,
) -> int:
    """解析列标识为 1-based 列索引。"""
    if headers and isinstance(column_spec, str) and column_spec in headers:
        col_idx = headers[column_spec]
        if strict_bounds and max_columns is not None and col_idx > max_columns:
            raise ValueError(f"列名 '{column_spec}' 对应的索引 {col_idx} 超出最大列数 {max_columns}")
        return col_idx

    if isinstance(column_spec, int):
        if column_spec < 1:
            raise ValueError(f"列索引必须 >= 1，当前值: {column_spec}")
        if strict_bounds and max_columns is not None and column_spec > max_columns:
            raise ValueError(f"列索引 {column_spec} 超出最大列数 {max_columns}")
        return column_spec

    if isinstance(column_spec, str):
        if column_spec.isdigit():
            idx = int(column_spec)
            if idx < 1:
                raise ValueError(f"列索引必须 >= 1，当前值: {column_spec}")
            if strict_bounds and max_columns is not None and idx > max_columns:
                raise ValueError(f"列索引 {idx} 超出最大列数 {max_columns}")
            return idx

        if column_spec.isalpha() and all(char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" for char in column_spec.upper()):
            col_idx = column_letter_to_index(column_spec)
            if strict_bounds and max_columns is not None and col_idx > max_columns:
                raise ValueError(f"Excel列标识 '{column_spec}' 对应的索引 {col_idx} 超出最大列数 {max_columns}")
            return col_idx

    raise ValueError(f"无法解析列标识: {column_spec} (支持的格式: 列名、Excel列标识A-Z、数字索引)")


def resolve_column_index_by_mode(
    column_spec: Any,
    headers: dict[str, int] | None,
    max_columns: int | None,
    mapping_mode: str,
    logger_instance: logging.Logger | None = None,
) -> int:
    """按映射模式解析列索引。"""
    active_logger = logger_instance or logger
    if mapping_mode == "column_index":
        try:
            return resolve_column_index(column_spec, headers=None, max_columns=max_columns)
        except ValueError as exc:
            if headers:
                active_logger.warning(f"column_index模式解析失败，回退按表头解析: {exc}")
                return resolve_column_index(column_spec, headers=headers, max_columns=max_columns)
            raise

    return resolve_column_index(column_spec, headers=headers, max_columns=max_columns, strict_bounds=True)


def convert_xls_cell(cell: Any, datemode: int) -> Any:
    """将 .xls 单元格值转换为更合适的 Python 类型。"""
    try:
        cell_type = cell.ctype
    except Exception:
        return cell.value

    empty_types = [getattr(xlrd, "XL_CELL_EMPTY", -1), getattr(xlrd, "XL_CELL_BLANK", -1)]
    if cell_type in empty_types:
        return None

    if cell_type == getattr(xlrd, "XL_CELL_DATE", -1):
        try:
            return xlrd.xldate_as_datetime(cell.value, datemode)
        except Exception:
            return cell.value

    if cell_type == getattr(xlrd, "XL_CELL_NUMBER", -1):
        try:
            if float(cell.value).is_integer():
                return int(cell.value)
        except Exception:
            pass
        return cell.value

    if cell_type == getattr(xlrd, "XL_CELL_BOOLEAN", -1):
        return bool(cell.value)

    return cell.value
