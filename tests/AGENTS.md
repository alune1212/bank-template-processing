# TESTS KNOWLEDGE BASE

**Generated:** 2026-03-19  
**Commit:** 71c8a33  
**Branch:** main  
**Scope:** `tests/` 测试与回归规范

## OVERVIEW
基于 `pytest`/`pytest-cov` 的完整测试套件，覆盖配置加载、主流程编排、运行时路径保护、共享管线、Excel 三格式读写、数据转换/校验、模板分组、批量合并以及文档同步。

## CURRENT SNAPSHOT
- 测试模块：28 个 `test_*.py`。
- 夹具目录：`tests/fixtures/`（输入样例、公式样例、集成配置等）。
- 质量门槛：总覆盖率 `>=92%`，分支覆盖率 `>=85%`（由 `scripts/check_branch_coverage.py` 校验）。
- 组织方式：
  - 模块化回归为主
  - 边界/错误路径测试单独拆文件维护
  - 通过 `tests/test_docs_sync.py` 约束 README 与配置说明的默认值同步

## STRUCTURE
```text
tests/
├── __init__.py
├── fixtures/
│   ├── test_input.xlsx/.csv/.xls
│   ├── test_formula.xlsx
│   └── integration_*.xlsx/.json
├── test_branch_coverage_script.py
├── test_chinese_column_bug.py
├── test_chinese_column_integration.py
├── test_config_loader.py
├── test_config_loader_edge_cases.py
├── test_docs_sync.py
├── test_error_context.py
├── test_example.py
├── test_excel_reader.py
├── test_excel_reader_error_paths.py
├── test_excel_reader_formula.py
├── test_excel_writer.py
├── test_excel_writer_consistency.py
├── test_excel_writer_error_paths.py
├── test_filename_stats.py
├── test_integration.py
├── test_main.py
├── test_main_runtime_paths.py
├── test_merge_folder.py
├── test_merge_folder_edge_cases.py
├── test_module_entrypoint.py
├── test_pipeline.py
├── test_properties.py
├── test_sheet_utils.py
├── test_template_selector.py
├── test_transformer.py
├── test_validator.py
└── test_validator_edge_cases.py
```

## WHERE TO LOOK
| 场景 | 文件 | 重点 |
|------|------|------|
| 配置新规则校验 | `test_config_loader.py` / `test_config_loader_edge_cases.py` | `reader_options`、`clear_rows`、禁止 `type_rules/range_rules` |
| 运行时路径分支 | `test_main_runtime_paths.py` | 配置/模板相对路径解析、保护分支 |
| 批量合并主路径 | `test_merge_folder.py` | 分组、月份推断、文件名统计校验 |
| 批量合并边界 | `test_merge_folder_edge_cases.py` | 规则组匹配、行读取边界、异常路径 |
| 共享管线 | `test_pipeline.py` | reader 构建、转换判断、上下文错误 |
| 文档默认值同步 | `test_docs_sync.py` | README/配置说明与运行时默认值一致 |
| 读取策略回归 | `test_excel_reader.py` / `test_excel_reader_error_paths.py` | `.xlsx/.csv/.xls`、过滤、`reader_options.header_row` |
| 公式缓存行为 | `test_excel_reader_formula.py` | `data_only=True/False` 差异 |
| 写入复杂路径 | `test_excel_writer.py` / `test_excel_writer_error_paths.py` | `clear_rows`、列解析、XLS/XLSX/CSV 边界 |
| 输出命名逻辑 | `test_filename_stats.py` | `count/amount/ext` 模板变量行为 |
| 中文列名历史缺陷 | `test_chinese_column_bug.py` | 防止中文列名被当作列字母解析 |
| 属性测试 | `test_properties.py` | 关键不变量与随机输入回归 |

## CONVENTIONS
- 测试文件命名保持 `test_*.py`。
- 测试名保持 `test_*`，明确输入条件与期望行为。
- 优先使用内置 `tmp_path` 与 `unittest.mock.patch`。
- 包导入统一 `from bank_template_processing...`，不使用平铺导入。
- 测试配置由 `pyproject.toml` 管理，不新增 `pytest.ini`。
- 属性测试使用 `Hypothesis`，并统一走 `tests/conftest.py` 的 `ci` profile（可复现、禁用 deadline）。

## ANTI-PATTERNS
- 不要只测 happy path，涉及配置解析、写入逻辑和合并逻辑时需同时覆盖失败分支。
- 不要删除中文列名、公式读取、运行时路径和批量合并相关回归测试，这几类都是已落地的历史问题或关键新功能。
- 不要在测试里依赖本地 `config.json` 或 `templates/` 实目录，使用 `tests/fixtures` 与临时目录。
- 不要引入与现有结构重复的“超大综合测试”，优先在对应模块追加聚焦用例。

## COMMANDS
```bash
# 全量测试
uv run pytest tests/ -v

# 关键回归（主流程 + 合并 + 共享管线）
uv run pytest tests/test_main.py tests/test_merge_folder.py tests/test_pipeline.py -v --no-cov

# 读取策略回归（含公式）
uv run pytest tests/test_excel_reader.py tests/test_excel_reader_formula.py -v --no-cov

# 文档同步
uv run pytest tests/test_docs_sync.py -v --no-cov

# 含覆盖率
uv run pytest tests/ --cov=src --cov-branch --cov-report=xml --cov-fail-under=92
uv run python scripts/check_branch_coverage.py --min-branch 85 --xml coverage.xml
```

## NOTES
- `tests/test_main.py` 中自定义文件名模板用例仍包含 `{timestamp}`，用于验证“模板透传”而非默认模板值。
- `tests/test_docs_sync.py` 只校验文档与默认值同步；单独运行时请配合 `--no-cov`，否则会被仓库全局覆盖率门槛拦下。
- `tests/test_excel_writer.py` 与 `tests/test_excel_writer_consistency.py` 对 `clear_rows` 在三种格式中的行为差异都有覆盖。
- `tests/test_validator.py` 对 `allowed_values` 的日期/数值归一化比较已有覆盖，修改校验逻辑时需优先回归。
