# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Run CLI (module mode)
uv run python -m bank_template_processing input.xlsx "单位名称" "01"

# Run CLI (script entry)
uv run bank-process input.xlsx "单位名称" "01"

# Run all tests
uv run pytest tests/ -v

# Run single test file
uv run pytest tests/test_filename_stats.py -v

# Format and lint
uv run ruff format .
uv run ruff check . --fix

# Type check
uv run ty check

# Build Windows executable
pwsh ./scripts/build_windows.ps1
```

## Architecture

Data processing pipeline: **Reader → Transformer → Validator → Writer**

| Module | Purpose |
|--------|---------|
| `main.py` | CLI parsing, pipeline orchestration, output filename generation |
| `config_loader.py` | JSON config loading, schema validation |
| `excel_reader.py` | Read `.xlsx/.csv/.xls`, supports `data_only` for formulas, `row_filter` for filtering |
| `transformer.py` | Date/amount/card number transformations, Luhn validation |
| `validator.py` | Required fields, data types, value ranges |
| `excel_writer.py` | Write to templates, auto-numbering, field/fixed value mapping |
| `template_selector.py` | Dynamic template selection by bank name (full-width normalization) |
| `merge_folder.py` | Batch merge generated files by unit+template grouping |

## Key Patterns

- **Config structure**: `organization_units` → unit configs with `field_mappings`, `fixed_values`, `auto_number`, `template_selector`
- **Field mapping dict**: `{"source_column": "输入列", "transform": "date_format|amount_decimal|card_number|none", "required": true}`
- **Output filename**: `{unit_name}_{template_name}_{count}人_金额{amount:.2f}元{ext}` (default template)
- **Row filtering**: Default filters rows where `实发工资 = 0` after read, before transform

## Conventions

- Use `uv` for all dependency management (not `pip`)
- Type annotations: Python 3.13+ syntax (`str | None`)
- Logging: `logging.getLogger(__name__)`
- Config: Prefer new dict-based `field_mappings` over legacy list format
- Do not commit `config.json` (local sensitive config); use `config.example.json`

## Anti-Patterns

- Don't use old validation keys `type_rules/range_rules` in `validation_rules`
- Don't treat Chinese column names as Excel column letters (regression test: `test_chinese_column_bug.py`)
- Don't remove `clear_rows` or `reader_options` validation (existing configs depend on them)