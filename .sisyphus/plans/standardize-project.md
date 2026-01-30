# Standardize Code and Project Structure

## TL;DR

> **Quick Summary**: Refactor project to standard `src/` layout, consolidate configuration into `pyproject.toml`, and modernize toolchain with Ruff and Ty (Astral).
> 
> **Deliverables**:
> - `src/bank_template_processing/` directory with all source code
> - Updated `pyproject.toml` (Ruff, Ty, Build System, Scripts)
> - Updated `bank_template_processing.spec` for PyInstaller
> - Refactored `main.py` (imports and path resolution)
> 
> **Estimated Effort**: Medium
> **Parallel Execution**: NO - sequential (atomic refactor)
> **Critical Path**: Config → Move Files → Fix Imports → Fix Build

---

## Context

### Original Request
Standardize code and project using Ruff and Ty, including moving to `src/` layout and consolidating configs.

### Interview Summary
**Key Discussions**:
- **Tools**: Migrate from Mypy to Ty (Astral); use Ruff for lint/format.
- **Layout**: Adopt standard `src/` layout.
- **Config**: Consolidate `pytest.ini` and tool configs into `pyproject.toml`.

**Research Findings**:
- **Ty**: Astral's new Rust-based type checker (confirmed via Context7).
- **Build**: Uses `pyinstaller` via `scripts/build_windows.ps1`.
- **Risks**: `main.py` relies on `__file__` for path resolution, which breaks when moving to `src/`.

### Metis Review
**Identified Gaps** (addressed):
- **Path Logic**: `main.py` must handle `src/` nesting in dev mode.
- **Build Spec**: `bank_template_processing.spec` needs path updates.
- **Ty Availability**: Proceeding based on Context7 findings.

---

## Work Objectives

### Core Objective
Modernize project structure and tooling for better maintainability and performance.

### Concrete Deliverables
- `src/bank_template_processing/` containing all modules.
- `pyproject.toml` with `[tool.ruff]`, `[tool.ty]`, `[project.scripts]`.
- Passing tests (`uv run pytest`).
- Working Windows build (`scripts/build_windows.ps1`).

### Definition of Done
- [ ] `uv run check` (or equivalent) passes with no errors.
- [ ] `uv run pytest` passes.
- [ ] `dist/bank-template-processing/bank-template-processing.exe` is generated and runs.

### Must Have
- `src/` layout.
- `pyproject.toml` as single source of config.
- `ty` replacing `mypy`.

### Must NOT Have (Guardrails)
- Do NOT modify `config.json` logic to look inside `src/`. It must stay in root.
- Do NOT delete `scripts/` (they are needed for build).

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: YES (`pytest`).
- **User wants tests**: YES (Maintain existing tests).
- **Framework**: `pytest`.

### Automated Verification Only
**Agent-Executable Verification**:
- **Code Structure**: `ls -R src/`
- **Lint/Type**: `uv run ruff check .`, `uv run ty check`
- **Tests**: `uv run pytest`
- **Build**: `powershell -ExecutionPolicy Bypass -File scripts/build_windows.ps1` (or simplified pyinstaller run)

---

## Execution Strategy

### Parallel Execution Waves
Sequential execution required due to massive file moves and inter-dependencies.

### Agent Dispatch Summary
- **Wave 1**: Config & Move (Quick/Git-Master)
- **Wave 2**: Fix Code & Imports (Refactor)
- **Wave 3**: Fix Tests & Build (QA)

---

## TODOs

- [x] 1. **Update Configuration (pyproject.toml)**
  
  **What to do**:
  - Remove `mypy`, add `ty`.
  - Add `hatchling` (or setuptools) to `[build-system]` to support `src` layout.
  - Move `pytest.ini` content to `[tool.pytest.ini_options]`.
  - Add `[project.scripts]`: `bank-process = "bank_template_processing.main:main"`.
  - Configure `[tool.ruff]`: line-length=120, target-version="py313".
  
  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`git-master`]
  
  **Verification**:
  ```bash
  cat pyproject.toml | grep "build-backend"
  # Expected: output contains hatchling or setuptools
  ```

- [x] 2. **Refactor to src/ Layout (Git Move)**
  
  **What to do**:
  - Create `src/bank_template_processing/__init__.py`.
  - Use `git mv` to move:
    - `main.py` -> `src/bank_template_processing/main.py`
    - `config_loader.py` -> `src/bank_template_processing/config_loader.py`
    - `excel_reader.py` -> `src/bank_template_processing/excel_reader.py`
    - `excel_writer.py` -> `src/bank_template_processing/excel_writer.py`
    - `transformer.py` -> `src/bank_template_processing/transformer.py`
    - `validator.py` -> `src/bank_template_processing/validator.py`
    - `template_selector.py` -> `src/bank_template_processing/template_selector.py`
  - Create `src/bank_template_processing/__main__.py` that imports/runs `main.py` (for `python -m`).

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`git-master`]
  
  **Verification**:
  ```bash
  ls src/bank_template_processing/main.py
  # Expected: file exists
  ```

- [x] 3. **Fix Imports and Path Logic (Source Code)**
  
  **What to do**:
  - Update `src/bank_template_processing/main.py`:
    - Fix imports: `from config_loader` -> `from .config_loader` (relative) OR `from bank_template_processing.config_loader` (absolute).
    - **CRITICAL**: Update `get_executable_dir()`:
      - If frozen: `sys.executable` (unchanged).
      - If dev: `Path(__file__).parents[2]` (was `.parent`).
      - Goal: Ensure it finds `config.json` in project root.
  - Update other modules' imports to be relative (`from . import ...`) or absolute.

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`git-master`]
  
  **Verification**:
  ```bash
  # Check import syntax
  grep "from \." src/bank_template_processing/*.py
  ```

- [x] 4. **Fix Test Imports**
  
  **What to do**:
  - Update `tests/*.py` imports.
  - `from main import ...` -> `from bank_template_processing.main import ...`
  - Ensure `pytest` can find the package (via `pyproject.toml` or `uv sync`).

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`git-master`]
  
  **Verification**:
  ```bash
  uv run pytest tests/test_config_loader.py
  # Expected: Tests pass (or at least imports succeed)
  ```

- [x] 5. **Update Build Spec (PyInstaller)**
  
  **What to do**:
  - Update `bank_template_processing.spec`:
    - `Analysis(['src/bank_template_processing/main.py'], ...)`
    - Update `pathex` if needed (include `src`).
    - Ensure `hiddenimports` are still valid.

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`git-master`]
  
  **Verification**:
  ```bash
  uv run pyinstaller bank_template_processing.spec --noconfirm
  ls dist/bank-template-processing/bank-template-processing.exe
  # Expected: File exists
  ```

- [x] 6. **Run Standardization Checks (Ruff & Ty)**
  
  **What to do**:
  - Run `uv run ruff format .`
  - Run `uv run ruff check . --fix`
  - Run `uv run ty check` (and fix/suppress errors).
  
  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`git-master`]
  
  **Verification**:
  ```bash
  uv run ruff check .
  # Expected: No errors
  ```

- [ ] 7. **Cleanup**
  
  **What to do**:
  - Remove `pytest.ini` (content moved).
  - Remove old `__pycache__` if present.

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`git-master`]

---

## Commit Strategy

| Task | Message | Files |
|------|---------|-------|
| 1 | `build: update pyproject.toml for src layout and tools` | `pyproject.toml` |
| 2 | `refactor: move code to src/bank_template_processing/` | `src/`, `*.py` |
| 3 | `fix: update imports and path resolution logic` | `src/**/*.py` |
| 4 | `test: fix test imports for src layout` | `tests/*.py` |
| 5 | `build: update pyinstaller spec for src layout` | `*.spec` |
| 6 | `style: apply ruff format and ty fixes` | `.` |
