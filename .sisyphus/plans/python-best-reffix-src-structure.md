# Python 最佳实践实施计划：bank-template-processing 项目（src 目录结构版）

## TL;DR

> **Quick Summary**: 为 bank-template-processing 项目创建 src/ 目录结构并配置现代 Python 工具链（uv, ruff, mypy），采用严格类型检查和全面优化策略，实现自动化代码质量保证。
>
> **Deliverables**:
> - src/ 目录结构（src/bank_template_processing/）
> - 更新后的 pyproject.toml（包含完整 ruff 和 mypy 配置，适配 src 结构）
> - Makefile（开发工作流自动化）
> - .pre-commit-config.yaml（Git hooks 自动化）
> - 更新后的 .gitignore
> - 所有 Python 模块迁移到 src/ 目录
> - 更新所有导入语句以适配新的包结构
> - 更新测试文件导入以适配新的包结构
> - 修复了所有 ruff 问题的代码
> - 完善类型注解（当前 40% 参数，目标 100%）
>
> **Estimated** Effort: Large（约 3-4 小时）
> **Parallel Execution**: YES - 5 waves
> **Critical Path**: 创建 src/ 目录 → 迁移模块 → 更新导入 → 更新 pyproject.toml → 修复 ruff 问题 → 添加类型注解 → 安装 pre-commit hooks

---

## Context

### Original Request

为 bank-template-processing 项目应用现代 Python 最佳实践，包括：
- 使用 uv 进行项目管理
- 使用 ruff 进行代码质量检查
- 使用 mypy 进行类型检查
- **按照 src 目录进行规范化管理**
- 完善项目结构、路径管理和打包指南

### Interview Summary

**Key Discussions**:
- **类型检查策略**: 选择"严格模式+忽略" - 立即启用 strict 模式，使用 # type: ignore 处理暂时问题
- **代码问题处理**: 选择"立即全部修复" - 配置工具后一次性修复所有 ruff 问题
- **Pre-commit 行为**: 选择"自动修复+阻塞" - 先自动修复，仍有错误则阻塞提交
- **CI/CD 集成**: 选择"仅本地工具" - 不创建 CI/CD 工作流
- **代码重构边界**: 选择"全面优化" - 添加类型注解时可重构代码结构
- **编辑器配置**: 选择"其他/不需要" - 不创建 VS Code 配置文件
- **项目结构**: 选择"创建 src/ 目录" - 采用 src/bank_template_processing/ 包结构进行规范化

**Research Findings**:
- 项目使用 Python 3.13（最新稳定版）
- 源代码 2,409 行，48 个函数，10 个类
- 当前类型注解覆盖：54% 返回类型，40% 参数类型
- 工具已安装：uv, ruff 0.14.14, mypy 1.19.1, pre-commit 4.5.1
- ruff 初步检查发现：F401（未使用导入）、F841（未使用变量）等问题
- mypy 在宽松模式下（--ignore-missing-imports）无错误

### Metis Review

**Identified Gaps** (addressed):
- **类型检查策略**: 已明确采用严格模式，# type: ignore 处理边界情况
- **Pre-commit 阻塞策略**: 已明确采用自动修复+阻塞模式
- **重构边界**: 已明确允许全面优化，但不破坏向后兼容性
- **范围防护**: 明确创建 src/ 目录结构，不添加 CI/CD，不创建编辑器配置

---

## Work Objectives

### Core Objective

为 bank-template-processing 项目建立完整的现代化 Python 开发环境，包括规范的 src/ 目录结构、严格的代码质量检查和类型安全保证，提升代码可维护性和团队协作效率。

### Concrete Deliverables

1. **src/ 目录结构** - 创建 src/bank_template_processing/ 包目录
2. **pyproject.toml** - 更新以包含完整 ruff 和 mypy 配置，适配 src/ 结构
3. **Makefile** - 创建简化开发工作流的命令接口
4. **.pre-commit-config.yaml** - 配置 Git commit 前自动检查
5. **.git**ignore** - 更新以包含工具生成的缓存文件
6. **模块迁移** - 将所有 Python 模块迁移到 src/bank_template_processing/
7. **导入更新** - 更新所有导入语句以适配新的包结构
8. **测试更新** - 更新测试文件导入以适配新的包结构
9. **代码修复** - 修复所有 ruff 发现的 F401、F841 等问题
10. **类型注解完善** - 为所有函数添加完整的类型注解（参数和返回值）
11. **文档更新** - 在 README.md 中添加开发工作流和包结构说明

### Definition of Done

- [ ] `uv run ruff check .` 运行无错误
- [ ] `uv run ruff format .` 成功格式化所有文件
- [ ] `uv run mypy . --strict` 运行无错误（允许 # type: ignore）
- [ ] `make lint` 成功运行并无错误
- [ ] `make format` 成功格式化代码
- [ ] `make type-check` 成功运行并无错误
- [ ] `make check` 运行所有检查并全部通过
- [ ] `make test` 所有测试通过
- [ ] `make run` 可以通过包方式运行项目
- [ ] `make install` 可以正确安装包
- [ ] `pre-commit install` 成功安装 hooks
- [ ] `pre-commit run --all-files` 在所有文件上成功运行
- [ ] 所有现有测试通过（无回归）

### Must Have

- ✅ src/bank_template_processing/ 目录结构
- ✅ src/bank_template_processing/__init__.py 包初始化文件
- ✅ pyproject.toml 配置使用 setuptools 和 src/ 目录
- ✅ pyproject.toml 配置包含完整的 ruff 和 mypy 配置
- ✅ ruff 配置包含全面的规则集（E, W, F, I, N, UP, B, C4, SIM, TCH, ANN, RUF）
- ✅ mypy 配置启用 strict 模式
- ✅ pre-commit hooks 配置为自动修复+阻塞
- ✅ Makefile 包含 lint, format, type-check, check, test, install, run 等命令
- ✅ .gitignore 包含 .mypy_cache, .ruff_cache, __pycache__, .venv
- ✅ 所有 Python 文件通过 ruff 检查
- ✅ 所有 Python 文件通过 mypy 检查（允许必要的 # type: ignore）
- ✅ 所有导入语句使用正确的包前缀 `bank_template_processing.`

### Must NOT Have (Guardrails)

- ❌ 不创建 VS Code 配置文件（.vscode/）
- ❌ 不创建 CI/CD 工作流（GitHub Actions 等）
- ❌ 不添加除 ruff, mypy, pre-commit 之外的工具
- ❌ 不重构与类型注解或 ruff 修复无关的代码
- ❌ 不破坏向后兼容性
- ❌ 不改变项目的主要接口（CLI 命令行接口保持不变）
- ❌ 不移动或修改配置文件、模板文件、文档文件
- ❌ 不一次性创建包含所有更改的单个大提交（保持原子化）

---

## Verification Strategy (MANDATORY)

### Test Decision

- **Infrastructure exists**: YES（pytest 已配置）
- **User wants tests**: Manual verification（使用现有测试验证无回归）

### Manual QA Only

由于项目已有完整的测试套件，本次工作的主要验证策略是：

**1. 运行现有测试确保无回归**

```bash
# 每次重大代码变更后运行
uv run pytest -v
```

**2. 工具配置验证**

| 工具 | 验证命令 | 预期输出 |
|------|----------|----------|
| ruff lint | `uv run ruff check .` | 无错误 |
| ruff format | `uv run ruff format --check .` | 无变更或已格式化 |
| mypy | `uv run mypy . --strict` | 无错误（允许 # type: ignore） |
| pytest | `uv run pytest -v` | 所有测试通过 |
| pre-commit | `pre-commit run --all-files` | 所有 hooks 通过 |

**3. Makefile 命令验证**

| 命令 | 验证内容 |
|------|----------|
| `make format` | 格式化所有 Python 文件 |
| `make lint` | 运行 ruff 检查 |
| `make type-check` | 运行 mypy 检查 |
| `make check` | 运行 format + lint + type-check |
| `make test` | 运行所有测试 |
| `make run` | 通过包方式运行 CLI |
| `make install` | 安装包到当前环境 |

**4. 包结构验证**

| 验证项 | 命令 | 预期输出 |
|----------|------|----------|
| 包目录存在 | `ls src/bank_template_processing/` | 显示模块文件 |
| 包可导入 | `python -c "from bank_template_processing import main"` | 无导入错误 |
| CLI 可运行 | `python -m bank_template_processing.main --help` | 显示帮助信息 |

**Evidence Required:**
- [ ] ruff check 输出（应无错误）
- [ ] mypy 输出（应无错误）
- [ ] pytest 输出（应显示所有测试通过）
- [ ] pre-commit run 输出（应显示所有 hooks 通过）
- [ ] Makefile 各命令成功执行的终端输出
- [ ] 包运行方式验证输出

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 0 (Start Immediately):
└── Task 0: 创建 src/ 目录结构

Wave 1 (After Wave 0):
├── Task 1: 迁移 Python 模块到 src/bank_template_processing/
└── Task 2: 创建 src/bank_template_processing/__init__.py

Wave 2 (After Wave 1):
├── Task 3: 更新主模块的导入语句
└── Task 4: 更新测试文件的导入语句

Wave 3 (After Wave 2):
├── Task 5: 更新 pyproject.toml 配置
└── Task 6: 创建 Makefile

Wave 4 (After Wave 3):
├── Task 7: 运行 ruff format 格式化代码
├── Task 8: 运行 ruff check --fix 修复问题
├── Task 9: 创建 .pre-commit-config.yaml
└── Task 10: 更新 .gitignore

Wave 5 (After Wave 4):
├── Task 11: 添加类型注解到所有函数
├── Task 12: 运行 mypy 验证类型安全
└── Task 13: 运行 pytest 验证无回归

Wave 6 (After Wave 5):
├── Task 14: 安装 pre-commit hooks
└── Task 15: 更新 README.md 文档
```

### Dependency Matrix

| Task | Depends On | Blocks | Can Parallelize With |
|------|------------|--------|---------------------|
| 0 | None | 1, 2 | None |
| 1 | 0 | 3 | 2 |
| 2 | 0 | None | 1 |
| 3 | 1 | 5 | 4 |
| 4 | 1 | 5 | 3 |
| 5 | 3, 4 | 7 | 6 |
| 6 | None | 7 | 5 |
| 7 | 5 | 11 | 8, 9, 10 |
| 8 | 5, 7 | 11 | 9, 10 |
| 9 | None | 14 | 7, 8, 10 |
| 10 | None | 14 | 7, 8, 9 |
| 11 | 7, 8 | 12, 13 | None |
| 12 | 11 | 13, 14 | None |
| 13 | 5, 12 | 15 | None |
| 14 | 9, 10, 12 | 15 | None |
| 15 | 13, 14 | None | None (final) |

Critical Path: Task 0 → Task 1 → Task 3 → Task 5 → Task 7 → Task 11 → Task 12 → Task 14 → Task 15

---

## TODOs

- [ ] 0. 创建 src/ 目录结构

  **What to do**:
  - 创建 `src/` 目录
  - 在 src/ 下创建 `bank_template_processing/` 包目录
  - 确保目录结构为：`src/bank_template_processing/`

  **Must NOT do**:
  - 不创建其他子目录（只创建包目录）
  - 不删除或移动任何现有文件

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: 创建目录结构是简单的文件系统操作
  - **Skills**: [`quick`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 0 (start immediately)
  - **Blocks**: Tasks 1, 2
  - **Blocked By**: None

  **References** (CRITICAL - - Be Exhaustive):

  **External References**:
  - https://packaging.python.org/en/latest/guides/modern-python/ - Python 包结构最佳实践

  **Acceptance Criteria**:

  - [ ] src/ 目录存在
  - [ ] src/bank_template_processing/ 目录存在
  - [ ] 目录为空或仅包含未来会创建的 __init__.py

  **Manual Execution Verification**:

  - [ ] 验证目录结构：
    ```bash
    ls -la src/bank_template_processing/
    # 预期: 目录存在，可能为空或只有 __init__.py
    ```

  **Evidence Required**:
  - [ ] 目录结构（ls 输出）

  **Commit**: YES
  - Message: `refactor: create src/ directory structure for package layout`
  - Files: `src/bank_template_processing/` (directory)
  - Pre-commit: 不适用

---

- [ ] 1. 迁移 Python 模块到 src/bank_template_processing/

  **What to do**:
  - 将以下文件移动到 `src/bank_template_processing/`：
    - `main.py`
    - `config_loader.py`
    - `excel_reader.py`
    - `excel_writer.py`
    - `transformer.py`
    - `validator.py`
    - `template_selector.py`
  - 保持文件内部结构不变

  **Must NOT do**:
  - 不修改文件内容（只是移动文件）
  - 不移动测试文件、配置文件、模板文件
  - 不移动非 Python 文件（README.md, LICENSE 等）

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: 文件移动是直接的操作，风险低
  - **Skills**: [`quick`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential (after Task 0)
  - **Blocks**: Tasks 3, 4
  - **Blocked By**: Task 0

  **References** (CRITICAL - Be Exhaustive):

  **Pattern References** (existing code to follow):
  - `main.py` - CLI 入口文件
  - `config_loader.py` - 配置加载模块
  - `excel_reader.py` - Excel 读取模块
  - `excel_writer.py` - Excel 写入模块
  - `transformer.py` - 数据转换模块
  - `validator.py` - 数据验证模块
  - `template_selector.py` - 模板选择模块

  **Acceptance Criteria**:

  - [ ] 所有 Python 模块文件在 src/bank_template_processing/ 目录中
  - [ ] 根目录不再有这些 .py 文件
  - [ ] 文件数量正确（8 个模块文件）

  **Manual Execution Verification**:

  - [ ] 验证文件迁移：
    ```bash
    ls src/bank_template_processing/*.py
    # 预期: 显示所有 8 个模块文件

    ls *.py 2>/dev/null
    # 预期: 无输出（所有文件已移动）
    ```

  - [ ] 检查 git 状态：
    ```bash
    git status
    # 预期: 显示文件移动（renamed 消息）
    ```

  **Evidence Required**:
  - [ ] src/bank_template_processing/ 目录内容（ls 输出）
  - [ ] git status 命令输出

  **Commit**: YES
  - Message: `refactor: move Python modules to src/bank_template_processing/`
  - Files: 所有移动的 .py 文件
  - Pre-commit: 不适用

---

- [ ] 2. 创建 src/bank_template_processing/__init__.py

  **What to do**:
  - 创建 `src/bank_template_processing/__init__.py` 文件
  - 设置包的 `__version__` 变量为项目版本号（"0.1.0"）
  - 添加基本的包文档字符串（可选）

  **Must NOT do**:
  - 不创建其他文件
  - 不添加不必要的导入或代码

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: 创建 __init__.py 是标准的包初始化
  - **Skills**: [`quick`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 1 (with Task 1)
  - **Blocks**: None
  - **Blocked By**: Task 0

  **References** (CRITICAL - Be Exhaustive):

  **External References**:
  - https://packaging.python.org/en/latest/guides/modern-python/ - Python 包初始化最佳实践

  **Acceptance Criteria**:

  - [ ] __init__.py 文件存在
  - [ ] 包含 __version__ 变量
  - [ ] __version__ 值与 pyproject.toml 中的版本号一致

  **Manual Execution Verification**:

  - [ ] 验证包初始化：
    ```bash
    cat src/bank_template_processing/__init__.py
    # 预期: 显示 __version__ = "0.1.0" 等

    python -c "from bank_template_processing import __version__; print(__version__)"
    # 预期: 打印包版本号 0.1.0
    ```

  **Evidence Required**:
  - [ ] __init__.py 文件内容
  - [ ] 版本号验证命令输出

  **Commit**: YES
  - Message: `refactor: add package __init__.py with version info`
  - Files: `src/bank_template_processing/__init__.py`
  - Pre-commit: 不适用

---

- [ ] 3. 更新主模块的导入语句

  **What to do**:
  - 更新 `src/bank_template_processing/main.py` 的导入语句：
    - 将同级导入改为包内导入
    - 示例：`from config_loader import load_config` → `from bank_template_processing.config_loader import load_config`
  - 更新所有模块文件中的相互导入：
    - 检查每个模块的 import 语句
    - 将相对导入改为包内导入
    - 确保导入使用新的包名 `bank_template_processing`
  - 保留第三方库导入（openpyxl, xlrd, xlwt, logging, json 等）不变

  **Must NOT do**:
  - 不修改第三方库导入
  - 不修改标准库导入
  - 不更改导入顺序（由 ruff 排序）
  - 不修改其他逻辑代码

  **Recommended Agent Profile**:
  - **Category**: `ultrabrain`
    - Reason: 需要深入理解模块依赖关系，正确更新导入
  - **Skills**: `[]` (不依赖特殊技能，需要代码理解)

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential (after Task 1)
  - **Blocks**: Task 5
  - **Blocked By**: Task 1

  **References** (CRITICAL - Be Exhaustive):

  **Pattern References** (existing code to follow):
  - `src/bank_template_processing/main.py` - 查看现有的导入模式
  - `src/bank_template_processing/config_loader.py` - 查看如何与其他交互
  - `src/bank_template_processing/excel_reader.py` - 查看模块间依赖
  - `src/bank_template_processing/excel_writer.py` - 查看模块间依赖
  - `src/bank_template_processing/transformer.py` - 查看模块间依赖
  - `src/bank_template_processing/validator.py` - 查看模块间依赖
  - `src/bank_template_processing/template_selector.py` - 查看模块间依赖

  **Acceptance Criteria**:

  - [ ] 所有模块间导入都使用 `bank_template_processing.` 前缀
  - [ ] 不再有同级相对导入（`from config_loader import...`）
  - [ ] 代码可以正常导入（无循环依赖）
  - [ ] 运行 `python -m bank_template_processing.main --help` 无导入错误

  **Manual Execution Verification**:

  - [ ] 验证导入语法：
    ```bash
    python -m py_compile src/bank_template_processing/*.py
    # 预期: 无语法错误
    ```

  - [ ] 测试 CLI 可运行：
    ```bash
    python -m bank_template_processing.main --help
    # 预期: 显示帮助信息（导入正确）
    ```

  **Evidence Required**:
  - [ ] 更新后的文件内容（git diff）
  - [ ] Python 编译检查输出
  - [ ] CLI 帮助命令输出

  **Commit**: YES
  - Message: `refactor: update imports in main modules for src/ package structure`
  - Files: 所有被更新的 .py 文件
  - Pre-commit: 不适用

---

- [ ] 4. 更新测试文件的导入语句

  **What to do**:
  - 更新 `tests/` 目录下所有测试文件的导入语句：
    - `test_config_loader.py` - 更新导入
    - `test_excel_reader.py` - 更新导入
    - `test_excel_writer.py` - 更新导入
    - `test_main.py` - 更新导入
    - `test_transformer.py` - 更新导入
    - `test_validator.py` - 更新导入
    - `test_template_selector.py` - 更新导入
    - `test_integration.py` - 更新导入
    - `test_example.py` - 更新导入
  - 将所有导入改为从 `bank_template_processing` 包导入
  - 示例：`from config_loader import ConfigError` → `from bank_template_processing.config_loader import ConfigError`

  **Must NOT do**:
  - 不修改测试逻辑（只更新导入）
  - 不修改 pytest fixtures（除非导入被破坏）
  - 不添加或删除测试用例

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: 需要仔细更新测试导入，确保所有测试都能运行
  - **Skills**: `[]` (需要代码理解)

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential (after Task 1)
  - **Blocks**: Task 5
  - **Blocked By**: Task 1

  **References** (CRITICAL - Be Exhaustive):

  **Pattern References** (existing code to follow):
  - `tests/test_config_loader.py` - 现有测试导入模式
  - `tests/test_main.py` - 现有测试导入模式
  - `pytest.ini` - 测试配置文件

  **Acceptance Criteria**:

  - [ ] 所有测试文件导入都使用 `bank_template_processing.` 前缀
  - [ ] 测试可以运行（pytest 可以发现测试用例）
  - [ ] 所有测试都能导入测试的模块

  **Manual Execution Verification**:

  - [ ] 运行测试：
    ```bash
    uv run pytest -v
    # 预期: 所有测试通过（或只有被测试逻辑破坏的失败）
    ```

  - [ ] 检查测试发现：
    ```bash
    uv run pytest --collect-only
    # 预期: 显示所有测试用例（导入正确）
    ```

  **Evidence Required**:
  - [ ] 更新后的测试文件（git diff）
  - [ ] pytest 收集测试输出
  - [ ] pytest 运行输出

  **Commit**: YES
  - Message: `refactor: update test imports for src/ package structure`
  - Files: `tests/*.py`
  - Pre-commit: 不适用

---

- [ ] 5. 更新 pyproject.toml 配置

  **What to do**:
  - 添加 [tool.ruff] 配置节
    - 设置 line-length = 100
    - 配置 [tool.ruff.lint] 规则（E, W, F, I, N, UP, B, C4, SIM, TCH, ANN, RUF）
    - 忽略 ANN101, ANN102, ANN001, ANN002, ANN003（渐进式）
    - 配置 [tool.ruff.lint.per-file-ignores]（tests/ 和 __init__.py）
  - 添加 [tool.mypy] 配置节
    - 设置 python_version = "3.13"
    - 启用 strict = true
    - 配置 strict 模式的各种选项
    - 添加 [[tool.mypy.overrides]] 处理第三方库和测试文件
  - 更新 [project.optional-dependencies] 确保包含 ruff, mypy, pre-commit
  - 添加 [project.scripts] 配置 CLI 入口点：
    - 设置 `bank-template = "bank_template_processing.main:main"`
  - 更新 [build-system] 配置：
    - 设置 `requires = ["setuptools"]`
    - 设置 `build-backend = "setuptools.build_meta"`
  - 添加 [tool.setuptools.packages.find] 配置：
    - 设置 `where = ["src"]`
  - 确保 name 和 version 等元数据保持不变

  **Must NOT do**:
  - 不修改项目元数据（name, version, description 等）
  - 不更改生产依赖项（不添加新库）
  - 不启用过于严格或不必要的 ruff 规则
  - 不创建新的配置节（只添加必要的 tool.*）

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: 配置文件更新需要理解多种工具的配置语法和最佳实践
  - **Skills**: [`unspecified-high`]
    - No specific skills needed - standard file editing

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential (after Tasks 3, 4)
  - **Blocks**: Tasks 7
  - **Blocked By**: Tasks 3, 4

  **References** (CRITICAL - Be Exhaustive):

  **Pattern References** (existing code to follow):
  - `pyproject.toml` lines 1-25 - 现有项目配置结构
  - `/Users/alune/Documents/code/bank-template-processing/pyproject.toml` - 当前配置文件

  **API/Type References** (contracts to implement against):
  - https://docs.astral.sh/ruff/settings/ - Ruff 配置 API 参考
  - https://mypy.readthedocs.io/en/stable/config_file.html - MyPy 配置 API 参考

  **Test References** (testing patterns to follow):
  - 不适用（配置文件）

  **Documentation References** (specs and requirements):
  - https://packaging.python.org/en/latest/specifications/pyproject-toml/ - pyproject.toml 规范

  **External References** (libraries and frameworks):
  - https://docs.astral.sh/ruff/ - Ruff 官方文档
  - https://mypy.readthedocs.io/ - MyPy 官方文档

  **WHY Each Reference Matters**:
  - 现有 pyproject.toml: 了解当前项目结构，避免破坏性更改
  - Ruff 文档: 确保配置语法正确，规则集合理
  - MyPy 文档: 确保 strict 模式配置正确，不会过于严格导致无法通过

  **Acceptance Criteria**:

  - [ ] pyproject.toml 文件更新
  - [ ] [tool.ruff] 节存在且配置正确
  - [ ] [tool.mypy] 节存在且配置正确
  - [ ] [tool.setuptools.packages.find] 节存在且 where = ["src"]
  - [ ] [project.scripts] 节存在且配置正确
  - [ ] `uv run ruff check .` 可以运行（输出内容不重要，重要的是不报配置错误）
  - [ ] `uv run mypy . --strict` 可以运行（允许有类型错误，重要的是不报配置错误）

  **Manual Execution Verification**:

  - [ ] 运行配置验证：
    ```bash
    uv run ruff check --help
    # 预期: 显示 ruff 帮助信息，证明配置被识别

    uv run mypy --help
    # 预期: 显示 mypy 帮助信息，证明配置被识别
    ```

  - [ ] 检查配置文件语法：
    ```bash
    python -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb'))"
    # 预期: 无错误（TOML 语法正确）
    ```

  - [ ] 验证包结构配置：
    ```bash
    python -c "import setuptools; print(setuptools.setup(find_packages(where=['src'])))"
    # 预期: 找到 bank_template_processing 包
    ```

  **Evidence Required**:
  - [ ] pyproject.toml 更新后的内容（可使用 git diff 查看）
  - [ ] ruff 和 mypy 帮助命令的成功输出
  - [ ] 包发现命令输出

  **Commit**: YES
  - Message: `chore: add ruff and mypy configuration and update for src/ structure`
  - Files: `pyproject.toml`
  - Pre-commit: `uv run pytest -v`

---

- [ ] 6. 创建 Makefile

  **What to do**:
  - 创建 Makefile 文件
  - 添加以下 targets:
    - `help`: 显示所有可用命令
    - `install`: 运行 uv sync --all-extras
    - `format`: 运行 uv run ruff format .
    - `lint`: 运行 uv run ruff check .
    - `type-check`: 运行 uv run mypy . --strict
    - `check`: 运行 format + lint + type-check
    - `test`: 运行 uv run pytest -v
    - `run`: 运行 python -m bank_template_processing.main
    - `test-fast`: 运行 uv run pytest -v --no-cov
    - `test-cov`: 运行 uv run pytest --cov=. --cov-report=term-missing -- --cov-report=html
    - `clean`: 清理缓存目录
    - `ci`: 运行 check + test-cov
    - `all`: 运行 install + check + test
  - 每个命令添加友好的帮助文本

  **Must NOT do**:
  - 不添加与工具无关的命令（如 build, deploy 等）
  - 不创建依赖系统特定的 Makefile 规则
  - 不添加需要额外依赖的命令

  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
    - Reason: Makefile 创建是直接的文件写入，复杂度低
  - **Skills**: [`unspecified-low`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential (after Task 2)
  - **Blocks**: Tasks 7
  - **Blocked By**: Task 2

  **References** (CRITICAL - Be Exhaustive):

  **Pattern References**:
  - 不适用（新文件）

  **API/Type References**:
  - GNU Make 文档: https://www.gnu.org/software/make/manual/

  **External References**:
  - Python 项目 Makefile 最佳实践示例

  **WHY Each Reference Matters**:
  - GNU Make 文档: 确保 Makefile 语法正确，跨平台兼容

  **Acceptance Criteria**:

  - [ ] Makefile 文件创建
  - [ ] `make help` 显示所有命令
  - [ ] `make format` 成功运行
  - [ ] `make lint` 成功运行
  - [ ] `make type-check` 成功运行
  - [ ] `make check` 成功运行所有检查
  - [ ] `make test` 成功运行所有测试
  - [ ] `make run` 成功运行 CLI（使用包方式）
  - [ ] `make install` 成功安装包

  **Manual Execution Verification**:

  - [ ] 测试每个命令：
    ```bash
    make help
    # 预期: 显示所有可用命令列表

    make format
    # 预期: 格式化所有 Python 文件，无错误

    make lint
    # 预期: 运行 ruff 检查，可能有错误（任务8会修复）

    make type-check
    # 预期: 运行 mypy 检查，可能有类型错误（任务11会修复）

    make test
    # 预期: 运行所有测试，应该通过

    make run -- input.xlsx "单位名称" 01
    # 预期: CLI 正常运行（包方式）
    ```

  **Evidence Required**:
  - [ ] Makefile 文件内容
  - [ ] `make help` 命令输出
  - [ ] 各命令的成功执行截图或输出

  **Commit**: YES
  - Message: `chore: add Makefile for development workflow automation`
  - Files: `Makefile`
  - Pre-commit: `uv run pytest -v`

---

- [ ] 7. 运行 ruff format 格式化代码

  **What to do**:
  - 运行 `uv run ruff format .` 格式化所有 Python 文件
  - 检查格式化结果
  - 确保格式化后的代码仍然可运行

  **Must NOT do**:
  - 不使用其他格式化工具（black, isort 等）
  - 不忽略任何文件（应该格式化所有 .py 文件）

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: 单个命令执行，快速且直接
  - **Skills**: [`quick`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential (after Task 5)
  - **Blocks**: Task 11
    - **Blocked By**: Tasks 5, 6

  **References** (CRITICAL - Be Exhaustive):

  **External References**:
  - https://docs.astral.sh/ruff/formatters/ - Ruff formatter 文档

  **Acceptance Criteria**:

  - [ ] 所有 Python 文件被格式化
  - [ ] `uv run ruff format --check .` 显示无变更（已完全格式化）
  - [ ] 格式化后代码可运行（验证：uv run pytest -v 通过）

  **Manual Execution Verification**:

  - [ ] 运行格式化：
    ```bash
    uv run ruff format .
    # 预期: 格式化输出，显示哪些文件被修改

    uv run ruff format --check .
    # 预期: 显示 "No files were changed" 或类似消息
    ```

  - [ ] 验证代码可运行：
    ```bash
    uv run pytest -v
    # 预期: 所有测试通过
    ```

  **Evidence Required**:
  - [ ] ruff format 命令输出
  - [ ] ruff format --check 命令输出
  - [ ] pytest 成功输出

  **Commit**: YES
  - Message: `style: format code with ruff`
  - Files: 所有被修改的 .py 文件
  - Pre-commit: `uv run pytest -v`

---

- [ ] 8. 运行 ruff check --fix 修复问题

  **What to do**:
  - 运行 `uv run ruff check --fix .` 自动修复可修复的问题
  - 检查修复结果
  - 手动修复需要手动处理的问题（如果有）
  - 重点修复：F401（未使用导入）、F841（未使用变量）

  **Must NOT do**:
  - 不使用 # noqa 忽略所有问题
  - 不手动删除被 ruff 修复为未使用但实际上有用的代码（需要审查）

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: 命令执行，可能需要手动审查
  - **Skills**: [`quick`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential (after Task 7)
  - **Blocks**: Task 11
  - **Blocked By**: Tasks 5, 6, 7

  **References** (CRITICAL - Be Exhaustive):

  **External References**:
  - https://docs.astral.sh/ruff/rules/ - Ruff 规则列表

  **Acceptance Criteria**:

  - [ ] 所有 F401（未使用导入）问题被修复
  - [ ] 所有 F841（未使用变量）问题被修复
  - [ ] `uv run ruff check .` 运行无错误或仅有需要手动审查的问题
  - [ ] 修复后代码可运行（验证：uv run pytest -v 通过）

  **Manual Execution Verification**:

  - [ ] 运行自动修复：
    ```bash
    uv run ruff check --fix .
    # 预期: 显示修复的问题，可能仍有部分需要手动处理

    uv run ruff check .
    # 预期: 显示剩余问题（应该很少或没有）
    ```

  - [ ] 验证代码可运行：
    ```bash
    uv run pytest -v
    # 预期: 所有测试通过
    ```

  **Evidence Required**:
  - [ ] ruff check --fix 命令输出
  - [ ] ruff check 命令输出（显示修复后状态）
  - [ ] pytest 成功输出

  **Commit**: YES
  - Message: `fix: resolve ruff linting issues (unused imports, unused variables)`
  - Files: 所有被修复的 .py 文件
  - Pre-commit: `uv run pytest -v`

---

- [ ] 9. 创建 .pre-commit-config.yaml

  **What to do**:
  - 创建 .pre-commit-config.yaml 文件
  - 添加 ruff-pre-commit repo
    - Hook: ruff (使用 --fix, --exit-non-zero-on-fix)
    - Hook: ruff-format
  - 添加 mypy repo
    - Hook: mypy (使用 --ignore-missing-imports)
  - 配置适当的版本号（与 pyproject.toml 中的版本一致）

  **Must NOT do**:
  - 不添加其他 pre-commit hooks（除非必要）
  - 不配置过于复杂的 hooks
  - 不使用过期的 pre-commit hook 版本

  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
    - Reason: 配置文件创建，直接且标准
  - **Skills**: [`unspecified-low`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Tasks 7, 8, 10)
    - **Blocked By**: Task 14
  - **Blocked By**: None

  **References** (CRITICAL - Be Exhaustive):

  **External References**:
  - https://pre-commit.com/ - pre-commit 官方文档
  - https://github.com/astral-sh/ruff-pre-commit - ruff pre-commit hook
  - https://github.com/pre-commit/mirrors-mypy - mypy pre-commit hook

  **Acceptance Criteria**:

  - [ ] .pre-commit-config.yaml 文件创建
  - [ ] 配置包含 ruff pre-commit hook
  - [ ] 配置包含 ruff-format pre-commit hook
  - [ ] 配置包含 mypy pre-commit hook
  - [ ] `pre-commit validate` 命令成功运行

  **Manual Execution Verification**:

  - [ ] 验证配置：
    ```bash
    pre-commit validate
    # 预期: 显示 "Configuration is valid" 或类似消息
    ```

  - [ ] 测试 hooks（稍后在 Task 14 安装后）：
    ```bash
    pre-commit run --all-files
    # 预期: 运行所有 hooks，通过或显示需要修复的问题
    ```

  **Evidence Required**:
  - [ ] .pre-commit-config.yaml 文件内容
  - [ ] pre-commit validate 命令成功输出

  **Commit**: YES
  - Message: `chore: add pre-commit configuration for automated checks`
  - Files: `.pre-commit-config.yaml`
  - Pre-commit: 不适用（pre-commit 还未安装）

---

- [ ] 10. 更新 .gitignore

  **What to do**:
  - 取消注释以下行：
    - `#uv.lock` → `uv.lock`
    - `#.python-version` → `.python-version`
  - 确保以下模式存在（如果没有）：
    - `.mypy_cache/`
    - `.ruff_cache/`
    - `__pycache__/`
    - `.venv/`
  - 确保不忽略 src/ 目录（需要版本控制）

  **Must NOT do**:
  - 不添加不必要的忽略模式
  - 不忽略项目文件（如 .py, .json 源文件）
  - 不忽略配置文件（如 pyproject.toml）

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: 简单的文件编辑，取消注释
  - **Skills**: [`quick`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Tasks 7, 8, 9)
    - **Blocked By**: Task 14
  - **Blocked By**: None

  **References** (CRITICAL - Be Exhaustive):

  **Pattern References**:
  - `.gitignore` lines 88 and 101 - uv.lock 和 .python-version 注释位置

  **Acceptance Criteria**:

  - [ ] .gitignore 更新
  - [ ] uv.lock 取消注释
  - [ ] .python-version 取消注释
  - [ ] .mypy_cache/ 存在
  - [ ] .ruff_cache/ 存在
  - [ ] `git status` 显示 uv.lock 和 .python-version 为已跟踪文件

  **Manual Execution Verification**:

  - [ ] 检查 git 状态：
    ```bash
    git status
    # 预期: 显示 uv.lock 和 .python-version 为已跟踪（如果有更改）
    ```

  - [ ] 验证忽略模式：
    ```bash
    git check-ignore -v .mypy_cache/ .ruff_cache/
    # 预期: 显示这些路径被忽略
    ```

  **Evidence Required**:
  - [ ] .gitignore 更新后的内容（git diff）
  - [ ] git status 命令输出

  **Commit**: YES
  - Message: `chore: update .gitignore for tooling and reproducibility`
  - Files: `.gitignore`
  - Pre-commit: 不适用

---

- [ ] 11. 添加类型注解到所有函数

  **What to do**:
  - 为所有缺少类型注解的函数添加完整的类型注解
  - 优先处理公共 API 和核心业务逻辑函数
  - 为复杂类型创建类型别名（可选，全面优化）
  - 使用 typing 模块的类型注解（Optional, List, etc.）
  - 对于暂时无法类型化的代码，添加 # type: ignore 并注释原因
  - 可能重构函数签名以支持更好的类型注解（全面优化允许）

  **重点文件及函数**（根据调研）：
  - src/bank_template_processing/main.py: CLI 函数和 main()
  - src/bank_template_processing/config_loader.py: load_config(), validate_config(), get_unit_config()
  - src/bank_template_processing/excel_reader.py: ExcelReader 类的所有方法
  - src/bank_template_processing/excel_writer.py: ExcelWriter 类的所有方法
  - src/bank_template_processing/transformer.py: Transformer 类的所有方法
  - src/bank_template_processing/validator.py: Validator 类的所有方法
  - src/bank_template_processing/template_selector.py: TemplateSelector 类的所有方法

  **Must NOT do**:
  - 不破坏函数签名的向后兼容性（除非必要且测试更新）
  - 不使用 Any 类型注解（除非确实必要）
  - 不删除现有的类型注解
  - 不重构与类型注解无关的代码结构

  **Recommended Agent Profile**:
  - **Category**: `ultrabrain`
    - Reason: 需要深入理解代码逻辑，添加准确的类型注解
  - **Skills**: `[]` (不依赖特殊技能，需要代码理解)

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential (after Tasks 7, 8, 10)
  - **Blocks**: Tasks 12, 13
  - **Blocked By**: Tasks 7, 8, 10

  **References** (CRITICAL - Be Exhaustive):

  **Pattern References** (existing code to follow):
  - `src/bank_template_processing/main.py` - 现有函数定义和类型注解模式
  - `src/bank_template_processing/config_loader.py` - 现有函数定义和类型注解模式
  - `src/bank_template_processing/excel_reader.py` - 类方法类型注解示例
  - `src/bank_template_processing/excel_writer.py` - 类方法类型注解示例
  - `src/bank_template_processing/transformer.py` - 类方法类型注解示例

  - **API/Type References**:
  - https://typing.readthedocs.io/ - Python typing 模块文档
  - https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html - MyPy 类型注解速查表

  - **External References**:
  - https://peps.python.org/pep-0484/ - PEP 484: Type Hints

  **WHY Each Reference Matters**:
  - 现有代码: 了解项目中已有的类型注解模式和风格，保持一致性
  - typing 模块: 了解可用的类型注解（Optional, List, Dict, etc.）
  - PEP 484: 了解 Python 类型注解的标准和最佳实践

  **Acceptance Criteria**:

  - [ ] 所有公开函数有完整的类型注解（参数和返回值）
  - [ ] 所有类方法有完整的类型注解
  - [ ] main() 函数有返回类型注解（-> int）
  - [ ] 复杂类型使用类型别名（可选，全面优化）
  - [ ] 必要的 # type: ignore 注释都有说明原因

  **Manual Execution Verification**:

  - [ ] 检查类型注解覆盖率：
    ```bash
    # 统计有类型注解的函数
    grep -rh "def " src/bank_template_processing/*.py | grep -c "def.*->"
    # 预期: 接近或等于 48（所有函数）

    grep -rh "def " src/bank_template_processing/*.py | grep -c "def.*:.*str\|def.*:.*int\|def.*:.*list\|def.*:.*dict\|def.*:.*List\|def.*:.*Dict\|def.*:.*Optional"
    # 预期: 接近或等于 48（所有函数）
    ```

  - [ ] 验证类型注解正确性：
    ```bash
    uv run mypy . --strict
    # 预期: 无错误（使用包方式运行）或仅有 # type: ignore 相关信息
    ```

  **Evidence Required**:
  - [ ] 添加类型注解后的文件（git diff）
  - [ ] mypy 检查输出
  - [ ] 类型注解覆盖率统计

  **Commit**: YES
  - Message: `feat: add comprehensive type hints to all functions`
  - Files: 所有被修改的 .py 文件
  - Pre-commit: `uv run pytest -v`

---

- [ ] 12. 运行 mypy 验证类型安全

  **What to do**:
  - 运行 `uv run mypy . --strict` 检查类型安全
  - 检查类型错误输出
  - 修复或验证 # type: ignore 的使用
  - 确保没有真实的类型错误

  **Must NOT do**:
  - 不使用 # type: ignore 忽略真正的类型错误
  - 不临时降低 mypy 严格性配置
  - 不忽略类型错误（必须修复或合理使用 # type: ignore）

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: 单个命令执行和结果分析
  - **Skills**: [`quick`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential (after Task 11)
  - **Blocks**: Tasks 13, 14
  - **Blocked By**: Task 11

  **References** (CRITICAL - Be Exhaustive):

  **External References**:
  - https://mypy.readthedocs.io/en/stable/error_code_list.html - MyPy 错误代码列表

  **Acceptance Criteria**:

  - [ ] `uv run mypy . --strict` 运行成功
  - [ ] 所有类型错误已修复或合理忽略
  - [ ] # type: ignore 使用有明确理由

  **Manual Execution Verification**:

  - [ ] 运行类型检查：
    ```bash
    uv run mypy . --strict
    # 预期: 显示 "Success: no issues found in X source files" 或仅有 # type: ignore 相关相关信息
    ```

  - [ ] 检查 # type: ignore 使用：
    ```bash
    grep -r "# type: ignore" src/bank_template_processing/*.py
    # 预期: 显示所有 # type: ignore（应该很少或没有）
    ```

  **Evidence Required**:
  - [ ] mypy 检查成功输出
  - [ ] # type: ignore 使用情况（如果有）

  **Commit**: NO
  - Reason: 此任务仅验证，不产生代码变更

---

- [ ] 13. 运行 pytest 验证无回归

  **What to do**:
  - 运行 `uv run pytest -v` 验证所有测试通过
  - 检查测试失败（如果有）
  - 确保类型注解和代码修复没有引入回归

  **Must NOT do**:
  - 不修改测试文件（除非测试本身被破坏）
  - 不跳过失败的测试
  - 不降低测试覆盖率要求

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: 标准测试执行
  - **Skills**: [`quick`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential (after Task 5, 12)
  - **Blocks**: Task 15
  - **Blocked By**: Tasks 5, 12

  **References** (CRITICAL - Be Exhaustive):

  **Pattern References**:
  - `pytest.ini` - 现有 pytest 配置

  **Acceptance Criteria**:

  - [ ] 所有测试通过
  - [ ] 测试覆盖率没有显著下降
  - [ ] 没有新的测试失败

  **Manual Execution Verification**:

  - [ ] 运行所有测试：
    ```bash
    uv run pytest -v
    # 预期: 显示所有测试通过（PASSED）
    ```

  - [ ] 运行覆盖率测试：
    ```bash
    uv run pytest --cov=. --cov-report=term-missing
    # 预期: 显示覆盖率报告，应该保持现有水平
    ```

  **Evidence Required**:
  - [ ] pytest 成功输出
  - [ ] 覆盖率报告输出

  **Commit**: NO
  - Reason: 此任务仅验证，不产生代码变更

---

- [ ] 14. 安装 pre-commit hooks

  **What to do**:
  - 运行 `pre-commit install` 安装 Git hooks
  - 验证 hooks 安装成功
  - 测试 pre-commit run --all-files 运行

  **Must NOT do**:
  - 不跳过 pre-commit 验证
  - 不配置 pre-commit 为非阻塞（虽然用户选择自动修复+阻塞）

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: 标准工具安装
  - **Skills**: [`quick`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential (after Tasks 9, 10, 12)
  - **Blocks**: Task 15
  - **Blocked By**: Tasks 9, 10, 12

  **References** (CRITICAL - Be Exhaustive):

  **External References**:
  - https://pre-commit.com/ - pre-commit 官方文档

  **Acceptance Criteria**:
  - [ ] pre-commit hooks 安装成功
  - [ ] .git/hooks/ 目录包含 pre-commit 相关文件
  - [ ] `pre-commit run --all-files` 成功运行

  **Manual Execution Verification**:

  - [ ] 安装 hooks：
    ```bash
    pre-commit install
    # 预期: 显示 "pre-commit installed at .git/hooks/pre-commit"
    ```

  - [ ] 运行 hooks：
    ```bash
    pre-commit run --all-files
    # 预期: 运行所有配置的 hooks，全部通过
    ```

  - [ ] 测试 Git commit hook：
    ```bash
    # 做一个小更改
    echo "# test" >> src/bank_template_processing/main.py
    git add .
    # 提交应该触发 pre-commit hooks
    git commit -m "test: verify pre-commit hooks"
    # 预期: pre-commit hooks 运行，成功或显示修复建议
    git reset HEAD~1  # 回滚测试提交
    ```

  **Evidence Required**:
  - [ ] pre-commit install 命令输出
  - [ ] pre-commit run --all-files 命令输出
  - [ ] Git commit hook 触发日志

  **Commit**: YES
  - Message: `chore: install pre-commit hooks`
  - Files: `.git/hooks/*` (不提交，本地更改)
  - Pre-commit: 不适用（hooks 是本地的）

---

- [ ] 15. 更新 README.md 文档

  **What to do**:
  - 在 README.md 添加"开发工作流"章节
  - 说明如何使用 Makefile 命令
  - 说明 pre-commit hooks 工作原理
  - 说明 ruff 和 mypy 配置
  - 添加类型注解使用指南
  - 添加 src/ 目录结构说明
  - 更新"安装"章节，包含开发依赖安装

  **Must NOT do**:
  - 不修改现有的功能说明
  - 不删除现有内容
  - 不过度冗长（保持简洁清晰）

  **Recommended Agent Profile**:
  - **Category**: `writing`
    - Reason: 文档编写，需要清晰的说明
  - **Skills**: [`writing`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential (after Tasks 13, 14)
  - **Blocks**: None (final task)
  - **Blocked By**: Tasks 13, 14

  **References** (CRITICAL - Be Exhaustive):

  **Pattern References**:
  - `README.md` lines 1-50 - 现有文档结构和风格
  - `README.md` lines 19-20 - 现有"安装"章节
  - `README.md` lines 238-251 - 现有"测试"章节

  **External References**:
  - 不适用

  **Acceptance Criteria**:

  - [ ] README.md 更新
  - [ ] 包含"开发工作流"章节
  - [ ] 包含 src/ 目录结构说明
  - [ ] 说明 Makefile 命令使用
  - [ ] 说明 pre-commit hooks 配置
  - [ ] 说明 ruff 和 mypy 配置
  - [ ] 文档清晰易读

  **Manual Execution Verification**:

  - [ ] 查看 README.md：
    ```bash
    cat README.md | grep -A 10 "开发工作流"
    # 预期: 显示开发工作流章节内容
    ```

  **Evidence Required**:
  - [ ] README.md 更新后的内容（git diff）
  - [ ] 开发工作流章节截图或复制

  **Commit**: YES
  - Message: `docs: add development workflow and package structure documentation`
  - Files: `README.md`
  - Pre-commit: 不适用

---

## Commit Strategy

| After Task | Message | Files | Verification |
|------------|---------|-------|--------------|
| 0 | `refactor: create src/ directory structure` | src/bank_template_processing/ | - |
| 1 | `refactor: move Python modules to src/bank_template_processing/` | *.py (moved) | - |
| 2 | `refactor: add package __init__.py` | src/bank_template_processing/__init__.py | - |
| 3 | `refactor: update imports in main modules` | src/bank_template_processing/*.py | uv run pytest -v |
| 4 | `refactor: update test imports` | tests/*.py | uv run pytest -v |
| 5 | `chore: add ruff and mypy configuration and update for src/ structure` | pyproject.toml | uv run pytest -v |
| 6 | `chore: add Makefile for development workflow automation` | Makefile | uv run pytest ruff check |
| 7 | `style: format code with ruff` | *.py | uv run pytest -v |
| 8 | `fix: resolve ruff linting issues` | *.py | uv run pytest -v |
| 9 | `chore: add pre-commit configuration` | .pre-commit-config.yaml | pre-commit validate |
| 10 | `chore: update .gitignore for tooling and reproducibility` | .gitignore | git status |
| 11 | `feat: add comprehensive type hints to all functions` | *.py | uv run pytest -v |
| 15 | `docs: add development workflow and package structure documentation` | README.md | - |

**Note**: Tasks 12, 13, 14 are verification-only and do not produce commits.

---

## Success Criteria

### Verification Commands

```bash
# Ruff 检查
uv run ruff check .
# Expected: No errors

# Ruff 格式化检查
uv run ruff format --check .
# Expected: No changes needed

# MyPy 类型检查
uv run mypy . --strict
# Expected: Success or # type: ignore only

# 测试
uv run pytest -v
# Expected: All tests pass

# 包运行方式
python -m bank_template_processing.main --help
# Expected: Show help message

# 安装包
make install
# Expected: Package installed successfully

# Pre-commit hooks
pre-commit run --all-files
# Expected: All hooks pass
```

### Final Checklist

- [ ] 所有 "Must Have" 存在
- [ ] 所有 "Must NOT Have" 缺失
- [ ] src/bank_template_processing/ 目录结构正确
- [ ] pyproject.toml 包含完整 ruff 和 mypy 配置
- [ ] pyproject.toml 配置使用 setuptools 和 src/ 目录
- [ ] Makefile 所有命令可用且正常工作
- [ ] .pre-commit-config.yaml 配置正确
- [ ] .gitignore 更新且正确
- [ ] 所有 ruff 检查通过
- [ ] 所有 mypy 检查通过（允许 # type: ignore）
- [ ] 所有测试通过（无回归）
- [ ] pre-commit hooks 安装且工作正常
- [ ] README.md 文档更新完成

---

## 附录

### A. Ruff 规则配置说明

**启用的规则集**：
- `E` - pycodestyle errors
- `W` - pycodestyle warnings
- `F` - pyflakes
- `I` - isort (import 排序)
- `N` - pep8-naming
- `UP` - pyupgrade (使用新语法)
- `B` - flake8-bugbear (常见 bug)
- `C4` - flake8-comprehensions
- `SIM` - flake8-simplify
- `TCH` - flake8-type-checking
- `ANN` - flake8-annotations (类型注解检查)
- `RUF` - Ruff 特定规则

**忽略的规则**（渐进式）：
- `E501` - 行过长（由 formatter 处理）
- `ANN001` - 允许函数参数缺少类型注解
- `ANN002` - 允许 *args 缺少类型注解
- `ANN003` - 允许 **kwargs 缺少类型注解
- `ANN101` - 缺少 self 的类型注解
- `ANN102` - 缺少 cls 的类型注解

### B. MyPy 严格模式配置

**启用的严格选项**：
- `strict = true` - 启用严格模式
- `warn_return_any = true` - 警告返回 Any 类型
- `warn_unused_configs = true` - 警告未使用的配置
- `warn_redundant_casts = true` - 警告冗余的类型转换
- `warn_unused_ignores = true` - 警告未使用的 # type: ignore
- `warn_reachable = true` - 警告不可达代码
- `check_untyped_defs = true` - 检查查未类型化定义
- `disallow_any_generics = true` - 禁止 Any 泛型
- `disallow_untyped_defs = false` - 允许部分函数无类型注解（渐进式）
- `disallow_incomplete_defs = false` - 允许不完整的类型注解（渐进式）
- `no_implicit_reexport = true` - 等隐式重新导出

### C. 包结构说明

**新项目结构**：
```
bank-template-processing/
├── src/
│   └── bank_template_processing/
│       ├── __init__.py
│       ├── main.py
│       ├── config_loader.py
│       ├── excel_reader.py
│       ├── excel_writer.pyExcelWriter 类的所有方法
│       ├── transformer.py
│       ├── validator.py
│       └── template_selector.py
├── tests/
│   ├── __init__.py
│   ├── test_*.py
│   └── fixtures/
├── templates/
├── pyproject.toml
├── Makefile
├── .pre-commit-config.yaml
├── .gitignore
└── README.md
```

**运行方式变化**：
- 之前：`python main.py input.xlsx 单位名称 01`
- 之后：`python -m bank_template_processing.main input.xlsx 单位名称 01`
- 或使用 Makefile：`make run input.xlsx 单位名称 01`

### D. 开发工作流示例

```bash
# 日常开发流程
git checkout -b feature/new-implementation

# 1. 编写代码
vim src/bank_template_processing/main.py

# 2. 格式化和检查
make format
make lint
make type-check

# 3. 运行测试
make test

# 4. 提交（pre-commit hooks 自动运行）
git add .
git commit -m "feat: add new feature"
# 如果有可修复问题，hooks 会自动修复并重新运行

# 5. 推送
git push origin feature/new-implementation
```

### E. 故障排除

**问题 1**: ruff 检查失败
- **解决**: 运行 `uv run ruff check --fix .` 自动修复

**问题 2**: mypy 类型检查失败
- **解决**: 检查类型注解，必要时添加 # type: ignore 并注释原因

**问题 3**: pre-commit hooks 阻止提交
- **解决**: 运行 `pre-commit run --all-files` 查看问题，修复后重试

**问题 4**: Makefile 命令失败
- **解决**: 检查命令语法，确保工具正确安装

**问题 5**: 包导入错误
- **解决**: 确保所有导入使用 `bank_template_processing.` 前缀，使用 `python -m` 运行

---

**计划创建时间**: 2025-01-28
**预计完成时间**: 3-4 小时
**负责人**: 执行者（通过 /start-work）
