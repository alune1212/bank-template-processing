# PACKAGE KNOWLEDGE BASE

## OVERVIEW
Core business logic for processing bank card excel templates. Handles input parsing, data transformation, validation, and template-based output generation.

## STRUCTURE
```
src/bank_template_processing/
├── config_loader.py      # JSON config loading & schema validation
├── excel_reader.py       # Input handling (.xlsx, .csv, .xls)
├── excel_writer.py       # Output generation (template filling)
├── main.py               # CLI entry point logic
├── template_selector.py  # Dynamic template routing
├── transformer.py        # Data cleaning & formatting logic
└── validator.py          # Data constraints & type checking
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
