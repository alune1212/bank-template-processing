# 银行卡进卡模板处理系统

处理OA系统审批流程中的数据，将数据处理为银行模板对应的格式。

## 功能特性

- **多格式支持**：支持 `.xlsx`、`.csv`、`.xls` 三种Excel格式
- **数据转换**：
  - 日期格式转换（支持多种输入格式）
  - 金额舍入（保留指定位数）
  - 卡号格式化（移除分隔符，Luhn校验）
- **动态模板选择**：根据"开户银行"字段自动选择默认模板或特殊模板
- **高级功能**：
  - 自动编号
  - 固定值填写
  - 银行支行映射
  - 月份类型映射（月收入、年终奖、补偿金）

## 安装

### 方式一：Windows 可执行文件（推荐普通用户）

下载 `bank-template-processing-win.zip` 压缩包，解压后即可使用，无需安装 Python。

解压后目录结构：
```
bank-template-processing/
├── bank-template-processing.exe  # 主程序
├── config.example.json           # 配置示例
├── README.md                     # 说明文档
├── 配置文件说明.md               # 配置说明
├── 快速使用指南.txt              # 快速指南
├── templates/                    # 模板目录（放入银行模板文件）
└── output/                       # 输出目录（处理结果保存在这里）
```

**首次使用步骤：**
1. 将 `config.example.json` 复制为 `config.json`
2. 根据实际需求修改 `config.json` 中的配置
3. 将银行模板文件放入 `templates/` 目录
4. 打开命令提示符（CMD）或 PowerShell 运行程序

### 方式二：从源码安装（开发者）

本项目使用 `uv` 作为包管理器，并采用标准的 `src` 目录结构。

```bash
# 克隆仓库
git clone <repository-url>
cd bank-template-processing

# 安装依赖
uv sync

# 激活虚拟环境 (可选，uv run 会自动处理)
# source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate     # Windows
```

## 使用示例

### Windows 可执行文件用法

```cmd
# 处理1月份数据
bank-template-processing.exe input.xlsx 单位名称 01

# 处理年终奖数据
bank-template-processing.exe input.xlsx 单位名称 年终奖

# 处理补偿金数据
bank-template-processing.exe input.xlsx 单位名称 补偿金

# 自定义输出目录
bank-template-processing.exe input.xlsx 单位名称 01 --output-dir custom_output/

# 使用自定义配置文件
bank-template-processing.exe input.xlsx 单位名称 01 --config custom_config.json
```

### Python 源码用法

推荐使用 `uv run` 或 `python -m` 方式运行：

```bash
# 处理1月份数据
uv run python -m bank_template_processing input.xlsx 单位名称 01
# 或者如果安装了项目脚本：
# uv run bank-process input.xlsx 单位名称 01

# 处理年终奖数据
uv run python -m bank_template_processing input.xlsx 单位名称 年终奖

# 自定义输出目录
uv run python -m bank_template_processing input.xlsx 单位名称 01 --output-dir custom_output/
```

## 配置文件说明

配置文件使用 JSON 格式，包含以下主要部分：

### 基本结构

```json
{
  "version": "1.0",
  "organization_units": {
    "单位名称": {
      "template_path": "templates/模板文件.xlsx",
      "header_row": 1,
      "start_row": 2,
      "field_mappings": { ... },
      "transformations": { ... },
      "validation_rules": { ... }
    }
  }
}
```

### 配置项说明

| 配置项 | 说明 | 默认值 |
|---------|------|---------|
| `version` | 配置文件版本号 | "1.0" |
| `template_path` | 模板文件路径 | 必填 |
| `header_row` | 表头所在行（从1开始）| 必填，≥ 1 |
| `start_row` | 数据起始行（从1开始）| header_row + 1 |
| `field_mappings` | 字段映射配置 | 必填 |
| `fixed_values` | 固定值配置 | 可选 |
| `auto_number` | 自动编号配置 | 可选 |
| `bank_branch_mapping` | 银行支行映射 | 可选 |
| `month_type_mapping` | 月份类型映射 | 可选 |
| `reader_options` | 读取器选项 | 可选 |
| `template_selector` | 动态模板选择 | 可选 |

### 字段映射配置

```json
"field_mappings": {
  "模板列名": {
    "source_column": "输入列名",
    "transform": "date_format|amount_decimal|card_number|none",
    "required": true
  }
}
```

### 固定值配置

```json
"fixed_values": {
  "模板列名": "固定值"
}
```

示例：
```json
"fixed_values": {
  "省份": "浙江省",
  "业务类型": "工资代发"
}
```

### 自动编号配置

```json
"auto_number": {
  "enabled": true,
  "column_name": "序号",
  "start_from": 1
}
```

### 银行支行映射

```json
"bank_branch_mapping": {
  "enabled": true,
  "source_column": "开户银行",
  "target_column": "开户支行"
}
```

### 月份类型映射

```json
"month_type_mapping": {
  "enabled": true,
  "target_column": "收入类型",
  "month_format": "{month}月收入",
  "bonus_value": "年终奖",
  "compensation_value": "补偿金"
}
```

### 读取器选项（reader_options）

用于控制读取 Excel 时的策略。

```json
"reader_options": {
  "data_only": true
}
```

说明：
- `data_only`: 当为 `true` 时，读取公式单元格的**缓存结果**；为 `false` 时读取公式文本。
  - 注意：`openpyxl` 不会计算公式，只有在 Excel 中保存过计算结果时才有缓存值。

### 动态模板选择配置

`template_selector` 配置用于根据"开户银行"字段自动选择模板：

```json
"template_selector": {
  "enabled": true,
  "default_bank": "中国农业银行",
  "special_template": "templates/特殊模板.xlsx"
}
```

当启用时：
- "开户银行" == "中国农业银行" → 使用默认模板
- "开户银行" ≠ "中国农业银行" → 使用特殊模板

**输出文件命名规则**：
- 单模板模式：`{unit_name}_{month}_{timestamp}.xlsx`
- 动态模板模式：`{unit_name}_{template_name}_{month}_{timestamp}.xlsx`

## 数据转换规则

### 日期格式转换

支持以下输入日期格式，统一输出为 `YYYY-MM-DD`：
- `YYYY-MM-DD`
- `DD/MM/YYYY`
- `MM/DD/YYYY`
- `YYYY年MM月DD日`
- `YYYY-M-D`

### 金额格式转换

使用标准舍入，保留指定位数：
- 默认：2位小数
- 示例：`123.4567` → `123.46`

### 卡号格式转换

1. 移除非数字字符（空格、横杠等）
2. 执行 Luhn 校验，确保卡号有效性

**Luhn 算法**：
- 从右向左遍历
- 偶数位乘以2，如果乘积大于9则减去9
- 所有数字相加，总和能被10整除则有效

## 模板文件结构

### 简单模板（`example_template.xlsx`）

```
第1行（表头）：序号 | 姓名 | 卡号 | 金额 | 日期 | 开户支行 | 收入类型
第2行开始：数据行
```

### 复杂模板（`complex_template.xlsx`）

```
第1-3行：说明文字、标题
第4行（表头）：序号 | 姓名 | 卡号 | 金额 | 日期 | ...
第5行开始：数据行
```

配置示例：
```json
{
  "header_row": 4,
  "start_row": 5
}
```

## 错误处理

系统会捕获并记录以下错误：

| 错误类型 | 说明 | 处理方式 |
|----------|------|----------|
| `ConfigError` | 配置文件错误 | 记录错误消息，退出 |
| `ExcelError` | Excel文件错误 | 记录错误消息，退出 |
| `ValidationError` | 数据验证错误 | 记录错误消息，退出 |
| `TransformError` | 数据转换错误 | 记录错误消息，退出 |
| `FileNotFoundError` | 文件未找到 | 记录错误消息，退出 |
| `ValueError` | 参数值错误 | 记录错误消息，退出 |

## 开发指南

### 代码规范
本项目采用现代化工具链：
- **包管理**: `uv`
- **代码格式/检查**: `ruff`
- **类型检查**: `ty` (Astral) 或 `mypy`

### 运行测试

```bash
# 运行所有测试
uv run pytest

# 运行测试并生成覆盖率报告
uv run pytest --cov=src --cov-report=html
```

### 代码检查

```bash
# 格式化代码
uv run ruff format .

# 静态检查
uv run ruff check . --fix

# 类型检查
uv run ty check
```

## Windows 打包（开发者）

如需自行构建 Windows 可执行文件：

### 前置条件

- Windows 操作系统
- Python 3.13+
- `uv` 包管理器

### 构建步骤

**方式一：使用 PowerShell 脚本（推荐）**

```powershell
# 在项目根目录执行
.\scripts\build_windows.ps1
```

**方式二：手动执行 PyInstaller**

```bash
# 安装依赖
uv sync

# 执行打包（使用 uv 环境）
uv run pyinstaller bank_template_processing.spec --noconfirm

# 打包结果在 dist\bank-template-processing\ 目录
```

### 构建产物

- `dist/bank-template-processing/` - 可分发目录
- `dist/bank-template-processing-win.zip` - 压缩包（可直接分发）

## 日志

日志格式：`%(asctime)s - %(name)s - %(levelname)s - %(message)s`

日志级别：
- `INFO`：常规操作信息
- `WARNING`：警告信息
- `ERROR`：错误信息
- `DEBUG`：调试信息

## 项目结构

```
bank-template-processing/
├── src/                          # 源代码目录
│   └── bank_template_processing/ # Python 包
│       ├── __init__.py
│       ├── __main__.py           # 模块入口
│       ├── main.py               # 命令行入口逻辑
│       ├── config_loader.py      # 配置加载器
│       ├── excel_reader.py       # Excel读取器
│       ├── excel_writer.py       # Excel写入器
│       ├── transformer.py        # 数据转换器
│       ├── validator.py          # 数据验证器
│       └── template_selector.py  # 模板选择器
├── config.json                   # 配置文件（用户创建）
├── config.example.json           # 配置文件示例
├── README.md                     # 项目文档
├── 配置文件说明.md               # 配置说明（中文）
├── pyproject.toml                # 项目配置 (依赖, 构建, 工具配置)
├── bank_template_processing.spec # PyInstaller 打包规格
├── run_for_pyinstaller.py        # PyInstaller 入口脚本
├── scripts/                      # 构建脚本
│   ├── build_windows.ps1         # PowerShell 打包脚本
│   └── build_windows.bat         # 批处理打包脚本
├── tests/                        # 测试目录
│   ├── __init__.py
│   ├── test_*.py                 # 测试文件
│   └── fixtures/                 # 测试fixtures
└── templates/                    # 模板文件目录（用户创建）
    └── ...                       # 银行模板文件
```

## 许可证

MIT License

## 贡献者

欢迎提交 Pull Request！

## 联系方式

如有问题或建议，请提交 Issue。
