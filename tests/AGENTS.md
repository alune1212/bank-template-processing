# TESTS KNOWLEDGE BASE

**Generated:** 2026-02-24  
**Commit:** f728266  
**Branch:** main  
**Scope:** `tests/` 测试与回归规范

## OVERVIEW
基于 `pytest`/`pytest-cov` 的完整测试套件，覆盖配置加载、主流程编排、Excel 三格式读写、数据转换/校验、模板分组及历史缺陷回归。

## CURRENT SNAPSHOT
- 测试模块：13 个 `test_*.py`。
- 测试用例：约 203 个 `test_*` 函数/方法。
- 夹具目录：`tests/fixtures/`（`xlsx/csv/xls/json`）。
- 组织方式：
  - 以 `Test*` 类组织为主
  - 以函数式测试补充关键回归（如公式读取、文件名统计、中文列名问题）

## STRUCTURE
```text
tests/
├── __init__.py
├── fixtures/
│   ├── test_input.xlsx/.csv/.xls
│   ├── test_formula.xlsx
│   └── integration_*.xlsx/.json
├── test_main.py                    # CLI 参数、主流程、transform 应用
├── test_config_loader.py           # 配置结构/规则校验（含新旧键兼容）
├── test_excel_reader.py            # 三格式读取、row_filter、header_row
├── test_excel_reader_formula.py    # data_only 公式读取行为
├── test_excel_writer.py            # 三格式写入、clear_rows、mapping_mode、自动编号
├── test_transformer.py             # 日期/金额/卡号/Luhn
├── test_validator.py               # required/data_types/value_ranges
├── test_template_selector.py       # 分组逻辑、全角归一化、自定义列名
├── test_integration.py             # 端到端流程与错误处理
├── test_filename_stats.py          # 输出文件名与统计逻辑
├── test_chinese_column_bug.py      # 中文列名误判回归
├── test_chinese_column_integration.py
└── test_example.py                 # 最小示例测试
```

## WHERE TO LOOK
| 场景 | 文件 | 重点 |
|------|------|------|
| 配置新规则校验 | `test_config_loader.py` | `reader_options`、`clear_rows`、禁止 `type_rules/range_rules` |
| 读取策略回归 | `test_excel_reader.py` | `.xlsx/.csv/.xls`、过滤、`reader_options.header_row` |
| 公式缓存行为 | `test_excel_reader_formula.py` | `data_only=True/False` 差异 |
| 写入复杂路径 | `test_excel_writer.py` | `clear_rows`、`column_index`、XLS 范围校验 |
| 输出命名逻辑 | `test_filename_stats.py` | `count/amount/ext` 模板变量行为 |
| 银行分组边界 | `test_template_selector.py` | 全角空格/全角字母归一化、空值校验 |
| 中文列名历史缺陷 | `test_chinese_column_bug.py` | 防止中文列名被当作列字母解析 |
| 端到端流程 | `test_integration.py` | 典型成功流、异常流、动态模板选择 |

## CONVENTIONS
- 测试文件命名保持 `test_*.py`。
- 测试名保持 `test_*`，明确输入条件与期望行为。
- 优先使用内置 `tmp_path` 与 `unittest.mock.patch`。
- 包导入统一 `from bank_template_processing...`，不使用平铺导入。
- 测试配置由 `pyproject.toml` 管理，不新增 `pytest.ini`。

## ANTI-PATTERNS
- 不要只测 happy path，涉及配置解析与写入逻辑需同时覆盖失败分支。
- 不要删除中文列名与公式读取相关回归测试，这两类问题已有历史缺陷。
- 不要在测试里依赖本地 `config.json` 或 `templates/` 实目录，使用 `tests/fixtures` 与临时目录。
- 不要引入与现有结构重复的“超大综合测试”，优先在对应模块追加聚焦用例。

## COMMANDS
```bash
# 全量测试
uv run pytest tests/ -v

# 关键回归（配置 + 写入 + 中文列名）
uv run pytest tests/test_config_loader.py tests/test_excel_writer.py tests/test_chinese_column_bug.py -v

# 读取策略回归（公式）
uv run pytest tests/test_excel_reader.py tests/test_excel_reader_formula.py -v

# 含覆盖率
uv run pytest --cov=src --cov-report=term-missing
```

## NOTES
- `tests/test_main.py` 中自定义文件名模板用例仍包含 `{timestamp}`，用于验证“模板透传”而非默认模板值。
- `tests/test_excel_writer.py` 对 `clear_rows` 在三种格式中的行为差异都有覆盖。
- `tests/test_validator.py` 对 `allowed_values` 的日期/数值归一化比较已有覆盖，修改校验逻辑时需优先回归。
