# 银行卡进卡模板处理系统

## 上下文

### 原始需求
构建一个命令行工具，用于处理银行卡进卡模板数据填充。工具接收三个参数：Excel文件路径、主体单位名称、备注（整数月份）。根据主体单位名称查找对应的银行卡进卡模板，从输入Excel文件中提取相应字段，按照模板要求填充数据，生成最终结果表。

### 新增需求（第8次细化）
- **自动编号**：配置中可选择是否对每一行进行自动编号（从1开始递增），并指定编号字段的列名
- **固定值填写**：配置中可以指定某些表头字段使用固定值，直接写入模板而不从输入数据读取
- **银行支行获取**：配置中可选择是否从输入Excel的"开户银行"表头获取支行信息，并映射到模板的对应字段

### 新增需求（第9次细化）
**month参数优化**：
- 原逻辑：month参数是数字（1-12或01-09）
- 新逻辑：
  - 如果传入的是月份（数字）：填写规则为 "输入的月份+月收入"，例如 "01月收入"、"12月收入"
  - 如果传入的是"年终奖"：固定填入"年终奖"
  - 如果传入的是"补偿金"：固定填入"补偿金"
- 配置中需要指定这个特殊字段的列名（例如"收入类型"或"备注"）

### 新增需求（第10次细化）
**多格式支持**：
- 当前仅支持 `.xlsx` 格式
- 新增支持：`.csv`、`.xls` 格式
- 支持的格式扩展：`.xlsx`（使用 openpyxl）、`.csv`（使用 csv 模块）、`.xls`（使用 xlwt/xlrd）
- 模板文件和输入文件都支持这三种格式
- 输出文件格式与模板文件格式保持一致

### 新增需求（第11次细化）
**表头行配置**：
- 当前问题：只配置了数据写入的起始行（`start_row`），但没有配置表头所在的行
- 新增配置：`header_row` 指定模板中表头所在的行数（默认第1行）
- 配置说明：
  - `header_row`：表头所在的行（从1开始计数）
  - `start_row`：数据写入的起始行（从1开始计数）
  - 表头行到数据起始行之间的内容会被保留（例如说明文字、空行等）
- 使用场景：
  - 模板第1-3行是说明信息，第4行是表头，第5行开始是数据
  - 配置：`header_row: 4`, `start_row: 5`
  - 系统会保留第1-3行的说明信息和第4行的表头，从第5行开始写入数据

### 面试摘要

**关键讨论**:
- **编程语言**: Python（适合Excel处理，脚本友好）
- **配置方式**: JSON/YAML配置文件（完整配置：单位映射、字段映射、转换规则、模板路径、默认值、验证规则）
- **输入数据结构**: 有固定表头（标准字段：姓名、卡号、金额、日期等）
- **模板格式**: 带表头的Excel模板（需要字段映射）
- **输出位置**: 指定输出目录
- **字段映射**: 在配置中定义映射（输入列名 → 模板列名）
- **数据转换**: 需要（日期、金额、卡号）
- **错误处理**: 跳过并记录
- **日志记录**: 需要完整日志
- **测试策略**: 完整自动化测试（pytest）

**数据转换规则**:
- **日期格式**: 输出格式 YYYY-MM-DD
- **金额格式**: 保留两位小数
- **卡号格式**: 纯数字（不格式化）

**项目结构**:
- **模板文件位置**: templates/目录
- **命令行参数**: 位置参数（python main.py excel_path unit_name month）

**测试**:
- **自动化测试**: 是，需要完整测试（pytest）

### Metis审查

**已识别的差距**（将在计划中解决）:

**关键差距（需要用户输入）**:
1. **配置格式**: JSON or YAML? (默认: JSON)
2. **模板结构**: 仅表头，或表头+示例数据，或表头+公式? (默认: 仅表头)
3. **数据放置**: 在模板的哪里写入数据（起始行）? (需要根据具体主体单位对应的模板进行选择，每个模板的起始行可能不同)
4. **日期输入格式**: 输入Excel中的日期是什么格式? (默认: 按顺序尝试多种格式: YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY, 中文格式 YYYY年MM月DD日, YYYY-M-D)
5. **输出文件名**: 如何命名输出文件? (需要让输出的文件名具有唯一值)

**次要差距（可自行解决）**:
- **工作表处理**: 默认使用第一个工作表
- **模板路径**: 相对于templates/目录
- **配置位置**: 项目根目录的config.json
- **行结构**: 表头行+数据行（标准Excel格式）

**模糊差距（已应用默认值）**:
- **多余列**: 忽略它们
- **缺失列**: 报错退出
- **空行**: 跳过它们
- **输出文件已存在**: 覆盖
- **金额舍入**: 舍入（标准）
- **卡号验证**: 需要Luhn校验，确保银行卡号符合要求（大多都是中国国内的银行卡号）

---

## 工作目标

### 核心目标
构建一个Python命令行工具，根据配置文件中的映射关系，将输入Excel文件的数据填充到对应的银行进卡模板中，并按照规则转换数据格式，生成格式化的输出Excel文件。

### 具体交付物
- `main.py` - 命令行入口，参数解析和程序主流程
- `config_loader.py` - 配置文件加载和验证
- `excel_reader.py` - Excel文件读取
- `excel_writer.py` - Excel文件写入
- `transformer.py` - 数据转换（日期、金额、卡号）
- `validator.py` - 数据验证
- `config.json` - 示例配置文件
- `pyproject.toml` - uv项目管理文件
- `tests/` - 完整测试套件
- `README.md` - 使用文档

### 完成定义
- [ ] 命令行工具可以正确解析3个参数
- [ ] 可以加载并验证配置文件
- [ ] 可以读取输入Excel文件并提取数据
- [ ] 可以根据单位名称找到对应的模板文件
- [ ] 可以根据字段映射将数据填充到模板
- [ ] 可以正确转换数据格式（日期、金额、卡号）
- [ ] 可以跳过错误行并记录日志
- [ ] 可以生成正确的输出Excel文件
- [ ] 所有测试通过（pytest）
- [ ] README包含完整的使用说明

### 必须具备
- 命令行参数解析（位置参数：excel_path unit_name month）
- 配置文件加载和验证（JSON格式）
- Excel文件读取（openpyxl）
- Excel文件写入（openpyxl）
- 字段映射（输入列名 → 模板列名）
- 数据转换（日期：YYYY-MM-DD，金额：2位小数，卡号：纯数字）
- 错误处理（跳过错误行，记录日志）
- 完整日志记录
- 单元测试和集成测试

### 必须不具备（防护栏）
- 网络功能（Web API、REST endpoints）
- 数据库持久化
- 自动配置文件发现或热重载
- 交互式UI或TUI
- 进度条或spinners
- 邮件/短信通知
- 调度或cron集成
- 模板创建/生成功能
- 多种输入/输出格式（仅支持Excel）
- 批处理或并行处理
- 复杂转换逻辑（配置中不允许自定义Python脚本）
- 复杂验证规则（仅基本类型/格式检查）
- 重试逻辑、circuit breakers、死信队列
- 设计模式（Strategy、Factory、Builder）未经论证
- 依赖注入框架
- 复杂类层次结构（保持扁平）

---

## 验证策略

### 测试决策
- **基础设施存在**: 否（新项目）
- **用户需要测试**: 是 (TDD)
- **框架**: pytest
- **质量保证方法**: TDD (RED-GREEN-REFACTOR)

### 测试设置任务（已启用TDD）

**任务结构**:
1. **RED**: 先写失败的测试
2. **GREEN**: 实现最小代码以通过
3. **REFACTOR**: 在保持绿色的同时清理代码

**测试基础设施设置**:
- **安装**: `pip install pytest pytest-cov`
- **配置**: 创建 `pytest.ini` 或 `pyproject.toml`
- **验证**: `pytest --version` → 显示pytest版本
- **示例**: 创建 `tests/test_example.py`
- **验证**: `pytest` → 1个测试通过

### 手动执行验证（始终包含，即使有测试）

**针对CLI变更**:
- [ ] **运行**: `python main.py test_input.xlsx unit_name 01 output/`
- [ ] **验证**: 输出文件存在于 `output/unit_name_01.xlsx`
- [ ] **验证**: 输出文件包含正确数据

**针对Excel变更**:
   - [ ] 在Excel中打开输出文件
   - [ ] **验证**: header_row 之前的所有内容完全保留（标题、说明等）
   - [ ] **验证**: header_row 行的表头与模板匹配
   - [ ] **验证**: 从 start_row 行开始正确填充数据
   - [ ] **验证**: 转换已应用

---

## 任务流程

\`\`
任务1 (测试基础设施) → 任务2 (配置) → 任务3 (Excel读取) → 任务4 (转换器) → 任务5 (验证器) → 任务6 (Excel写入) → 任务7 (主程序) → 任务8 (集成测试)
                                   ↘ 任务9 (文档)
\`\`

## 并行化

| 组别 | 任务 | 原因 |
|-------|-------|--------|
| A | 2,3, 4, 5, 6 | 独立模块 |
| B | 9 | 文档 |

| 任务 | 依赖 | 原因 |
|------|------------|--------|
| 7 | 2, 3, 4, 5, 6 | 主程序集成所有模块 |
| 8 | 7 | 集成测试需要主流程 |
| 9 | 7 | 实现后的文档 |

---

## 任务列表

- [ ] 1. 使用uv和测试基础设施设置项目

  **要做什么**:
   - 使用 `uv init`' 初始化项目
   - 创建包含依赖项的 `pyproject.toml'`:
     - \`openpyxl>=3.0.0\` (用于 .xlsx 文件)
     - \`xlrd>=2.0.0\` (用于读取 .xls 文件)
     - \`xlwt>=1.3.0\` (用于写入 .xls 文件)
     - \`pytest>=7.0.0\`
     - \`pytest-cov>=4.0.0\`
  - 创建 \`pytest.ini\` 配置文件
  - 创建 \`tests/\` 目录
  - 创建 \`tests/__init__.py\`
  - 创建示例测试 \`tests/test_example.py\`
  - 使用 \`uv sync\` 安装依赖项
  - 验证pytest安装

  **必须不做**:
  - 安装未指定的测试框架（no nose, unittest2）
  - 创建requirements.txt（使用uv/pyproject.toml替代）

  **可并行化**: 否（不依赖任何任务）

  **参考**:

  **模式参考**:
  - Python测试最佳实践的标准pytest项目结构

  **API/类型参考**:
  - pytest API: \`pytest fixtures, pytest.raises, pytest.mark\`

  **测试参考**:
  - 无（第一个任务）

  **文档参考**:
  - pytest文档: \`https://docs.pytest.org/en/stable/\`
  - uv文档: \`https://github.com/astral-sh/uv\`

  **外部参考**:
  - pytest官方文档: \`https://docs.pytest.org/\`
  - uv官方文档: \`https://docs.astral.sh/uv/\`

  **每个参考为何重要**:
  - uv是快速的Python包和项目管理器
  - pytest是Python测试的事实标准
  - 提供fixtures、参数化测试、覆盖率报告

  **验收标准**:

  **如果使用TDD**:
  - [ ] 测试文件已创建: \`tests/test_example.py\`
  - [ ] 测试包含: 一个通过的简单测试
  - [ ] \`pytest tests/test_example.py\` → 通过 (1个测试)

  **手动执行验证**:
  - [ ] **运行**: \`uv sync\`
  - [ ] **验证**: \`uv run pytest --version\` → pytest X.Y.Z
  - [ ] **运行**: \`uv run pytest\`
  - [ ] **预期**: 1个测试通过

  **需要的证据**:
  - [ ] 命令输出: pytest版本和测试结果

  **提交**: 是
  - **消息**: \`chore: setup project with uv and test infrastructure\`
  - **文件**: \`pyproject.toml\`, \`pytest.ini\`, \`tests/\`

- [ ] 2. 实现配置加载器模块

   **要做什么**:
   - 创建 \`config_loader.py\`
   - 实现 \`load_config(config_path: str) -> dict\`
   - 实现 \`validate_config(config: dict) -> None\`
   - 实现对必填字段的验证: \`version\`, \`organization_units\`
   - 实现对每个单位的验证: \`template_path\`, \`header_row\`, \`start_row\`, \`field_mappings\`, \`transformations\`
   - 实现行配置验证：
     - \`header_row\` 必须 ≥ 1
     - \`start_row\` 必须 > \`header_row\`
     - 如果 \`start_row\` 未指定，默认为 \`header_row + 1\`
   - 配置无效时抛出 \`ConfigError\`
   - 为配置加载和验证添加日志

  **必须不做**:
  - 添加热重载或自动配置发现
  - 支持多种配置格式（选择JSON或YAML）

  **可并行化**: 是（与3, 4, 5, 6一起）

  **参考**:

  **模式参考**:
  - 无（新项目）

  **API/类型参考**:
  - Python \`json\` 模块API用于JSON解析

  **测试参考**:
  - \`tests/test_example.py\` - 基本测试结构模式

  **文档参考**:
  - Python json模块: \`https://docs.python.org/3/library/json.html\`

  **外部参考**:
  - JSON模式验证模式（如果使用jsonschema）

  **每个参考为何重要**:
  - json模块是内置的，无外部依赖
  - JSON模式验证确保配置结构正确

  **验收标准**:

   **如果使用TDD**:
   - [ ] 测试文件已创建: \`tests/test_config_loader.py\`
   - [ ] 测试覆盖:
     - 有效配置加载
     - 无效配置路径 (FileNotFoundError)
     - 无效JSON语法 (json.JSONDecodeError)
     - 缺失必填字段 (ConfigError)
     - 无效field_mappings结构 (ConfigError)
     - 无效header_row (ConfigError: 必须 ≥ 1)
     - 无效start_row (ConfigError: 必须 > header_row)
     - start_row 默认值测试 (未指定时为 header_row + 1)
   - [ ] \`pytest tests/test_config_loader.py\` → 通过 (所有测试)

  **手动执行验证**:
  - [ ] 创建测试配置文件 \`tests/fixtures/test_config.json\`
  - [ ] **运行** Python REPL:
    \`\`\`
    >>> from config_loader import load_config, validate_config
    >>> config = load_config('tests/fixtures/test_config.json')
    >>> validate_config(config)
    预期: 无异常抛出
    \`\`\`
  - [ ] 测试无效配置:
    \`\`\`
    >>> load_config('nonexistent.json')
    预期: FileNotFoundError
    \`\`\`

  **需要的证据**:
  - [ ] REPL输出显示成功的配置加载和验证
  - [ ] 无效配置的错误输出

  **提交**: 是
  - **消息**: \`feat: implement configuration loader and validation\`
  - **文件**: \`config_loader.py\`, \`tests/test_config_loader.py\`

- [ ] 3. 实现Excel读取器模块

   **要做什么**:
   - 创建 \`excel_reader.py\`
   - 实现带有 \`read_excel(file_path: str) -> List[dict]\` 的 \`ExcelReader\` 类
   - 根据文件扩展名自动选择读取方式：
     - `.xlsx` 文件：使用 openpyxl（读取第一个工作表）
     - `.csv` 文件：使用 csv 模块（处理 UTF-8 编码）
     - `.xls` 文件：使用 xlrd（读取第一个工作表）
   - 从第1行提取表头
   - 从第2行开始读取数据
   - 将每行转换为带有表头键的字典
   - 跳过空行
   - 文件未找到或无效格式时抛出 \`ExcelError\`
   - 不支持的格式时抛出 \`ExcelError\`
   - 为文件读取和行计数添加日志

  **必须不做**:
  - 读取多个工作表（仅使用第一个工作表）
  - 批量操作（在主程序中逐行处理）

  **可并行化**: 是（与2, 4, 5, 6一起）

  **参考**:

  **模式参考**:
  - 无（新项目）

  **API/类型参考**:
  - openpyxl库API: \`openpyxl.load_workbook\`, \`worksheet.iter_rows\`

  **测试参考**:
  - \`tests/test_config_loader.py\` - 错误处理模式

  **文档参考**:
  - openpyxl文档: \`https://openpyxl.readthedocs.io/\`

  **外部参考**:
  - openpyxl官方文档: \`https://openpyxl.readthedocs.io/en/stable/\`

   **每个参考为何重要**:
   - openpyxl是轻量级的，适合 .xlsx 文件读写，保留格式和公式
   - xlrd/xlwt 用于 .xls 文件（旧格式）
   - csv 模块用于 .csv 文件（简单文本格式）
   - 提供逐行迭代以提高内存效率

  **验收标准**:

   **如果使用TDD**:
   - [ ] 测试文件已创建: \`tests/test_excel_reader.py\`
   - [ ] 测试覆盖:
     - 有效 .xlsx 文件读取
     - 有效 .csv 文件读取
     - 有效 .xls 文件读取
     - 表头提取
     - 数据行转换为字典
     - 空行跳过
     - 文件未找到 (FileNotFoundError)
     - 无效文件格式 (ExcelError)
     - 不支持的格式 (ExcelError)
   - [ ] 创建测试fixtures:
     - \`tests/fixtures/test_input.xlsx\`
     - \`tests/fixtures/test_input.csv\`
     - \`tests/fixtures/test_input.xls\`
   - [ ] \`pytest tests/test_excel_reader.py\` → 通过 (所有测试)

  **手动执行验证**:
  - [ ] **运行** Python REPL:
    \`\`\`
    >>> from excel_reader import ExcelReader
    >>> reader = ExcelReader()
    >>> data = reader.read_excel('tests/fixtures/test_input.xlsx')
    >>> len(data)
    预期: 非空行的数量
    >>> data[0]
    预期: 带有表头键的字典
    \`\`\`

  **需要的证据**:
  - [ ] REPL输出显示成功的Excel读取
  - [ ] 数据结构显示正确的字典转换

  **提交**: 是
  - **消息**: \`feat: implement Excel reader module\`
  - **文件**: \`excel_reader.py\`, \`tests/test_excel_reader.py\`, \`tests/fixtures/test_input.xlsx\`

- [ ] 4. 实现数据转换器模块

  **要做什么**:
  - 创建 \`transformer.py\`
  - 实现带有转换方法的 \`Transformer\` 类:
    - \`transform_date(value, output_format="YYYY-MM-DD") -> str\`
    - \`transform_amount(value, decimal_places=2) -> float\`
    - \`transform_card_number(value) -> str\`
  - 日期转换: 解析输入日期（按顺序尝试多种格式），格式化YYYY-MM-DD
    - 支持的输入格式: \`YYYY-MM-DD\`, \`DD/MM/YYYY\`, \`MM/DD/YYYY\`, \`中文格式 YYYY年MM月DD日\`, \`YYYY-M-D\`
    - 按顺序尝试每种格式，使用首次成功的解析
    - 如果所有格式都失败，抛出 \`TransformError\'
  - 金额转换: 使用标准舍入舍入到2位小数
  - 卡号转换: 移除非数字字符，仅保留数字
  - 对卡号进行Luhn验证：验证符合中国银行卡号要求
  - 无效数据时抛出 \`TransformError\`
  - 为转换添加日志

  **必须不做**:
  - 添加自定义转换函数（保持3个内置函数）
  - 不对其他字段进行Luhn验证（仅卡号）

  **可并行化**: 是（与2, 3, 5, 6一起）

  **参考**:

  **模式参考**:
  - 无（新项目）

  **API/类型参考**:
  - Python \`datetime\` 模块: \`datetime.strptime\`, \`datetime.strftime\`
  - Python \`decimal\` 模块: \`Decimal.quantize\`, \`ROUND_HALF_UP\`

  **测试参考**:
  - \`tests/test_excel_reader.py\` - 错误处理模式

  **文档参考**:
  - Python datetime: \`https://docs.python.org/3/library/datetime.html\`
  - Python decimal: \`https://docs.python.org/3/library/decimal.html\`

  **外部参考**:
  - 日期格式标准: YYYY-MM-DD使用ISO 8601

  **每个参考为何重要**:
  - datetime模块提供强大的日期解析和格式化
  - decimal模块为金融金额提供精确的小数运算

  **验收标准**:

  **如果使用TDD**:
  - [ ] 测试文件已创建: \`tests/test_transformer.py\`
  - [ ] 测试覆盖:
    - 日期转换: 多种输入格式 (YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY, YYYY年MM月DD日, YYYY-M-D) → YYYY-MM-DD
    - 金额转换: 舍入到2位小数
    - 卡号转换: 移除空格/横杠
    - 无效日期（所有格式失败 → TransformError）
    - 无效金额 (TransformError)
    - 无效卡号 (TransformError)
    - Luhn校验: 中国银行卡号通过Luhn算法验证
  - [ ] \`pytest tests/test_transformer.py\` → 通过 (所有测试)

  **手动执行验证**:
  - [ ] **运行** Python REPL:
    \`\`\`
    >>> from transformer import Transformer
    >>> t = Transformer()
    >>> t.transform_date('2025年1月25日')
    预期: '2025-01-25'
    >>> t.transform_amount(12345.6789)
    预期: 12345.68
    >>> t.transform_card_number('6222 1234 5678 9012')
    预期: '6222123456789012'
    \`\`\`

  **需要的证据**:
  - [ ] REPL输出显示正确的转换

  **提交**: 是
  - **消息**: \`feat: implement data transformer module\`
  - **文件**: \`transformer.py\`, \`tests/test_transformer.py\`

- [ ] 5. 实现数据验证器模块

  **要做什么**:
  - 创建 \`validator.py\`
  - 实现带有验证方法的 \`Validator\` 类:
    - \`validate_required(row: dict, required_fields: List[str]) -> None\`
    - \`validate_data_types(row: dict, type_rules: dict) -> None\`
    - \`validate_value_ranges(row: dict, range_rules: dict) -> None\`
    - 必填字段验证: 检查必填字段是否存在且非空
  - 数据类型验证: 检查字段值是否匹配预期的类型
    - 值范围验证: 检查字段值是否在允许的范围内
    - 验证失败时抛出 \`ValidationError\`
    - 为验证结果添加日志

  **必须不做**:
  - 添加复杂的验证规则（仅基本类型/范围检查）
  - 添加跨字段验证（仅单字段验证）

  **可并行化**: 是（与2, 3, 4, 6一起）

  **参考**:

  **模式参考**:
  - 无（新项目）

  **API/类型参考**:
  - 无（基本Python类型检查）

  **测试参考**:
  - \`tests/test_transformer.py\` - 错误处理模式

  **文档参考**:
  - 无（基本验证逻辑）

  **外部参考**:
  - 无（简单验证规则）

  **每个参考为何重要**:
  - 基本\`验证确保处理前的数据质量
  - 简单规则保持代码可维护

  **验收标准**:

  **如果使用TDD**:
  - [ ] 测试文件已创建: \`tests/test_validator.py\`
  - [ ] 测试覆盖:
    - 必填字段验证: 全部存在 → 通过
    - 必填字段验证: 缺失必填 → ValidationError
    - 数据类型验证: 正确类型 → 通过
    - 数据类型验证: 错误类型 → ValidationError
    - 值范围验证: 在范围内 → 通过
    - 值范围验证: 超出范围 → ValidationError
  - [ ] \`pytest tests/test_validator.py\` → 通过 (所有测试)

  **手动执行验证**:
  - [ ] **运行** Python REPL:
    \`\`\`
    >>> from validator import Validator
    >>> v = Validator()
    >>> v.validate_required({'name'\`'John', 'amount'\`'100}, ['name'\`, 'amount'\`])
    预期: 无异常
    >>> v.validate_required({'name'\`'John'}, ['name'\`, 'amount'\`'])
    预期: ValidationError
    \`\`\`

  **需要的证据**:
  - [ ] REPL输出显示验证行为

  **提交**: 是
  - **消息**: \`feat: implement data validator module\`
  - **文件**: \`validator.py\`, \`tests/test_validator.py\`

- [ ] 6. 实现Excel写入器模块

   **要做什么**:
    - 创建 \`excel_writer.py\`
    - 实现带有 \`write_excel(template_path: str, data: List[dict], field_mappings: dict, output_path: str, header_row: int, start_row: int, mapping_mode: str, fixed_values: dict, auto_number: dict, bank_branch_mapping: dict, month_type_mapping: dict, month_param: str) -> None\` 的 \`ExcelWriter\` 类
    - 根据模板文件扩展名自动选择写入方式：
      - `.xlsx` 文件：使用 openpyxl（保留格式、公式、合并单元格）
      - `.csv` 文件：使用 csv 模块（UTF-8 编码，无格式保留）
      - `.xls` 文件：使用 xlwt（基本格式，无公式保留）
    - 加载模板文件（从配置的 header_row 读取表头）
    - 从配置获取字段映射、表头行（header_row）和数据起始行（start_row）
    - 验证配置：start_row 必须 > header_row，否则抛出 ConfigError
    - 从配置的起始行开始清除所有行（移除现有数据，对 .xlsx/.xls 有效）
    - 从配置的起始行开始将转换后的数据写入模板
    - 保留第1行到header_row-1的所有内容（说明文字、空行等）
    - 保留header_row行的表头
    - 应用字段映射（支持列名优先，列索引备选）
    - 处理固定值：为每一行写入配置的固定值到指定列
    - 处理自动编号：如果enabled=true，从start_from开始为每一行递增编号
    - 处理银行支行映射：如果enabled=true.get("source_column")获取支行信息，写入到get("target_column")
    - 处理month类型映射（month_type_mapping）：
      - 如果enabled=false，不处理
      - 如果month_param是数字（1-12或01-09），格式化为"{month}月收入"（例如"01月收入"）
      - 如果month_param="年终奖"，写入配置的"bonus_value"（默认"年终奖"）
      - 如果month_param="补偿金"，写入配置的"compensation_value"（默认"补偿金"）
      - 将结果写入到配置的"target_column"
    - 保留配置的header_row行的模板格式、公式和合并单元格（仅对 .xlsx/.xls 有效）
    - 保存到输出路径（从不覆盖原始模板）
    - 写入失败时抛出 \`ExcelError\`
    - 不支持的格式时抛出 \`ExcelError\`
    - 为文件写入和行计数添加日志

  **必须不做**:
  - 覆盖原始模板文件（始终写入到新输出文件）
  - 从配置的起始行+行开始追加数据（先清除配置的起始行+行）

  **可并行化**: 是（与2, 3, 4, 5一起）

  **参考**:

  **模式参考**:
  - 无（新项目）

  **API/类型参考**:
  - openpyxl库API: \`openpyxl.load_workbook\`, \`cell.value\`, \`workbook.save\`

  **测试参考**:
  - \`tests/test_validator.py\` - 错误处理模式

   **文档参考**:
   - openpyxl文档: \`https://openpyxl.readthedocs.io/\`
   - xlrd/xlwtwt文档: \`https://www.python-excel.org/\`
   - Python csv模块: \`https://docs.python.org/3/library/csv.html\`

   **外部参考**:
   - openpyxl官方文档: \`https://openpyxl.readthedocs.io/en/stable/\`
   - xlrd官方文档: \`https://xlrd.readthedocs.io/\`

   **每个参考为何重要**:
   - openpyxl保留Excel格式和公式（用于 .xlsx）
   - xlrd/xlwt 用于 .xls 文件（旧格式）
   - csv 模块用于 .csv 文件（简单文本格式）
   - 逐单元格写入允许精确控制

  **验收标准**:

   **如果使用TDD**:
   - [ ] 测试文件已创建: \`tests/test_excel_writer.py\`
   - [ ] 测试覆盖:
     - 成功的 .xlsx 文件写入（保留格式、公式）
     - 成功的 .csv 文件写入（无格式）
     - 成功的 .xls 文件写入（基本格式）
     - 字段映射应用（列名优先）
     - 字段映射应用（列索引备选）
     - 固定值填写（fixed_values）
     - 自动编号（auto_number）
     - 银行支行映射（bank_branch_mapping）
     - month类型映射（month_type_mapping）：
       - 月份参数为数字时，格式化为"01月收入"、"12月收入"等
       - 月份参数为"年终奖"时，填入"年终奖"
       - 月份参数为"补偿金"时，填入"补偿金"
     - 模板格式保留（.xlsx/.xls）
     - 如需要创建输出目录
     - 权限错误 (ExcelError)
     - 不支持的格式 (ExcelError)
   - [ ] 创建测试fixtures:
     - \`tests/fixtures/test_template.xlsx\`
     - \`tests/fixtures/test_template.csv\`
     - \`tests/fixtures/test_template.xls\`
   - [ ] \`pytest tests/test_excel_writer.py\` → 通过 (所有测试)

   **手动执行验证**:
   - [ ] **运行** Python REPL:
     \`\`\`
     >>> from excel_writer import ExcelWriter
     >>> writer = ExcelWriter()
     >>> data = [{'姓名'\`'张三', '卡号'\`:'6222123456789012', '金额'\`: 100.00}]
     >>> mappings = {'客户姓名'\`:'姓名', '卡号'\`:'卡号', '金额'\`:'金额'\`}
     >>> fixed_values = {'省份': '浙江省', '业务类型': '工资代发'}
     >>> auto_number = {'enabled': True, 'column_name': '序号', 'start_from': 1}
     >>> bank_branch = {'enabled': True, 'source_column': '开户银行', 'target_column': '开户支行'}
     >>> month_mapping = {'enabled': False}
     >>> # 测试 .xlsx 格式
     >>> writer.write_excel('tests/fixtures/test_template.xlsx', data, mappings, 'output/test.xlsx', 2, 'name_first', fixed_values, auto_number, bank_branch, month_mapping, '01')
     预期: 文件创建于 output/test.xlsx
     >>> # 测试 .csv 格式
     >>> writer.write_excel('tests/fixtures/test_template.csv', data, mappings, 'output/test.csv', 2, 'name_first', fixed_values, auto_number, bank_branch, month_mapping, '01')
     预期: 文件创建于 output/test.csv
     >>> # 测试 .xls 格式
     >>> writer.write_excel('tests/fixtures/test_template.xls', data, mappings, 'output/test.xls', 2, 'name_first', fixed_values, auto_number, bank_branch, month_mapping, '01')
     预期: 文件创建于 output/test.xls
     \`\`\`

  **需要的证据**:
  - [ ] 输出文件已创建
  - [ ] 输出文件包含正确数据

  **提交**: 是
  - **消息**: \`feat: implement Excel writer module\`
  - **文件**: \`excel_writer.py\`, \`tests/test_excel_writer.py\`, \`tests/fixtures/test_template.xlsx\`

- [ ] 7. 实现主CLI模块

   **要做什么**:
   - 创建 \`main.py\`
   - 使用 \`argparse\` 实现参数解析:
     - 位置参数1: \`excel_path\` (输入Excel文件路径)
     - 位置参数2: \`unit_name\` (组织单位名称)
     - 位置参数3: \`month\` (月份参数，支持：1-12或01-09格式的月份，或"年终奖"，或"补偿金")
     - 可选参数: \`--output-dir\` (输出目录, 默认: \`output/\`)
     - 可选参数: \`--config\` (配置文件路径, 默认: \`config.json\`)
     - 可选参数: \`--output-filename-template\` (输出文件名模板, 默认: \`{unit_name}_{month}\`)
   - 实现month参数校验：
     - 数字格式：1-12或01-09，支持0开头
     - 关键字格式："年终奖"或"补偿金"
     - 其他值：抛出ValueError
   - 实现主工作流程:
     1. 加载并验证配置
     2. 基于unit_name从配置获取单位配置
     3. 读取输入Excel文件
     4. 验证输入数据
     5. 按照配置转换数据
     6. 写入到模板Excel文件（传入month参数）
     7. 生成输出文件名: 使用模板+时间戳确保唯一性
     8. 保存到输出目录
   - 实现错误处理: 捕获并记录所有异常
   - 实现日志: 配置带时间戳的日志
   - 添加 \`--help\` 并附带清晰的使用说明

  **必须不做**:
  - 添加TUI或交互式提示
  - 添加进度条或spinners
  - 添加网络功能

  **可并行化**: 否（依赖2, 3, 4, 5, 6）

  **参考**:

  **模式参考**:
  - \`config_loader.py\` - 配置加载模式
  - \`excel_reader.py\` - Excel读取模式
  - \`transformer.py\` - 转换模式
  - \`validator.py\` - 验证模式
  - \`excel_writer.py\` - Excel写入模式

  **API/类型参考**:
  - argparse API: \`argparse.ArgumentParser\`, \`add_argument\`, \`parse_args\`

  **测试参考**:
  - 所有模块的测试文件用于模块模式

  **文档参考**:
  - argparse文档: \`https://docs.python.org/3/library/argparse.html\`

  **外部参考**:
  - 无（标准库）

  **每个参考为何重要**:
  - argparse是内置的，无外部依赖
  - 提供标准化的CLI接口和帮助生成

  **验收标准**:

   **如果使用TDD**:
   - [ ] 测试文件已创建: \`tests/test_main.py\`
   - [ ] 测试覆盖:
     - 参数解析（有效参数）
     - 缺失必填参数（argparse错误）
     - 无效文件路径 (FileNotFoundError)
     - 无效单位名称 (ConfigError)
     - 无效月份格式 (ValueError: 不是1-12、01-09、"年终奖"或"补偿金")
     - 有效月份格式（1-12、01-09、"年终奖"、"补偿金"）
     - 成功的端到端处理
     - 唯一文件名生成策略
   - [ ] \`pytest tests/test_main.py\` → 通过 (所有测试)

   **手动执行验证**:
   - [ ] **运行**: \`python main.py --help\`
   - [ ] **验证**: 帮助文本显示所有参数，包括month参数的三种格式说明
   - [ ] **运行**: \`python main.py tests/fixtures/test_input.xlsx unit_test 01 --output-dir output/\`
   - [ ] **验证**: 输出文件创建于 \`output/unit_test_01_20250126001234.xlsx\`，收入类型列为"01月收入"
   - [ ] **运行**: \`python main.py tests/fixtures/test_input.xlsx unit_test 年终奖 --output-dir output/\`
   - [ ] **验证**: 输出文件收入类型列为"年终奖"
   - [ ] **运行**: \`python main.py tests/fixtures/test_input.xlsx unit_test 补偿金 --output-dir output/\`
   - [ ] **验证**: 输出文件收入类型列为"补偿金"
   - [ ] **运行**: \`python main.py nonexistent.xlsx unit_test 01\`
   - [ ] **预期**: FileNotFoundError 并附带清晰消息

  **需要的证据**:
  - [ ] 帮助输出显示所有参数
  - [ ] 成功运行的输出附带日志
  - [ ] 无效输入的错误输出

  **提交**: 是
  - **消息**: \`feat: implement main CLI module with argument parsing and month validation\`
  - **文件**: \`main.py\`, \`tests/test_main.py\`

- [ ] 8. 实现集成测试

  **要做什么**:
  - 创建 \`tests/test_integration.py\`
  - 实现端到端集成测试:
    - 完整工作流: 读取配置，读取输入，转换，写入输出
    - 错误处理: 缺失文件，无效数据
    - 数据转换验证
    - 唯一文件名生成验证
    - Luhn校验功能验证
    - 创建完整的测试fixtures:
      - \`tests/fixtures/integration_input.xlsx\` (示例输入)
      - \`tests/fixtures/integration_template.xlsx\` (示例模板)
      - \`tests/fixtures/integration_config.json\` (完整配置)
  - 验证输出数据正确性
  - 验证转换正确应用
  - 验证错误处理正常工作

  **必须不做**:
  - 测试外部依赖（网络、数据库）

  **可并行化**: 否（依赖7）

  **参考**:

  **模式参考**:
  - 所有模块的测试文件用于模块模式

  **API/类型参考**:
  - pytest API用于fixtures和断言

  **测试参考**:
  - 所有模块的测试文件

  **文档参考**:
  - pytest文档: \`https://docs.pytest.org/\`

  **外部参考**:
  - 无（使用pytest）

  **每个参考为何重要**:
  - 集成测试验证完整工作流
  - 捕获单元测试中未发现的集成问题

  **验收标准**:

  **如果使用TDD**:
  - [ ] 测试文件已创建: \`tests/test_integration.py\`
  - [ ] 测试覆盖:
    - 成功的完整工作流
    - 数据转换正确性
    - 缺失文件的错误处理
    - 无效数据的错误处理
    - 唯一文件名生成验证
    - Luhn校验功能验证
    - 日志输出验证
  - [ ] \`pytest tests/test_integration.py\` → 通过 (所有测试)

  **手动执行验证**:
  - [ ] **运行**: \`pytest tests/test_integration.py -v\`
  - [ ] **验证**: 所有集成测试通过
  - [ ] **运行**: \`pytest --cov=. --cov-report=html\`
  - [ ] **验证**: 覆盖率报告生成（应>90%）

  **需要的证据**:
  - [ ] pytest输出显示所有集成测试通过
  - [ ] 覆盖率报告显示高覆盖率

  **提交**: 是
  - **消息**: \`test: add integration tests for complete workflow\`
  - **文件**: \`tests/test_integration.py\`, \`tests/fixtures/integration_*.xlsx\`, \`tests/fixtures/integration_config.json\`

- [ ] 9. 创建文档和示例配置

   **要做什么**:
   - 创建 \`README.md\` 并包含:
     - 项目描述（银行进卡模板处理系统）
     - 安装说明（使用uv）
     - 使用示例
     - 配置文件结构说明（包括header_row, start_row, mapping_mode, luhn_validation, output_filename_template等新增配置项）
     - 多格式支持说明（.xlsx, .csv, .xls）
     - 错误处理文档
     - 测试说明
   - 创建附带清晰注释的`示例 \`config.json\`（包括所有新增配置项：fixed_values, auto_number, bank_branch_mapping, month_type_mapping）
   - 创建示例 \`templates/example_template.xlsx\`（包含序号、开户支行、收入类型等列）
   - 创建复杂模板示例 \`templates/complex_template.xlsx\`（包含多行说明、标题等，演示 header_row 和 start_row 的使用）

  **必须不做**:
  - 添加自动生成的文档工具（未经请求）
  - 添加交互式教程（未经请求）
  - 创建requirements.txt（使用uv/pyproject.toml）

  **可并行化**: 是（与其他所有任务一起）

  **参考**:

  **模式参考**:
  - 标准Python项目README格式

  **API/类型参考**:
  - 无

  **测试参考**:
  - 无

  **文档参考**:
  - 无（标准README格式）

  **外部参考**:
  - Python打包最佳实践: \`https://packaging.python.org/\`

  **每个参考为何重要**:
  - README是用户首先看到的内容
  - 清晰的文档减少支持负担

  **验收标准**:

  **如果使用TDD**:
  - [ ] \`README.md\` 完整且可读
  - [ ] \`config.json\` 是附带示例配置的有效JSON
  - [ ] \`templates/example_template.xlsx\` 是有效的Excel文件

  **手动执行验证**:
  - [ ] **运行**: \`uv run python main.py --help\`
  - [ ] **验证**: 帮助输出正确显示
  - [ ] **打开**: \`README.md\`
  - [ ] **验证**: 包含安装、使用和配置部分
  - [ ] **验证**: README提及使用uv进行安装

  **需要的证据**:
  - [ ] README.md内容
  - [ ] 帮助输出

  **提交**: 是
  - **消息**: \`docs: add comprehensive README and example configuration\`
  - **文件**: \`README.md\`, \`config.json\`, \`templates/example_template.xlsx\`

---

## 提交策略

| 任务后 | 消息 | 文件 | 验证 |
|------------|---------|-------|--------------|
| 1 | \`chore: setup project with uv and test infrastructure\` | \`pyproject.toml\`, \`pytest.ini\`, \`tests/\` | \`uv run pytest pytest --version\` |
| 2 | \`feat: implement configuration loader and validation\` | \`config_loader.py\`, \`tests/\` | \`uv run pytest tests/test_config_loader.py\` |
| 3 | \`feat: implement Excel reader module\` | \`excel_reader.py\`, \`tests/\` | \`uv run pytest tests/test_excel_reader.py\` |
| 4 | \`feat: implement data transformer module\` | \`transformer.py\`, \`tests/\` | \`uv run pytest tests/test_transformer.py\` |
| 5 | \`feat: implement data validator module\` | \`validator.py\`, \`tests/\` | \`uv run pytest tests/test_validator.py\` |
| 6 | \`feat: implement Excel writer module\` | \`excel_writer.py\`, \`tests/\` | \`uv run pytest tests/test_excel_writer.py\` |
| 7 | \`feat: implement main CLI module with argument parsing and month validation\` | \`main.py\`, \`tests/\` | \`uv run pytest tests/test_main.py\` |
| 8 | \`test: add integration tests for complete workflow\` | \`tests/test_integration.py\`, \`tests/fixtures/\` | \`uv run pytest tests/test_integration.py\` |
| 9 | \`docs: add comprehensive README and example config\` | \`README.md\`, \`config.json\`, \`templates/\` | \`uv run pytest --cov\` |

---

## 成功标准

### 验证命令
\`\`\`bash
# 使用uv同步依赖项
uv sync
# 预期: 依赖项已安装

# 运行所有测试
uv run pytest tests/ -v
# 预期: 所有测试通过

# 运行覆盖率
uv run pytest --cov=. --cov-report=html
# 预期: 覆盖率>90%

# 测试CLI帮助
uv run python main.py --help
# 预期: 帮助文本显示

# 测试端到端
uv run python main.py tests/fixtures/test_input.xlsx unit_test 01 --output-dir output/
# 预期: output/unit_test_01_20250126001234.xlsx 已创建（或带有时间戳以确保唯一性）

# 验证覆盖率报告
open htmlcov/index.html
# 预期: 覆盖率报告显示
\`\`\`

### 最终检查清单
- [ ] 所有"必须具备"存在
- [ ] 所有"必须不具备不具备"不存在
- [ ] 所有测试通过（pytest）
- [ ] 覆盖率>90%
- [ ] README完整
- [ ] 示例config.json有效
- [ ] 示例template.xlsx有效
- [ ] CLI适用于所有测试用例
- [ ] 错误处理适用于所有错误用例
- [ ] 日志输出完整且可读

---

## 配置文件结构（需要决策）

**[需要决策: 配置格式 - JSON或YAML?]**

建议的结构（JSON）:

```json
{
  "version": "1.0",
  "organization_units": {
    "unit_name": {
      "template_path": "templates/unit_template.xlsx",
      "header_row": 1,  // 表头所在的行（从1开始计数，默认第1行）
      "start_row": 2,   // 数据写入的起始行（从1开始计数，默认从header_row+1开始）
      "field_mappings": {
        "template_column_name": {
          "source_column": "input_column_name",
          "source_column_name": "姓名",  // 保留列名用于日志
          "mapping_mode": "name_first",  // 数据放置方式："name_first"(列名优先), "index_first"(列索引优先), "name_first_fallback"(列名优先，回退到索引)
          "transform": "date_format|amount_decimal|card_number|none",
          "required": true
        }
      },
      "fixed_values": {
        "template_column_name": "固定值内容",
        "省份": "浙江省",
        "业务类型": "工资代发"
      },
      "auto_number": {
        "enabled": true,
        "column_name": "序号",
        "start_from": 1
      },
      "bank_branch_mapping": {
        "enabled": true,
        "source_column": "开户银行",
        "target_column": "开户支行"
      },
      "month_type_mapping": {
        "enabled": true,
        "target_column": "收入类型",  // 模板中接收month类型信息的列名
        "month_format": "{month}月收入",  // 月份格式模板，例如 "01月收入"
        "bonus_value": "年终奖",  // 当month="年终奖"时填写的值
        "compensation_value": "补偿金"  // 当month="补偿金"时填写的值
      },
      "transformations": {
        "date_format": {
          "output_format": "YYYY-MM-DD"
        },
        "amount": {
          "decimal_places": 2,
          "rounding": "round"
        },
        "card_number": {
          "remove_formatting": true,
          "luhn_validation": true
        }
      },
      "validation_rules": {
        "required_fields": ["name", "card_number", "amount", "date"],
        "data_types": {
          "amount": "numeric",
          "date": "date"
        }
      }
    }
  }
}
```

**[需要决策: 日期输入格式]**
- 输入Excel中的日期是什么格式?
- 工具应该自动检测，还是强制特定格式?
- 支持的输入格式: \`YYYY-MM-DD\`, \`DD/MM/YYYY\`, \`MM/DD/YYYY\`, \`中文格式 YYYY年MM月DD日\`, \`YYYY-M-D\`

**[需要决策: 模板结构]**
- 仅表头（将被数据替换）?
- 表头+示例数据（将被替换）?
- 表头+公式/格式化（将被保留+数据添加）?
- 每个主体的模板的起始行可能不同（需要在配置中为每个单位指定）

**[需要决策: 数据放置]**
- 数据应该写入到哪一行？第2行？需要在配置中为每个单位指定起始行？

**[需要决策: 输出文件名]**
- 如何生成唯一的输出文件名以避免冲突?
- 是否使用时间戳或序列号?
- 是否在配置中指定文件名生成策略?

---

## 模板文件要求（需要决策）

**[需要决策: 模板工作表名称]**
- 使用第一个工作表？特定名称？

**[需要决策: 模板表头行]**
- 始终是第1行？可配置？

**[需要决策: 单元格保留]**
- 公式应该被保留？
- 格式化应该被保留？
- 合并单元格应该被处理？

---

## 已应用的默认决策（如需要可覆盖）

- **配置格式**: JSON（合理的默认值，可覆盖为YAML）
- **数据放置方案**: 混合方案（列名优先，回退到列索引）- 这是最终决策
- **日期输入格式**: 按顺序尝试多种\`格式: \`YYYY-MM-DD\`, \`DD/MM/YYYY\`, \`MM/DD/YYYY\`, \`中文格式 YYYY年MM月DD日\`, \`YYYY-M-D\`（灵活解析，首次匹配胜出）
- **日期输出格式**: YYYY-MM-DD（用户已确认）
- **金额小数位数**: 2（用户已确认）
- **金额舍入**: 舍入（标准）
- **卡号格式**: 纯数字（用户已确认）
- **卡号验证**: Luhn校验（中国银行卡号要求）
- **工作表处理**: 使用第一个工作表
- **模板表头行**: 第1行
- **数据起始行**: 基于配置（每个主体的模板可能起始行不同）
- **模板数据处理**: 从配置的起始行开始清除所有行后写入数据（替换模式，不是追加）
- **输出文件名**: 唯一文件名生成（使用时间戳避免冲突）
- **输出文件已存在**: 覆盖
- **空行**: 跳过
- **多余列**: 忽略
- **缺失列**: 报错
- **配置位置**: 项目根目录的config.json
- **模板路径**: 相对于templates/目录
- **日志输出**: 仅控制台（可稍后添加文件日志）

---

## 示例数据结构

### 示例输入Excel (test_input.xlsx)
| 姓名 | 卡号 | 金额 | 日期 | 开户银行 |
|------|------|------|------|----------|
| 张三 | 6222 1234 5678 9012 | 12345.678 | 2025-01-25 | 工商银行杭州分行 |
| 李四 | 6222-9876-5432-1098 | 67890.123 | 25/01/2025 | 工商银行宁波分行 |
| 王五 | 6222987654321098 | 12.5 | 2025年1月25日 | 工商银行温州分行 |
| 赵六 | 6222020061234567 | 99999.99 | 2025-01-25 | 工商银行嘉兴分行 |

### 示例配置 (config.json)
\`\`\`json
{
  "version": "1.0",
  "organization_units": {
    "工商银行": {
      "template_path": "templates/icbc_template.xlsx",
      "header_row": 1,  // 表头在第1行
      "start_row": 2,   // 数据从第2行开始写入
      "field_mappings": {
        "客户姓名": {
          "source_column": "姓名",
          "source_column_name": "姓名",
          "mapping_mode": "name_first",
          "transform": "none",
          "required": true
        },
        "银行卡号": {
          "source_column": "卡号",
          "source_column_name": "卡号",
          "mapping_mode": "name_first",
          "transform": "card_number",
          "required": true
        },
        "转账金额": {
          "source_column": "金额",
          "source_column_name": "金额",
          "mapping_mode": "name_first",
          "transform": "amount_decimal",
          "required": true
        },
        "交易日期": {
          "source_column": "日期",
          "source_column_name": "日期",
          "mapping_mode": "name_first",
          "transform": "date_format",
          "required": true
        }
      },
      "fixed_values": {
        "省份": "浙江省",
        "业务类型": "工资代发",
        "账户类型": "个人结算账户"
      },
      "auto_number": {
        "enabled": true,
        "column_name": "序号",
        "start_from": 1
      },
      "bank_branch_mapping": {
        "enabled": true,
        "source_column": "开户银行",
        "target_column": "开户支行"
      },
      "month_type_mapping": {
        "enabled": true,
        "target_column": "收入类型",
        "month_format": "{month}月收入",
        "bonus_value": "年终奖",
        "compensation_value": "补偿金"
      },
      "transformations": {
        "date_format": {
          "output_format": "YYYY-MM-DD"
        },
        "amount": {
          "decimal_places": 2,
          "rounding": "round"
        },
        "card_number": {
          "remove_formatting": true,
          "luhn_validation": true
        }
      },
      "validation_rules": {
        "required_fields": ["姓名", "卡号", "金额", "日期"],
        "data_types": {
          "金额": "numeric",
          "日期": "date"
        }
      }
    },
    "建设银行": {
      "template_path": "templates/ccb_template.xlsx",
      "header_row": 2,  // 表头在第2行
      "start_row": 3,   // 数据从第3行开始写入
      "field_mappings": {
        "户名": {
          "source_column": "姓名",
          "source_column_name": "姓名",
          "mapping_mode": "name_first",
          "transform": "none",
          "required": true
        },
        "卡号": {
          "source_column": "卡号",
          "source_column_name": "卡号",
          "mapping_mode": "name_first",
          "transform": "card_number",
          "required": true
        },
        "入账金额": {
          "source_column": "金额",
          "source_column_name": "金额",
          "mapping_mode": "name_first",
          "transform": "amount_decimal",
          "required": true
        },
        "日期": {
          "source_column": "日期",
          "source_column_name": "日期",
          "mapping_mode": "name_first",
          "transform": "date_format",
          "required": true
        }
      },
      "fixed_values": {
        "交易类型": "代发",
        "货币种类": "人民币"
      },
      "auto_number": {
        "enabled": false
      },
      "bank_branch_mapping": {
        "enabled": false
      },
      "month_type_mapping": {
        "enabled": false
      },
      "transformations": {
        "date_format": {
          "output_format": "YYYY-MM-DD"
        },
        "amount": {
          "decimal_places": 2,
          "rounding": "round"
        },
        "card_number": {
          "remove_formatting": true,
          "luhn_validation": true
        }
      },
      "validation_rules": {
        "required_fields": ["姓名", "卡号", "金额", "日期"],
        "data_types": {
          "金额": "numeric",
          "日期": "date"
        }
      }
|------|--------|--------|------|
| `.xlsx` | openpyxl | openpyxl | 保留格式、公式、合并单元格 |
| `.xls` | xlrd | xlwt | 基本格式，无公式保留 |
| `.csv` | csv | csv | 纯文本，无格式，UTF-8编码 |

**注意**：
- 模板文件和输入文件都可以是任何支持的格式
- 输出文件格式与模板文件格式保持一致
- CSV 文件不支持格式、公式和合并单元格

### 示例模板文件

#### icbc_template.xlsx (.xlsx 格式)
| 序号 | 客户姓名 | 银行卡号 | 转账金额 | 交易日期 | 省份 | 业务类型 | 账户类型 | 开户支行 | 收入类型 |
|------|----------|----------|----------|----------|------|----------|----------|----------|----------|
| (第2+行将被清除并填充转换后的数据)

### 示例输出Excel (output/工商银行_01_20250126001212.xlsx)
**当month参数为"01"时**：
| 序号 | 客户姓名 | 银行卡号 | 转账金额 | 交易日期 | 省份 | 业务类型 | 账户类型 | 开户支行 | 收入类型 |
|------|----------|----------|----------|----------|------|----------|----------|----------|----------|
| 1 | 张三 | 6222123456789012 | 12345.68 | 2025-01-25 | 浙江省 | 工资代发 | 个人结算账户 | 工商银行杭州分行 | 01月收入 |
| 2 | 李四 | 6222987654321098 | 67890.12 | 2025-01-25 | 浙江省 | 工资代发 | 个人结算账户 | 工商银行宁波分行 | 01月收入 |
| 3 | 王五 | 6222987654321098 | 12.50 | 2025-01-25 | 浙江省 | 工资代发 | 个人结算账户 | 工商银行温州分行 | 01月收入 |
| 4 | 赵六 | 6222020061234567 | 99999.99 | 2025-01-25 | 浙江省 | 工资代发 | 个人结算账户 | 工商银行嘉兴分行 | 01月收入 |

**当month参数为"年终奖"时**：
| 序号 | 客户姓名 | 银行卡号 | 转账金额 | 交易日期 | 省份 | 业务类型 | 账户类型 | 开户支行 | 收入类型 |
|------|----------|----------|----------|----------|------|----------|----------|----------|----------|
| 1 | 张三 | 6222123456789012 | 12345.68 | 2025-01-25 | 浙江省 | 工资代发 | 个人结算账户 | 工商银行杭州分行 | 年终奖 |
| 2 | 李四 | 6222987654321098 | 67890.12 | 2025-01-25 | 浙江省 | 工资代发 | 个人结算账户 | 工商银行宁波分行 | 年终奖 |
| 3 | 王五 | 6222987654321098 | 12.50 | 2025-01-25 | 浙江省 | 工资代发 | 个人结算账户 | 工商银行温州分行 | 年终奖 |
| 4 | 赵六 | 6222020061234567 | 99999.99 | 2025-01-25 | 浙江省 | 工资代发 | 个人结算账户 | 工商银行嘉兴分行 | 年终奖 |

**当month参数为"补偿金"时**：
| 序号 | 客户姓名 | 银行卡号 | 转账金额 | 交易日期 | 省份 | 业务类型 | 账户类型 | 开户支行 | 收入类型 |
|------|----------|----------|----------|----------|------|----------|----------|----------|----------|
| 1 | 张三 | 6222123456789012 | 12345.68 | 2025-01-25 | 浙江省 | 工资代发 | 个人结算账户 | 工商银行杭州分行 | 补偿金 |
| 2 | 李四 | 6222987654321098 | 67890.12 | 2025-01-25 | 浙江省 | 工资代发 | 个人结算账户 | 工商银行宁波分行 | 补偿金 |
| 3 | 王五 | 6222987654321098 | 12.50 | 2025-01-25 | 浙江省 | 工资代发 | 个人结算账户 | 工商银行温州分行 | 补偿金 |
| 4 | 赵六 | 6222020061234567 | 99999.99 | 2025-01-25 | 浙江省 | 工资代发 | 个人结算账户 | 工商银行嘉兴分行 | 补偿金 |

---

## 第9次细化：Month参数优化说明

**month参数现在支持三种类型**：

### 1. 月份数字
- **格式**: 1-12 或 01-09（支持0开头）
- **输出规则**: `{month}月收入`
- **示例**:
  - 输入: `01` → 输出: `01月收入`
  - 输入: `12` → 输出: `12月收入`
  - 输入: `9` → 输出: `9月收入`

### 2. 年终奖
- **格式**: `年终奖`
- **输出规则**: 固定值 `"年终奖"`
- **示例**: 输入: `年终奖` → 输出: `年终奖`

### 3. 补偿金
- **格式**: `补偿金`
- **输出规则**: 固定值 `"补偿金"`
- **示例**: 输入: `补偿金` → 输出: `补偿金`

**命令行使用示例**:
```bash
# 月份处理
python main.py input.xlsx 工商银行 01 --output-dir output/

# 年终奖处理
python main.py input.xlsx 工商银行 年终奖 --output-dir output/

# 补偿金处理
python main.py input.xlsx 工商银行 补偿金 --output-dir output/
```

---

## 第10次细化：多格式文件支持

**系统现在支持三种文件格式**：

### 格式对比

| 格式 | 扩展名 | 读取库 | 写入库 | 格式保留 | 公式保留 | 合并单元格 |
|------|--------|--------|--------|----------|----------|------------|
| **Excel 2007+** | `.xlsx` | openpyxl | openpyxl | ✅ 完全保留 | ✅ 保留 | ✅ 保留 |
| **Excel 97-2003** | `.xls` | xlrd | xlwt | ⚠️ 基本保留 | ❌ 不保留 | ❌ 不保留 |
| **CSV** | `.csv` | csv | csv | ❌ 无格式 | ❌ 不适用 | ❌ 不适用 |

### 使用示例

**命令行使用**：
```bash
# 使用 .xlsx 模板和输入文件
python main.py input.xlsx 工商银行 01 --output-dir output/

# 使用 .csv 模板和输入文件
python main.py input.csv 工商银行 年终奖 --output-dir output/

# 使用 .xls 模板和输入文件
python main.py input.xls 工商银行 补偿金 --output-dir output/
```

**不同格式的输出结果**：

1. **`.xlsx` 输出**：
   - 完全保留模板的格式、字体、颜色、边框
   - 保留所有公式
   - 保留合并单元格
   - 适合需要复杂格式化的银行模板

2. **`.xls` 输出**：
   - 保留基本格式（字体、对齐）
   - 公式不会被保留
   - 合并单元格不会保留
   - 适合旧版Excel兼容

3. **`.csv` 输出**：
   - 纯文本格式，无任何格式
   - UTF-8 编码
   - 逗号分隔，双引号包裹（如果包含逗号）
   - 适合简单数据交换

### 格式处理规则

1. **自动检测格式**：根据文件扩展名自动选择处理方式
2. **输出格式继承**：输出文件格式与模板文件格式一致
3. **错误处理**：不支持的格式会抛出 `ExcelError`
4. **模板优先**：模板文件的格式决定输出文件的格式

### CSV 特殊处理

- 编码：UTF-8（无 BOM）
- 分隔符：逗号（`,`）
- 引用：双引号（`"`），仅在必要时使用
- 换行符：`\n`（Unix 风格）

### 配置示例

配置文件中不需要指定格式，系统会自动根据 `template_path` 的扩展名判断：

```json
{
  "organization_units": {
    "工商银行": {
      "template_path": "templates/icbc_template.xlsx",  // 自动识别为 .xlsx
      ...
    },
    "建设银行": {
      "template_path": "templates/ccb_template.xls",   // 自动识别为 .xls
      ...
    },
    "农业银行": {
      "template_path": "templates/abc_template.csv",    // 自动识别为 .csv
      ...
    }
  }
}
```

### 依赖包说明

项目需要安装以下依赖：

```toml
[dependencies]
openpyxl = ">=3.0.0"  # 用于 .xlsx 文件
xlrd = ">=2.0.0"      # 用于 .xls 文件读取
xlwt = ">=1.3.0"      # 用于 .xls 文件写入

[dev-dependencies]
pytest = ">=7.0.0"
pytest-cov = ">=4.0.0"
```

注意：CSV 模块是 Python 标准库，无需额外安装。

---

## 第11次细化：表头行配置

**新增配置项：`header_row``**

### 配置说明

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `header_row` | int | 1 | 模板中表头所在的行（从1开始计数） |
| `start_row` | int | header_row+1 | 数据写入的起始行（从1开始计数） |

### 行保留规则

系统会保留以下内容：

1. **第1行到 `header_row-1` 行**：保留所有内容（说明文字、标题、空行等）
2. **`header_row` 行**：保留表头（格式、公式、合并单元格）
3. **`start_row` 及之后行**：清除原有数据，写入新数据

### 配置示例

#### 示例1：标准模板
```
第1行：表头
第2行：数据起始
```
```json
{
  "header_row": 1,
  "start_row": 2
}
```

#### 示例2：带说明的模板
```
第1行：标题 "工资发放表"
第2行：（空行）
第3行：说明 "填写日期：2025年1月"
第4行：表头
第5行：数据起始
```
```json
{
  "header_row": 4,
  "start_row": 5
}
```
**保留内容**：
- ✅ 第1-3行（标题、空行、说明）完全保留
- ✅ 第4行（表头）保留，包括格式和合并单元格
- ✅ 第5行开始写入新数据

#### 示例3：复杂模板
```
第1行：银行LOGO
第2行：标题 "中国工商银行"
第3行：项目名称 "2025年1月工资发放"
第4行：（空行）
第5行：表头
第6行：数据起始
```
```json
{
  "header_row": 5,
  "start_row": 6
}
```

### 验证规则

配置加载时会验证以下规则：

1. `header_row` 必须 ≥ 1
2. `start_row` 必须 > `header_row`
3. 如果 `start_row` 未指定，默认为 `header_row + 1`

**验证失败示例**：
```json
{
  "header_row": 5,
  "start_row": 3  // ❌ 错误：start_row 必须 > header_row
}
```

### 与其他功能的关系

`header_row` 配置不会影响以下功能：

- ✅ **固定值填写**：固定值仍然根据列名映射写入
- ✅ **自动编号**：序号列根据 `column_name` 映射
- ✅ **银行支行映射**：支行信息根据 `source_column` 和 `target_column` 映射
- ✅ **month类型映射**：收入类型根据 `target_column` 映射

### 不同格式的行为

| 格式 | `header_row` 行保留 | `header_row` 到 `start_row` 保留 |
|------|-------------------|--------------------------------|
| `.xlsx` | ✅ 完全保留格式、公式、合并单元格 | ✅ 完全保留 |
| `.xls` | ⚠️ 保留基本格式 | ✅ 保留 |
| `.csv` | ❌ 无格式（纯文本） | ✅ 保留 |

### 配置示例（完整）

```json
{
  "version": "1.0",
  "organization_units": {
    "工商银行": {
      "template_path": "templates/icbc_template.xlsx",
      "header_row": 4,  // 表头在第4行
      "start_row": 5,   // 数据从第5行开始写入
      "field_mappings": {
        "客户姓名": {
          "source_column": "姓名",
          "source_column_name": "姓名",
          "mapping_mode": "name_first",
          "transform": "none",
          "required": true
        }
        // ... 其他字段映射
      },
      "fixed_values": {
        "省份": "浙江省",
        "业务类型": "工资代发"
      },
      "auto_number": {
        "enabled": true,
        "column_name": "序号",
        "start_from": 1
      },
      "bank_branch_mapping": {
        "enabled": true,
        "source_column": "开户银行",
        "target_column": "开户支行"
      },
      "month_type_mapping": {
        "enabled": true,
        "target_column": "收入类型",
        "month_format": "{month}月收入",
        "bonus_value": "年终奖",
        "compensation_value": "补偿金"
      }
    }
  }
}
```

### 使用场景总结

| 场景 | header_row | start_row | 说明 |
|------|-----------|-----------|------|
| 简单的标准模板 | 1 | 2 | 表头在第1行，数据从第2行开始 |
| 带标题的模板 | 2 | 3 | 第1行是标题，第2行是表头 |
| 带多行说明的模板 | 5 | 6 | 第1-4行是说明，第5行是表头 |
| 银行标准模板 | 3 | 4 | 银行LOGO和标题占前2行 |
