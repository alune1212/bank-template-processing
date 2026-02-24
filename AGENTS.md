# PROJECT KNOWLEDGE BASE

**Generated:** 2026-02-24  
**Commit:** b7b2f84  
**Branch:** main

## OVERVIEW
银行卡进卡模板处理 CLI。将 OA 审批数据清洗、校验并写入银行模板，支持 `.xlsx/.csv/.xls` 输入输出，支持按银行列动态分组到不同模板。

## CURRENT SNAPSHOT
- 运行时与依赖：
  - `.python-version` 为 `3.14`
  - `pyproject.toml` 要求 `requires-python >=3.13`
  - 使用 `uv` 管理依赖，`uv.lock` 已跟踪
- 包结构：
  - `src/bank_template_processing/` 共 9 个 `.py` 文件（`main.py` 593 行，`excel_writer.py` 843 行）
- 测试结构：
  - `tests/` 当前有 13 个 `test_*.py` 文件
  - 覆盖主流程、配置校验、中文列名回归、公式读取策略、文件名统计逻辑
- 配置现状：
  - `config.example.json` 当前为 `"version": "2.0"`
  - 同时支持旧结构和多规则组结构（`default` / `crossbank`）

## STRUCTURE
```text
./
├── src/bank_template_processing/
│   ├── __main__.py                # 模块入口（python -m）
│   ├── main.py                    # CLI 参数、主流程编排、输出文件名统计变量
│   ├── config_loader.py           # 配置加载/校验（含 reader_options、clear_rows）
│   ├── excel_reader.py            # 读取 .xlsx/.csv/.xls，支持 row_filter/data_only/header_row
│   ├── excel_writer.py            # 写入 .xlsx/.csv/.xls，支持 clear_rows/自动编号/映射模式
│   ├── transformer.py             # 日期/金额/卡号转换，Luhn 校验
│   ├── validator.py               # required/data_types/value_ranges 校验
│   └── template_selector.py       # 模板分组，银行名全角/空白归一化
├── tests/                         # 13 个测试模块 + fixtures
├── scripts/                       # Windows 打包脚本（ps1/bat）
├── skills/                        # 项目内技能（doc-coauthoring, xlsx）
├── templates.example/             # 模板目录说明
├── pyproject.toml                 # 依赖、脚本入口、pytest/ruff 配置
├── bank_template_processing.spec  # PyInstaller spec
└── run_for_pyinstaller.py         # PyInstaller 入口包装
```

## WHERE TO LOOK
| 任务 | 位置 | 说明 |
|------|------|------|
| CLI 与流程总控 | `src/bank_template_processing/main.py` | 参数解析、月份校验、路径解析、分组处理、错误出口 |
| 输出文件名策略 | `src/bank_template_processing/main.py` | 默认模板：`{unit_name}_{template_name}_{count}人_金额{amount:.2f}元{ext}` |
| 配置模式与校验 | `src/bank_template_processing/config_loader.py` | 校验 `data_types/value_ranges`，禁止旧键 `type_rules/range_rules` |
| 输入读取 | `src/bank_template_processing/excel_reader.py` | `data_only` 公式读取策略、`row_filter.exclude_keywords`、`reader_options.header_row` |
| 输出写入 | `src/bank_template_processing/excel_writer.py` | `clear_rows`、`column_name/column_index` 映射、三格式写入 |
| 分组逻辑 | `src/bank_template_processing/template_selector.py` | 默认组/特殊组拆分，支持 `default_group_name/special_group_name` |
| 数据转换 | `src/bank_template_processing/transformer.py` | 金额舍入模式（`round/half_up/floor/ceil/down/up`）与卡号 Luhn |
| 数据验证 | `src/bank_template_processing/validator.py` | required、类型、范围、枚举值归一化比较 |
| 关键回归测试 | `tests/test_chinese_column_bug.py` | 防止中文列名被误判为 Excel 列字母 |
| 公式读取测试 | `tests/test_excel_reader_formula.py` | `data_only=True/False` 行为差异 |
| 文件名统计测试 | `tests/test_filename_stats.py` | `_calculate_stats` 与 `generate_output_filename` |

## CONVENTIONS
- 目录结构：保持 `src` 布局，导入使用包路径（`bank_template_processing.*`）。
- 类型标注：按 Python 3.13+ 语法（如 `str | None`）。
- 日志：统一 `logging.getLogger(__name__)`。
- 配置优先：优先维护新配置格式（字段映射字典结构 + 多规则组）；旧格式仅做兼容。
- 测试组织：`pytest`，按模块拆分 `test_*.py`，配置集中在 `pyproject.toml`。

## ANTI-PATTERNS (THIS PROJECT)
- 不要在日常开发流程直接使用 `pip`，统一使用 `uv`（`build_windows.bat` 属于兼容脚本，保留历史行为）。
- 不要提交 `config.json`（本地敏感配置）；使用 `config.example.json`。
- 不要新增 `setup.py` 或 `pytest.ini`，继续使用 `pyproject.toml`。
- 不要在 `validation_rules` 中使用旧键 `type_rules/range_rules`。
- 不要把中文列名当作 Excel 列字母处理（相关回归见 `tests/test_chinese_column_bug.py`）。
- 不要删除 `clear_rows` 与 `reader_options` 相关校验，它们已被现有配置与测试依赖。

## COMMANDS
```bash
# 安装/同步依赖
uv sync

# 运行 CLI（模块方式）
uv run python -m bank_template_processing input.xlsx "单位名称" "01"

# 运行 CLI（脚本入口）
uv run bank-process input.xlsx "单位名称" "01"

# 运行测试
uv run pytest tests/ -v

# 单测（文件名统计）
uv run pytest tests/test_filename_stats.py -v

# 代码格式化与检查
uv run ruff format .
uv run ruff check . --fix

# Windows 打包（推荐）
pwsh ./scripts/build_windows.ps1

# 直接打包
uv run pyinstaller bank_template_processing.spec
```

## NOTES
- `templates/` 目录在 `.gitignore` 中，仓库只保留 `templates.example/README.md` 作为占位说明。
- `main.py` 已支持通过 `--output-filename-template` 自定义文件名，变量含 `{unit_name} {month} {template_name} {count} {amount} {ext}`。
- `clear_rows` 支持 `end_row` 或兼容键 `data_end_row`（二者不能同时存在）。
- `TemplateSelector` 会做全角转半角与首尾空白归一化，避免银行名格式差异导致分组错误。
- `tests/test_main.py` 仍保留旧模板变量示例（`{timestamp}`）用于“自定义模板透传”场景；默认模板已切换为“人数+金额”格式。
