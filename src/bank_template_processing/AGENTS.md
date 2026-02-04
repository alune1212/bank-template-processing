# PACKAGE KNOWLEDGE BASE

**Generated:** 2026-02-04  
**Scope:** Core business logic for bank card Excel template processing

## OVERVIEW
Handles input parsing, data transformation, validation, and template-based output generation. Supports multi-format Excel (.xlsx/.csv/.xls), dynamic template routing by bank name, and comprehensive data validation including Luhn algorithm for card numbers.

## STRUCTURE
```
src/bank_template_processing/
├── __init__.py           # Package marker (empty)
├── __main__.py           # Module entry point (python -m)
├── main.py               # CLI logic, workflow orchestration (594 lines)
├── config_loader.py      # JSON config loading & multi-rule schema validation
├── excel_reader.py       # Input handling (.xlsx, .csv, .xls) with filtering
├── excel_writer.py       # Template filling, auto-numbering, fixed values
├── transformer.py        # Date/amount/card transformation, Luhn validation
├── validator.py          # Required fields, type checking, range validation
└── template_selector.py  # Dynamic routing by "开户银行" column
```

## WHERE TO LOOK
| Task | Module | Notes |
|------|--------|-------|
| **CLI logic** | `main.py` | Entry point, argument parsing |
| **Config schema** | `config_loader.py` | `_validate_unit_config` defines schema |
| **Input parsing** | `excel_reader.py` | Supports 3 formats, row filtering |
| **Output logic** | `excel_writer.py` | Template preservation, cell writing |
| **Data rules** | `transformer.py` | Date/Amount/Luhn algorithms |
| **Validation** | `validator.py` | Required fields, type checks |
| **Template routing** | `template_selector.py` | Selects template based on bank |

## CONVENTIONS
- **Layout**: Standard `src/` layout.
- **Imports**: Use relative imports (e.g., `from . import config_loader`).
- **Typing**: Python 3.13+ type hints required.
- **Docs**: Bilingual strategy (Chinese module docs).

## ANTI-PATTERNS
- **Do NOT** hardcode Excel formulas in Python. Use valid Excel formula strings.
- **Do NOT** use absolute imports from `src`. Use relative or package imports.
- **Do NOT** commit `config.json` (sensitive).
- **Do NOT** flatten to root without updating imports/tests.

## COMMANDS
```bash
# Run module
uv run python -m bank_template_processing input.xlsx "Unit" "01"
```
