# PROJECT KNOWLEDGE BASE

**Generated:** 2026-01-28
**Commit:** 5bf2c39
**Branch:** main

## OVERVIEW
Python CLI tool for processing bank card excel templates. Flat-layout application using `uv` for dependency management and `openpyxl`/`xlrd`/`xlwt` for multi-format Excel handling.

## STRUCTURE
```
./
├── main.py                    # CLI entry point (arg parsing, workflow)
├── config_loader.py           # JSON config loading & schema validation
├── excel_reader.py            # Input handling (.xlsx, .csv, .xls)
├── excel_writer.py            # Output generation (template filling)
├── transformer.py             # Data cleaning & formatting logic
├── validator.py               # Data constraints & type checking
├── template_selector.py       # Dynamic template routing logic
├── bank_template_processing.spec # PyInstaller build spec
└── scripts/                   # Windows build scripts
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| **CLI logic** | `main.py` | Entry point, argument parsing |
| **Config schema** | `config_loader.py` | `_validate_unit_config` defines schema |
| **Input parsing** | `excel_reader.py` | Supports 3 formats, row filtering |
| **Output logic** | `excel_writer.py` | Template preservation, cell writing |
| **Data rules** | `transformer.py` | Date/Amount/Luhn algorithms |
| **Validation** | `validator.py` | Required fields, type checks |
| **Build** | `pyproject.toml` | Dependencies, pytest config |

## CONVENTIONS
- **Layout**: Flat structure (no `src/` directory). All modules in root.
- **Config**: `pyproject.toml` for project metadata. `config.json` for runtime app config.
- **Dependency**: Uses `uv` (modern pip replacement). `uv.lock` is tracked.
- **Documentation**: Bilingual strategy. Module docs in Chinese; Bug reports in English.
- **Imports**: Direct imports (e.g., `from config_loader import ...`).

## ANTI-PATTERNS (THIS PROJECT)
- **Do NOT** add `src/` directory without full refactor of imports/tests.
- **Do NOT** commit `config.json` (contains sensitive/local paths). Use `config.example.json`.
- **Do NOT** use `setup.py`. Use `pyproject.toml` exclusively.
- **Do NOT** rely on `pytest.ini` if `pyproject.toml` has config (dual config exists, prefer `pyproject.toml`).

## COMMANDS
```bash
# Run App
uv run main.py input.xlsx "UnitName" "01"

# Run Tests
uv run pytest tests/ -v

# Build Windows Exe
uv run pyinstaller bank_template_processing.spec
```

## NOTES
- **Dual Config**: `pytest.ini` and `pyproject.toml` contain duplicate test configs. `pytest.ini` currently takes precedence.
- **Templates**: `templates/` directory is git-ignored. Users must create it or use `templates.example/` (if added).
- **Encoding**: Windows build scripts use CP936/GBK awareness for Chinese console output.
