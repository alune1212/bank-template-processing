# TESTS KNOWLEDGE BASE

## OVERVIEW
Comprehensive test suite using `pytest` and `pytest-cov`, covering all application modules with 3k+ lines of test code. Features class-based organization and extensive compatibility testing.

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
- **Class-Based**: All tests grouped in `Test*` classes (e.g., `class TestLoadConfig:`).
- **Naming**: Descriptive snake_case (e.g., `test_load_valid_config`).
- **Fixtures**: Heavy use of built-in `tmp_path`. No custom fixtures in `conftest.py`.
- **Docs**: Bilingual strategy. Module docs in Chinese; Bug tests in English.
- **Mocking**: Use `unittest.mock` (patch, MagicMock) directly, not pytest-mock.
- **Coverage**: Always run with `term-missing` report enabled.

## ANTI-PATTERNS
- **Do NOT** use `src/` layout imports (imports are direct from root).
- **Do NOT** add custom markers (use file structure for organization).
- **Do NOT** rely on `pytest.ini` exclusively (check `pyproject.toml` for duplicates).

## COMMANDS
```bash
# Run all tests
uv run pytest tests/ -v

# Run specific module
uv run pytest tests/test_excel_writer.py -v

# Run with HTML coverage report
uv run pytest --cov=. --cov-report=html
```
