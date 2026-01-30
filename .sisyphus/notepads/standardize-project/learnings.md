
## Learnings - Fix Test Imports (2026-01-30)

### Task
Fix test imports to work with `src/` layout after code reorganization.

### Changes Made

1. **Updated all test imports** to use package imports:
   - `from config_loader import ...` → `from bank_template_processing.config_loader import ...`
   - `from transformer import ...` → `from bank_template_processing.transformer import ...`
   - `from excel_reader import ...` → `from bank_template_processing.excel_reader import ...`
   - `from excel_writer import ...` → `from bank_template_processing.excel_writer import ...`
   - `from validator import ...` → `from bank_template_processing.validator import ...`
   - `from template_selector import ...` → `from bank_template_processing.template_selector import ...`
   - `from main import ...` → `from bank_template_processing.main import ...`

2. **Updated pytest decorators** in `test_main.py`:
   - `@patch("main.ExcelReader")` → `@patch("bank_template_processing.main.ExcelReader")`
   - `@patch("main.ExcelWriter")` → `@patch("bank_template_processing.main.ExcelWriter")`
   - `@patch("main.TemplateSelector")` → `@patch("bank_template_processing.main.TemplateSelector")`

3. **Updated `pyproject.toml`**:
   - `pythonpath = "."` → `pythonpath = ["src"]`
   - `--cov=.` → `--cov=src` (coverage should target src directory)
   - `bank-process = "main:main"` → `bank-process = "bank_template_processing.main:main"`

4. **Updated `pytest.ini`**:
   - `pythonpath = .` → `pythonpath = src`
   - `--cov=.` → `--cov=src`

5. **Installed package in editable mode**: `uv pip install -e .`

### Verification

```bash
# Run all tests
.venv/bin/python -m pytest tests/ -v

# Results: 155 passed, 1 failed (pre-existing, unrelated failure)
```

### Key Insight

When using `src/` layout with Python projects:
- Tests must import using the package name: `from mypackage.module import ...`
- `pythonpath` in pytest config should point to `src`, not `.`
- Package must be installed in editable mode (`pip install -e .` or `uv pip install -e .`)
- Coverage should target `src` directory

### Files Modified
- `tests/test_config_loader.py`
- `tests/test_transformer.py`
- `tests/test_excel_reader.py`
- `tests/test_excel_writer.py`
- `tests/test_validator.py`
- `tests/test_template_selector.py`
- `tests/test_main.py`
- `tests/test_integration.py`
- `tests/test_chinese_column_bug.py`
- `tests/test_chinese_column_integration.py`
- `pyproject.toml`
- `pytest.ini`

---

## Learnings - Update Build Spec (PyInstaller) (2026-01-30)

### Task
Update PyInstaller build spec file to work with `src/` layout.

### Problem
PyInstaller cannot easily handle package entry points with src layout. Pointing to `src/bank_template_processing/main.py` or `__main__.py` results in "attempted relative import with no known parent package" errors.

### Solution

1. **Created wrapper script** `run_for_pyinstaller.py` in project root:
   ```python
   """
   PyInstaller entry point script.
   PyInstaller cannot easily handle package entry points with src layout,
   so we use this simple wrapper script.
   """

   if __name__ == '__main__':
       from bank_template_processing.main import main
       main()
   ```

2. **Updated `bank_template_processing.spec`**:
   - Changed script from `['main.py']` to `['run_for_pyinstaller.py']`
   - Added `src` to `pathex`: `pathex=[str(project_root), str(project_root / 'src')]`
   - Added package hidden imports:
     ```python
     'bank_template_processing',
     'bank_template_processing.main',
     ```

3. **Preserved existing configuration**:
   - All existing `hiddenimports` (openpyxl, xlrd, xlwt) remain valid
   - `datas` entries unchanged (config.example.json, README.md, 配置文件说明.md)
   - Output name unchanged: `bank-template-processing`

### Verification

```bash
# Build with PyInstaller
uv run pyinstaller bank_template_processing.spec --noconfirm
# Result: Build complete!

# Test executable
./dist/bank-template-processing/bank-template-processing --help
# Result: Shows help message correctly

# Test with missing config
./dist/bank-template-processing/bank-template-processing test.xlsx "test" "01"
# Result: Runs and reports missing config.json (expected)
```

### Key Insight

PyInstaller with src layout requires a wrapper script because:
- Direct module import (`-m bank_template_processing.main`) doesn't work with PyInstaller
- Entry point from `pyproject.toml` (`bank_template_processing.main:main`) cannot be used directly
- Relative imports in package modules fail when run as standalone scripts
- The wrapper script allows absolute import: `from bank_template_processing.main import main`

### Files Modified
- `bank_template_processing.spec`
- `run_for_pyinstaller.py` (new file)

### Files Created (Output)
- `dist/bank-template-processing/bank-template-processing` (executable)
- `dist/bank-template-processing/_internal/` (runtime files)
