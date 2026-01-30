# Type Checking Issues Documented

## 2026-01-30: Initial Type Checking with Ty

### Summary
Run `uv run ty check` found 15 type errors across the codebase. These are documented here for future resolution.

### Error Categories

#### 1. Invalid Type Assignment (Conditional Imports)
**File**: `src/bank_template_processing/excel_writer.py` (Lines 15, 16, 21, 26, 31)

**Issue**: Conditional import fallbacks assign `None` or custom Exception to typed variables

```python
try:
    from openpyxl.utils.exceptions import InvalidFileException
except ImportError:
    openpyxl = None  # Error: None not assignable to module type
    InvalidFileException = type("InvalidFileException", (Exception,), {})  # Error: type mismatch
```

**Impact**: Low - These are graceful fallbacks for optional dependencies. The code works at runtime but fails strict type checking.

**Resolution Strategy**: Use `Any` or `Optional` type annotations for these imports, or use `# type: ignore` comments.

---

#### 2. Subscript Assignment on Union Types
**File**: `skills/xlsx/recalc.py` (Line 135)

**Issue**: Attempting to assign to a dictionary subscript on a union type that includes `str` and `int`

```python
result["error_summary"][err_type] = {
    "count": len(locations),
    "locations": locations[:20],
}
```

**Type Error**: `result["error_summary"]` is typed as `Unknown | str | int | dict[Unknown, Unknown]`, and Ty can't verify it's always a dict.

**Impact**: Medium - This is in the `skills/` directory which may be legacy or auxiliary code.

**Resolution Strategy**: Add proper type annotations for `result["error_summary"]` or use `# type: ignore`.

---

#### 3. Dict Value Type Mismatches in Tests
**Files**:
- `tests/test_integration.py` (Lines 52, 299)
- `tests/test_config_loader.py` (Lines 169, 254, 278)

**Issue**: Tests assign incompatible types to dict values

**Example from `test_integration.py`**:
```python
row: dict[str, str]  # Expected to be str only
row[field_name] = float(result)  # Error: assigning float to str dict
```

**Example from `test_config_loader.py`**:
```python
config["organization_units"]  # Typed as str somewhere in the code
config["organization_units"]["test_unit"]["start_row"]  # Error: treating str as dict
```

**Impact**: Low - These are test files, not production code. Type mismatches in tests are less critical.

**Resolution Strategy**: Fix test data structures to match expected types, or use `# type: ignore` for test code.

---

#### 4. Function Argument Type Mismatches
**File**: `tests/test_integration.py` (Lines 305, 310)

**Issue**: Passing `list[dict[str, str]]` where `str` is expected

```python
# Function expects: template_name: str | None, template_path: str
filename = generate_output_filename("测试单位", "01", group_name, timestamp, template_path)
# Error: group_name and template_path are Any | list[dict[str, str]], not str

writer.write_excel(
    template_path=template_path,  # Error: expects str, got Any | list[dict[str, str]]
    ...
)
```

**Impact**: Low - Test code issue only.

**Resolution Strategy**: Fix test data or use `# type: ignore`.

---

### Overall Assessment

**Total Errors**: 15
- **Critical**: 0 (All code works at runtime)
- **High Priority**: 0
- **Medium Priority**: 1 (skills/xlsx/recalc.py - may need cleanup)
- **Low Priority**: 14 (Mostly conditional imports and test code)

**Recommendation**: 
1. Add type annotations or `# type: ignore` comments for conditional imports (graceful fallbacks are acceptable)
2. Fix the `skills/xlsx/recalc.py` error with proper type annotations
3. Ignore test file type errors or fix as part of test refactoring
4. Focus on production code quality; test type errors are secondary

**Status**: Documented for future resolution. The codebase passes all runtime tests; type errors are strict typing issues, not functional bugs.

---

## 2026-01-30: Ruff Standardization Complete

### Formatting Applied
- **Files reformatted**: 5
- **Files unchanged**: 18
- **Command**: `uv run ruff format .`

### Linting Applied
- **Initial errors found**: 20
- **Auto-fixed**: 17
- **Manually fixed**: 3
- **Final status**: All checks passed!

### Manual Fixes
1. **Unused variable in test**: Removed unused `file_path` variable in `tests/test_excel_reader.py` line 100
2. **Duplicate test methods**: Removed duplicate `test_apply_transformations_amount` and `test_apply_transformations_card_number` in `tests/test_main.py` (lines 452-472)

### Summary
✅ Code formatted consistently
✅ All lint errors resolved
✅ Ruff passes cleanly with `uv run ruff check .`
✅ Type errors documented but not blocking (15 non-critical type issues remain)

The project is now standardized with Ruff formatting and linting rules enforced.
