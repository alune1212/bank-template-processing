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
  - 固固定值填写
  - 银行支行映射
  - 月份类型映射（月收入、年终奖、补偿金）

## 安装

本项目使用 `uv` 作为包管理器：

```bash
# 克隆仓库
git clone <repository-url>
cd bank-template-processing

# 安装依赖
uv sync

# 或使用 pip 安装（如果需要）
pip install openpyxl xlrd xlwt pytest pytest-cov
```

## 使用示例

### 基本用法

```bash
# 处理1月份数据
python main.py input.xlsx 单位名称 01

# 处理年终奖数据
python main.py input.xlsx 单位名称 年终奖

# 处理补偿金数据
python main.py input.xlsx 单位名称 补偿金

# 自定义输出目录
python main.py input.xlsx 单位名称 01 --output-dir custom_output/

# 使用自定义配置文件
python main.py input.xlsx 单位名称 01 --config custom_config.json
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

## 测试

运行测试：

```bash
# 运行所有测试
uv run pytest tests/ -v

# 运行测试并生成覆盖率报告
uv run pytest --cov=. --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html
```

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
├── main.py                 # 命令行入口
├── config_loader.py         # 配置加载器
├── excel_reader.py         # Excel读取器
├── excel_writer.py         # Excel写入器
├── transformer.py           # 数据转换器
├── validator.py            # 数据验证器
├── template_selector.py     # 模板选择器
├── config.json            # 示例配置文件
├── README.md              # 项目文档
├── pyproject.toml          # 项目配置
├── pytest.ini             # pytest配置
├── tests/                 # 测试目录
│   ├── __init__.py
│   ├── test_*.py           # 测试文件
│   └── fixtures/            # 测试fixtures
│       ├── test_*.xlsx       # 测试Excel文件
│       ├── test_*.csv        # 测试CSV文件
│       └── test_*.xls        # 测试XLS文件
└── templates/             # 模板文件目录
    ├── example_template.xlsx
    ├── complex_template.xlsx
    └── example_special_template.xlsx
```

## 许可证

MIT License

## 贡献者

欢迎提交 Pull Request！

## 联系方式

如有问题或建议，请提交 Issue。
