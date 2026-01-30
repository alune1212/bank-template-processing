# Plan: Custom Output Filename with Stats

## TL;DR
> **Quick Summary**: Change output filename format to include row count and total amount, removing the timestamp. Requires refactoring `main.py` to calculate stats *after* data transformation but *before* filename generation.
>
> **Deliverables**:
> - Modified `src/bank_template_processing/main.py` (execution order change)
> - Modified `generate_output_filename` signature and logic
> - New helper `_calculate_stats` in `main.py`
>
> **Estimated Effort**: Medium (due to refactoring execution flow)
> **Parallel Execution**: NO (sequential refactoring)
> **Critical Path**: Refactor Flow -> Implement Stats -> Update Filename

---

## Context

### Original Request
Change output filename to format: `[UnitName]_[TemplateName]_[Count]_[Amount].xlsx`.
Specifics:
- Remove timestamp.
- Add "X人" (row count).
- Add "金额XXX.XX元" (sum of first amount column).
- Fallback template name: use template filename stem.

### Metis Review
**Identified Gaps** (addressed):
- **Execution Order**: Filename generation currently happens *before* transformation. Must move it to *after* transformation to get accurate float values for summation.
- **Zero Handling**: Treat non-numeric/empty values as 0 during summation.
- **Overwrite Risk**: Removing timestamp increases collision risk. Accepted as per user request.

---

## Work Objectives

### Core Objective
Update filename generation logic to include data statistics and exclude timestamp.

### Concrete Deliverables
- `src/bank_template_processing/main.py` updated with reordered logic.
- Filename format: `{unit_name}_{template_name}_{count}人_金额{amount:.2f}元.xlsx`

### Definition of Done
- [ ] Filename matches pattern: `*_3人_金额3245.87元.xlsx`
- [ ] Amount summation is accurate based on transformed values
- [ ] Timestamp is removed
- [ ] Single and Multi template modes both work

### Must Have
- Auto-detection of amount column (first field with `transform="amount_decimal"`)
- Correct handling of mixed float/string types in data

### Must NOT Have (Guardrails)
- Do NOT sum untransformed string values (must use transformed floats)
- Do NOT include timestamp

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: Yes (pytest)
- **User wants tests**: Yes (TDD approach recommended for logic changes)
- **Framework**: pytest

### TDD Enabled

**Task Structure:**
1. **RED**: Write failing test for filename generation with stats
2. **GREEN**: Implement `calculate_stats` and update flow
3. **REFACTOR**: Clean up `main.py`

### Automated Verification

**For Filename Verification** (using Bash):
```bash
# Agent executes:
uv run bank-process tests/fixtures/input.xlsx "TestUnit" "01" --output-dir output_test
ls output_test/
# Assert: File exists matching pattern "TestUnit_Example_3人_金额*.xlsx"
```

---

## Execution Strategy

### Parallel Execution Waves

Sequential execution required due to dependency on `main.py` refactoring.

### Agent Dispatch Summary

| Wave | Tasks | Recommended Agents |
|------|-------|-------------------|
| 1 | 1 | delegate_task(category="quick", load_skills=["git-master"]) |
| 2 | 2 | delegate_task(category="quick", load_skills=["git-master"]) |
| 3 | 3 | delegate_task(category="quick", load_skills=["git-master"]) |

---

## TODOs

- [ ] 1. Create failing test for new filename format

  **What to do**:
  - Create `tests/test_filename_stats.py`
  - Mock data and config
  - Test `generate_output_filename` with new args (count, amount)
  - Test `_calculate_stats` logic

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`git-master`]

  **Parallelization**: NO

  **References**:
  - `src/bank_template_processing/main.py` - Current logic

  **Acceptance Criteria**:
  - [ ] Test fails because function signature doesn't match yet

- [ ] 2. Implement `_calculate_stats` and update `generate_output_filename`

  **What to do**:
  - Add `_calculate_stats(data, field_mappings)` to `main.py`
    - Iterate `field_mappings` to find `transform="amount_decimal"`
    - Sum that column from `data` (handle missing/non-float as 0)
    - Return `(count, total_amount)`
  - Update `generate_output_filename` signature to accept `count`, `amount`
  - Remove timestamp generation from `generate_output_filename`
  - Update format string: `f"{unit_name}_{template_name}_{count}人_金额{amount:.2f}元{ext}"`

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`git-master`]

  **Parallelization**: NO

  **Acceptance Criteria**:
  - [ ] `_calculate_stats` correctly sums float values
  - [ ] `generate_output_filename` produces correct string

- [ ] 3. Refactor `main.py` execution flow

  **What to do**:
  - In `main()` (Single Template path):
    - Move `generate_output_filename` call to *after* `_transform_data`
    - Call `_calculate_stats` using transformed data
  - In `main()` (Multi Template logic block - lines 380+):
    - Move `generate_output_filename` call to *after* `_transform_data`
    - Call `_calculate_stats` using transformed data
  - Ensure `template_name` fallback (use stem) logic is preserved/enhanced

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`git-master`]

  **Parallelization**: NO

  **Acceptance Criteria**:
  - [ ] `uv run pytest tests/test_filename_stats.py` passes
  - [ ] Integration test: Run CLI and verify actual file output name

---

## Success Criteria

### Verification Commands
```bash
uv run pytest tests/test_filename_stats.py
```

### Final Checklist
- [ ] Filename contains "X人"
- [ ] Filename contains "金额XXX.XX元"
- [ ] Timestamp is gone
- [ ] Existing functionality (Excel generation) remains broken? NO, must work.
