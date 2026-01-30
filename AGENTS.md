# PROJECT KNOWLEDGE BASE

**Generated:** 2026-01-30
**Commit:** 5bf2c39
**Branch:** main

## OVERVIEW
Python CLI tool for processing bank card excel templates. Standard src-layout using `uv` for dependency management and `openpyxl`/`xlrd`/`xlwt` for multi-format Excel handling.

## STRUCTURE
```
./
├── src/
│   └── bank_template_processing/
│       ├── __main__.py           # Module entry point
│       ├── main.py               # CLI entry point (arg parsing)
│       ├── config_loader.py      # JSON config loading & schema validation
│       ├── excel_reader.py       # Input handling (.xlsx, .csv, .xls)
│       ├── excel_writer.py       # Output generation (template filling)
│       ├── transformer.py        # Data cleaning & formatting logic
│       ├── validator.py          # Data constraints & type checking
│       └── template_selector.py  # Dynamic template routing logic
├── tests/                        # Unit & integration tests
├── scripts/                      # Windows build scripts
├── pyproject.toml                # Project metadata, deps, entry points
└── bank_template_processing.spec # PyInstaller build spec
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| **CLI logic** | `src/bank_template_processing/main.py` | Entry point, argument parsing |
| **Config schema** | `src/bank_template_processing/config_loader.py` | `_validate_unit_config` defines schema |
| **Input parsing** | `src/bank_template_processing/excel_reader.py` | Supports 3 formats, row filtering |
| **Output logic** | `src/bank_template_processing/excel_writer.py` | Template preservation, cell writing |
| **Data rules** | `src/bank_template_processing/transformer.py` | Date/Amount/Luhn algorithms |
| **Validation** | `src/bank_template_processing/validator.py` | Required fields, type checks |
| **Build** | `pyproject.toml` | Dependencies, pytest config, entry points |

## CONVENTIONS
- **Layout**: Standard src-layout (`src/bank_template_processing/`).
- **Config**: `pyproject.toml` for project metadata. `config.json` for runtime app config.
- **Dependency**: Uses `uv` exclusively. `uv.lock` is tracked.
- **Documentation**: Bilingual strategy. Module docs in Chinese; Bug reports in English.
- **Imports**: Package imports (e.g., `from bank_template_processing.main import ...`).

## ANTI-PATTERNS (MSI PROJECT)
- **Do NOT** use `pip` directly. Always use `uv` commands.
- **Do NOT** commit `config.json` (contains sensitive/local paths). Use `config.example.json`.
- **Do NOT** use `setup.py`. Use `pyproject.toml` exclusively.
- **Do NOT** rely on `pytest.ini`. Use `pyproject.toml` for pytest config.

## COMMANDS
```bash
# Run App (via module)
uv run python -m bank_template_processing input.xlsx "UnitName" "01"

# Run App (via script entry point)
uv run bank-process input.xlsx "UnitName" "01"

# Run Tests
uv run pytest tests/ -v

# Build Windows Exe
uv run pyinstaller bank_template_processing.spec
```

## NOTES
- **Entry Points**: `pyproject.toml` defines `bank-process` script entry point.
- **Templates**: `templates/` directory is git-ignored. Users must create it or use `templates.example/` (if added).
- **Encoding**: Windows build scripts use CP936/GBK awareness for Chinese console output.
