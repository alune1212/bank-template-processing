# Orchestration Report: Standardize Project

## Summary
Successfully standardized the project structure and toolchain. The project now uses a standard `src/` layout, consolidated configuration in `pyproject.toml`, and modern tools (Ruff, Ty).

## Completed Tasks
- [x] **Update Configuration**: Consolidated `pytest.ini` and tool configs into `pyproject.toml`. Replaced `mypy` with `ty`. Added `hatchling` build backend.
- [x] **Refactor to src/ Layout**: Moved all source code to `src/bank_template_processing/`. Preserved git history.
- [x] **Fix Imports**: Updated all imports to use relative imports within the package and absolute imports in tests. Fixed `get_executable_dir()` logic for dev mode.
- [x] **Fix Tests**: Updated test imports and fixed a regression in `test_main.py`.
- [x] **Update Build**: Updated `bank_template_processing.spec` and added `run_for_pyinstaller.py` wrapper.
- [x] **Standardization**: Formatted code with Ruff. Documented Ty errors in `issues.md`.
- [x] **Cleanup**: Removed `pytest.ini` and `__pycache__`.

## Key Changes
- **Source Layout**: `src/bank_template_processing/`
- **Config**: `pyproject.toml` is the single source of truth.
- **Build**: `uv run pyinstaller bank_template_processing.spec` works with the new layout.
- **Dev Workflow**: `uv run python -m bank_template_processing` works.

## Known Issues
- **Ty Errors**: 15 type errors documented in `.sisyphus/notepads/standardize-project/issues.md`. These are non-blocking.
- **Test Failure**: `tests/test_chinese_column_bug.py` has one pre-existing failure unrelated to this refactor.

## Next Steps
- Address documented type errors incrementally.
- Fix the pre-existing test failure in `test_chinese_column_bug.py`.
