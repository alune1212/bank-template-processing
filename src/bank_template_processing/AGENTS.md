# PACKAGE KNOWLEDGE BASE

**Generated:** 2026-03-19  
**Commit:** 71c8a33  
**Branch:** main  
**Scope:** `src/bank_template_processing/` 核心业务代码

## OVERVIEW
负责 CLI 主流程、配置校验、Excel 多格式读写、数据转换与验证、按银行动态模板分组，以及已生成文件的批量合并。当前以共享管线 `pipeline.py` 串起读取、校验、转换、统计和错误上下文补充。

## CURRENT SNAPSHOT
- 模块规模：13 个 `.py` 文件。
- 大文件：
  - `merge_folder.py` 817 行
  - `excel_writer.py` 714 行
  - `main.py` 642 行
  - `config_loader.py` 620 行
  - `validator.py` 523 行
- 入口：
  - `__main__.py`：`python -m bank_template_processing`
  - `main.py:main`：命令行脚本入口（`bank-process`）
- 配置兼容：
  - 旧结构（单位下直接配置）
  - 新结构（单位下 `default/crossbank/...` 规则组）

## STRUCTURE
```text
src/bank_template_processing/
├── __init__.py           # 包标识
├── __main__.py           # 模块入口
├── main.py               # 参数解析、主流程、输出命名、模式切换
├── config_loader.py      # 配置加载与结构校验
├── config_types.py       # TypedDict 配置类型
├── excel_reader.py       # 读取 .xlsx/.xls（含 data_only/header_row）
├── excel_writer.py       # 写入 .xlsx/.xls（含 clear_rows/列解析）
├── merge_folder.py       # 批量合并目录模式
├── pipeline.py           # 共享处理管线与上下文补错
├── sheet_utils.py        # 列标识、表头、单元格转换工具
├── transformer.py        # 日期/金额/卡号转换 + Luhn
├── validator.py          # required/data_types/value_ranges 校验
└── template_selector.py  # 银行名归一化与 default/special 分组
```

## WHERE TO LOOK
| 任务 | 模块 | 关键点 |
|------|------|------|
| CLI 主链路 | `main.py` | `parse_args`、`validate_month`、`main`、模式切换处理函数 |
| 共享管线 | `pipeline.py` | `build_reader`、`split_validation_rules`、`apply_transformations`、`calculate_stats` |
| 批量合并 | `merge_folder.py` | `prepare_merge_tasks`、`parse_merge_filename`、`resolve_rule_group_for_template` |
| 输出文件名 | `main.py` | `generate_output_filename` + `pipeline.calculate_stats` |
| 配置校验 | `config_loader.py` | 禁止旧键 `type_rules/range_rules`，支持 `data_types/value_ranges` |
| 读取策略 | `excel_reader.py` | `row_filter.exclude_keywords`、`reader_options.data_only/header_row` |
| 写入策略 | `excel_writer.py` | `clear_rows`、列名/列字母/列索引解析、XLS/XLSX 写入 |
| 列解析 | `sheet_utils.py` | 中文列名与 Excel 列字母区分、列索引转换 |
| 银行分组 | `template_selector.py` | 全角转半角、空白归一化、组名配置 |
| 转换规则 | `transformer.py` | 日期解析、金额舍入、卡号清洗与 Luhn |
| 值校验 | `validator.py` | 类型/区间/枚举归一化比较 |

## CONVENTIONS
- 保持 `src` 布局，导入使用包路径或相对导入，不做根目录平铺。
- Python 版本按 `>=3.13`，类型标注使用现代语法（如 `str | None`）。
- 日志统一 `logging.getLogger(__name__)`。
- 新增配置优先落在新结构（规则组 + 字典式字段映射）；旧结构仅兼容不扩展。
- 共享逻辑优先沉淀到 `pipeline.py` 或 `sheet_utils.py`，避免在 `main.py`/`merge_folder.py` 复制实现。

## ANTI-PATTERNS
- 不要在 `validation_rules` 里继续使用 `type_rules/range_rules`。
- 不要移除 `reader_options`、`clear_rows` 的校验逻辑（现有配置与测试依赖）。
- 不要把中文列名误判为 Excel 列字母（相关行为由 `sheet_utils.py` 统一处理并有回归测试）。
- 不要绕过 `main.py` 路径解析逻辑去硬编码相对路径（PyInstaller 场景会出错）。
- 不要在批量合并分支里重复实现转换/校验流程，优先复用 `pipeline.py`。

## COMMANDS
```bash
# 运行模块入口
uv run python -m bank_template_processing input.xlsx "单位名称" "01"

# 运行脚本入口
uv run bank-process input.xlsx "单位名称" "01"

# 针对核心模块的快速回归
uv run pytest tests/test_main.py tests/test_pipeline.py tests/test_merge_folder.py tests/test_excel_writer.py -v --no-cov
```

## NOTES
- 输出文件名默认模板为：`{unit_name}_{template_name}_{count}人_金额{amount:.2f}元{ext}`。
- `clear_rows` 支持 `end_row` 或兼容键 `data_end_row`（二选一）。
- `template_selector` 分组键仍为 `default/special`，主流程会将 `special` 映射到规则组 `crossbank`。
- `merge_folder.py` 在文件名含人数/金额时会进行统计一致性校验；若文件名不完整则按规则跳过相应校验。
- `config.example.json` 已采用 `"version": "2.0"`，文档与示例应优先对齐该结构。
