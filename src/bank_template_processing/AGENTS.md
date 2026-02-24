# PACKAGE KNOWLEDGE BASE

**Generated:** 2026-02-24  
**Commit:** f728266  
**Branch:** main  
**Scope:** `src/bank_template_processing/` 核心业务代码

## OVERVIEW
负责 CLI 主流程、配置校验、Excel 多格式读写、数据转换与验证、按银行动态模板分组。当前已支持新旧配置兼容，并强化了 `reader_options`、`clear_rows` 与输出文件名统计变量能力。

## CURRENT SNAPSHOT
- 模块规模：9 个 `.py` 文件。
- 大文件：`excel_writer.py` 843 行、`main.py` 593 行、`validator.py` 460 行、`config_loader.py` 454 行。
- 入口：
  - `__main__.py`：`python -m bank_template_processing`
  - `main.py:main`：命令行脚本入口（`bank-process`）
- 配置兼容：
  - 旧结构（单位下直接配置）
  - 新结构（单位下 `default/crossbank` 规则组）

## STRUCTURE
```text
src/bank_template_processing/
├── __init__.py           # 包标识
├── __main__.py           # 模块入口
├── main.py               # 参数解析、主流程、输出命名、分组处理
├── config_loader.py      # 配置加载与结构校验
├── excel_reader.py       # 读取 .xlsx/.csv/.xls（含 data_only/header_row）
├── excel_writer.py       # 写入 .xlsx/.csv/.xls（含 clear_rows/映射模式）
├── transformer.py        # 日期/金额/卡号转换 + Luhn
├── validator.py          # required/data_types/value_ranges 校验
└── template_selector.py  # 银行名归一化与 default/special 分组
```

## WHERE TO LOOK
| 任务 | 模块 | 关键点 |
|------|------|------|
| CLI 主链路 | `main.py` | `parse_args`、`validate_month`、`main`、`process_group` |
| 输出文件名 | `main.py` | `generate_output_filename` + `_calculate_stats`（人数/金额） |
| 配置校验 | `config_loader.py` | 禁止旧键 `type_rules/range_rules`，支持 `data_types/value_ranges` |
| 读取策略 | `excel_reader.py` | `row_filter.exclude_keywords`、`reader_options.data_only/header_row` |
| 写入策略 | `excel_writer.py` | `clear_rows`、`column_name/column_index`、三种格式写入 |
| 银行分组 | `template_selector.py` | 全角转半角、空白归一化、组名配置 |
| 转换规则 | `transformer.py` | 日期解析、金额舍入、卡号清洗与 Luhn |
| 值校验 | `validator.py` | 类型/区间/枚举归一化比较 |

## CONVENTIONS
- 保持 `src` 布局，导入使用包路径或相对导入，不做根目录平铺。
- Python 版本按 `>=3.13`，类型标注使用现代语法（如 `str | None`）。
- 日志统一 `logging.getLogger(__name__)`。
- 新增配置优先落在新结构（规则组 + 字典式字段映射）；旧结构仅兼容不扩展。

## ANTI-PATTERNS
- 不要在 `validation_rules` 里继续使用 `type_rules/range_rules`。
- 不要移除 `reader_options`、`clear_rows` 的校验逻辑（现有配置与测试依赖）。
- 不要把中文列名误判为 Excel 列字母（写入器已针对该问题修复并有回归测试）。
- 不要绕过 `main.py` 路径解析逻辑去硬编码相对路径（PyInstaller 场景会出错）。

## COMMANDS
```bash
# 运行模块入口
uv run python -m bank_template_processing input.xlsx "单位名称" "01"

# 运行脚本入口
uv run bank-process input.xlsx "单位名称" "01"

# 针对核心模块的快速回归
uv run pytest tests/test_main.py tests/test_config_loader.py tests/test_excel_writer.py -v
```

## NOTES
- 输出文件名默认模板为：`{unit_name}_{template_name}_{count}人_金额{amount:.2f}元{ext}`。
- `clear_rows` 支持 `end_row` 或兼容键 `data_end_row`（二选一）。
- `template_selector` 分组键仍为 `default/special`，主流程会将 `special` 映射到规则组 `crossbank`。
- `config.example.json` 已采用 `"version": "2.0"`，文档与示例应优先对齐该结构。
