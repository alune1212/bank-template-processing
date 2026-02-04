# PROJECT KNOWLEDGE BASE

**Generated:** 2026-02-04
**Commit:** ada210c
**Branch:** main

## OVERVIEW
Python CLI tool for processing bank card Excel templates. Transforms OA system approval data into bank-specific formats. Uses standard src-layout with `uv` for dependency management and `openpyxl`/`xlrd`/`xlwt` for multi-format Excel handling.

## STRUCTURE
```
./
├── src/bank_template_processing/   # Core package (10 modules)
│   ├── __main__.py                 # Module entry point
│   ├── main.py                     # CLI entry, argument parsing
│   ├── config_loader.py            # JSON config loading & validation
│   ├── excel_reader.py             # Input handling (.xlsx, .csv, .xls)
│   ├── excel_writer.py             # Output generation (template filling)
│   ├── transformer.py              # Data cleaning & formatting
│   ├── validator.py                # Data constraints & type checking
│   └── template_selector.py        # Dynamic template routing
├── tests/                          # 15 test files, pytest-based
├── scripts/                        # Windows build scripts (PowerShell/batch)
├── skills/                         # Custom skills (doc-coauthoring, xlsx)
├── templates.example/              # Example template files
├── pyproject.toml                  # Project metadata, deps, entry points
└── bank_template_processing.spec   # PyInstaller build spec
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| **CLI logic** | `src/bank_template_processing/main.py` | Entry point, argument parsing, PyInstaller path resolution |
| **Config schema** | `src/bank_template_processing/config_loader.py` | `_validate_unit_config` defines schema, supports multi-rule groups |
| **Input parsing** | `src/bank_template_processing/excel_reader.py` | Supports 3 formats (.xlsx/.csv/.xls), row filtering, data_only mode |
| **Output logic** | `src/bank_template_processing/excel_writer.py` | Template preservation, cell writing, formula support |
| **Data rules** | `src/bank_template_processing/transformer.py` | Date/Amount/Luhn algorithms, multi-format date parsing |
| **Validation** | `src/bank_template_processing/validator.py` | Required fields, type checks, value ranges |
| **Template routing** | `src/bank_template_processing/template_selector.py` | Dynamic template selection based on bank column |
| **Build** | `pyproject.toml` | Dependencies, pytest config, entry points, ruff settings |

## CONVENTIONS
- **Layout**: Standard src-layout (`src/bank_template_processing/`).
- **Config**: `pyproject.toml` for project metadata; `config.json` for runtime app config.
- **Dependency**: Uses `uv` exclusively. `uv.lock` is tracked.
- **Documentation**: Bilingual strategy. Module docs in Chinese; bug reports in English.
- **Imports**: Package imports (e.g., `from bank_template_processing.main import ...`).
- **Type Hints**: Python 3.13+ type hints required (e.g., `str | None`).
- **Logging**: Use `logging.getLogger(__name__)` pattern.

## ANTI-PATTERNS (THIS PROJECT)
- **Do NOT** use `pip` directly. Always use `uv` commands.
- **Do NOT** commit `config.json` (contains sensitive/local paths). Use `config.example.json`.
- **Do NOT** use `setup.py`. Use `pyproject.toml` exclusively.
- **Do NOT** rely on `pytest.ini`. Use `pyproject.toml` for pytest config.
- **Do NOT** hardcode Excel formulas in Python. Use valid Excel formula strings.
- **Do NOT** use absolute imports from `src`. Use relative or package imports.
- **Do NOT** flatten to root without updating imports/tests.

## COMMANDS
```bash
# Run App (via module)
uv run python -m bank_template_processing input.xlsx "UnitName" "01"

# Run App (via script entry point)
uv run bank-process input.xlsx "UnitName" "01"

# Run Tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Build Windows Exe
uv run pyinstaller bank_template_processing.spec

# Format code
uv run ruff format .

# Lint code
uv run ruff check . --fix
```

## NOTES
- **Entry Points**: `pyproject.toml` defines `bank-process` script entry point.
- **Templates**: `templates/` directory is git-ignored. Users must create it or use `templates.example/`.
- **Encoding**: Windows build scripts use CP936/GBK awareness for Chinese console output.
- **Multi-Rule Groups**: Config supports both legacy structure and new multi-rule group structure (default/crossbank).
- **Template Selection**: Dynamic template routing based on "开户银行" column value.
- **Config Versioning**: Config files include `"version": "1.0"` field for future migrations.
