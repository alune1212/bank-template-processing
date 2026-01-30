# TESTS KNOWLEDGE BASE

## OVERVIEW
Comprehensive test suite using `pytest` and `pytest-cov`, covering all application modules. Features class-based organization and extensive compatibility testing.

## STRUCTURE
```
tests/
├── __init__.py                # Package marker
├── fixtures/                  # Shared test data (XLS, XLSX, CSV)
├── test_*.py                 # Unit tests mirroring root modules
├── test_integration.py        # End-to-end workflows
└── test_chinese_column_*.py  # Specialized bug regression tests
```

## WHERE TO LOOK
| Type | File Pattern | Notes |
|------|--------------|-------|
| **Unit Tests** | `test_[module].py` | Class-based, isolated tests |
| **Integration** | `test_integration.py` | Full CLI workflows, e2e logic |
| **Bug Fixes** | `test_chinese_*.py` | Regression tests for specific issues |
| **Fixtures** | `fixtures/` | Excel/JSON files for testing |

## CONVENTIONS
- **Class-Based**: All tests grouped in `Test*` classes.
- **Naming**: Descriptive snake_case (e.g., `test_load_valid_config`).
- **Fixtures**: Use built-in `tmp_path`. No custom fixtures in `conftest.py`.
- **Docs**: Bilingual strategy. Module docs in Chinese.
- **Mocking**: Use `unittest.mock` directly.
- **Imports**: Uses installed package (src layout).

## ANTI-PATTERNS
- **Do NOT** use flat layout imports (e.g. `import main` is wrong; use `from bank_template_processing import main`).
- **Do NOT** add custom markers (use file structure for organization).
- **Do NOT** rely on `pytest.ini` (use `pyproject.toml`).

## COMMANDS
```bash
# Run all tests
uv run pytest tests/ -v

# Run with HTML coverage report
uv run pytest --cov=src --cov-report=html
```
