# 银行卡进卡模板处理系统

将 OA 审批导出的发薪数据清洗、校验、转换后写入银行模板，支持单文件处理和已生成结果文件的批量合并。

## 功能概览

- 支持 `.xlsx`、`.xls` 两种输入与模板格式。
- 默认在读取后过滤 `实发工资 = 0` 的数据行。
- 支持多规则组配置，常见结构为 `default`、`crossbank` 和自定义项目组。
- 支持按“开户银行”自动分组输出到不同模板。
- 支持按输入文件名中的项目编码直接路由到指定规则组。
- 支持日期、金额、卡号转换，以及必填、类型、范围校验。
- 支持 `fixed_values`、`auto_number`、`month_type_mapping`、`clear_rows` 等模板写入能力。
- 支持对已生成文件按“单位 + 模板”分组再汇总输出。
- 默认输出文件名模板为 `{unit_name}_{template_name}_{count}人_金额{amount:.2f}元{ext}`。

## 运行要求

- Python `>=3.13`
- 仓库当前 `.python-version` 为 `3.14`
- 包管理器使用 [`uv`](https://docs.astral.sh/uv/)

普通使用者也可以直接使用 Windows 打包产物；开发与日常维护建议直接从源码运行。

## 快速开始

### 从源码运行

```bash
uv sync
cp config.example.json config.json
mkdir -p templates
```

然后：

1. 按需编辑 `config.json`
2. 将银行模板放入 `templates/`
3. 运行 CLI

### 普通处理模式

```bash
uv run python -m bank_template_processing input.xlsx "单位名称" 01

# 或使用项目脚本入口
uv run bank-process input.xlsx "单位名称" 01
```

月份参数支持：

- `1` 到 `12`
- `01` 到 `09`
- `年终奖`
- `补偿金`

### 批量合并模式

```bash
uv run python -m bank_template_processing --merge-folder output --config config.json
```

该模式会读取 `output/` 目录第一层中的已生成文件，并将汇总结果写到 `output/result/`。

## 命令行参数

### 普通模式

```bash
uv run python -m bank_template_processing <excel_path> "<unit_name>" <month> [options]
```

常用参数：

- `--output-dir`：输出目录，默认 `output/`
- `--config`：配置文件路径，默认 `config.json`
- `--output-filename-template`：自定义输出文件名模板

### 合并模式

```bash
uv run python -m bank_template_processing --merge-folder <folder> [options]
```

约束：

- 使用 `--merge-folder` 时，不能同时提供 `excel_path`、`unit_name`、`month`
- 合并模式只扫描目标目录第一层文件，不递归子目录

### 输出文件名模板

默认值：

```text
{unit_name}_{template_name}_{count}人_金额{amount:.2f}元{ext}
```

可用变量：

- `{unit_name}`
- `{month}`
- `{template_name}`
- `{count}`
- `{amount}`
- `{ext}`

说明：

- 如果模板中没有使用 `{ext}`，程序会自动追加模板扩展名。
- 合并模式只有在规则组启用了 `month_type_mapping` 且输出模板实际使用 `{month}` 时，才会尝试推断月份值。

## 配置速览

配置文件为 JSON，推荐使用多规则组结构。顶层至少包含 `"version": "2.0"` 和 `organization_units`。

```json
{
  "version": "2.0",
  "organization_units": {
    "单位名称": {
      "template_selector": {
        "enabled": true,
        "default_bank": "中国农业银行",
        "bank_column": "开户银行",
        "default_group_name": "农业银行",
        "special_group_name": "农行跨行"
      },
      "input_filename_routing": {
        "enabled": true,
        "routes": [
          { "project_code": "B01095", "rule_group": "b01095" }
        ]
      },
      "default": {
        "template_path": "templates/default.xlsx",
        "header_row": 1,
        "start_row": 2,
        "reader_options": {
          "data_only": false,
          "header_row": 1
        },
        "clear_rows": {
          "start_row": 2,
          "end_row": 200
        },
        "field_mappings": {
          "姓名": {
            "source_column": "姓名",
            "target_column": "姓名",
            "transform": "none",
            "required": true
          },
          "金额": {
            "source_column": "实发工资",
            "target_column": "金额",
            "transform": "amount_decimal",
            "required": true
          }
        },
        "transformations": {
          "amount_decimal": {
            "decimal_places": 2,
            "rounding": "round"
          }
        },
        "validation_rules": {
          "required_fields": ["姓名", "实发工资"],
          "data_types": {
            "实发工资": "numeric"
          }
        }
      },
      "crossbank": {
        "template_path": "templates/crossbank.xlsx",
        "header_row": 2,
        "start_row": 3,
        "field_mappings": {},
        "transformations": {}
      },
      "b01095": {
        "template_path": "templates/b01095.xlsx",
        "header_row": 1,
        "start_row": 2,
        "field_mappings": {},
        "transformations": {}
      }
    }
  }
}
```

关键点：

- 多规则组结构中必须有 `default`
- `input_filename_routing` 只支持多规则组结构
- `header_row` 是输出模板表头行，允许为 `0`
- `reader_options.header_row` 是输入文件表头行，必须 `>= 1`
- `start_row` 必须大于 `header_row`
- `field_mappings`、`transformations` 为规则组必填项

更完整的字段说明见 [配置文件说明.md](/Users/alune/Documents/code/bank-template-processing/配置文件说明.md)。

## 关键运行时行为

### 路径解析

- 相对 `config` 路径会解析到程序运行目录
- 相对 `template_path` 也会解析到程序运行目录
- 源码运行时，这个目录通常是项目根目录
- PyInstaller 打包运行时，这个目录是可执行文件所在目录

### 数据读取与筛选

- 程序会先读取输入文件，再执行 `实发工资 = 0` 行过滤
- 当前实现固定依赖输入数据存在 `实发工资` 列；若缺失会直接报错
- `row_filter.exclude_keywords` 会在读取阶段跳过包含关键字的整行
- `reader_options.data_only=true` 时，`.xlsx` 会读取公式缓存值而不是公式文本

### 动态模板选择

- `input_filename_routing` 命中时，优先于 `template_selector`
- `template_selector` 使用 `bank_column` 与 `default_bank` 对比
- 对比前会做全角转半角和首尾空白归一化，减少银行名称格式差异造成的误分组
- `special_template`、`default_template` 可选；未配置时会回退到对应规则组的 `template_path`

### 批量合并

- 程序优先按默认命名 `{unit_name}_{template_name}_{count}人_金额{amount:.2f}元{ext}` 解析文件
- 若文件名不完全符合默认命名，会尝试根据配置中的单位名与模板名回推
- 输入文件按修改时间升序处理；若修改时间相同，按文件名升序处理
- 文件名中若带有人数和金额，合并时会与数据重算结果做一致性校验
- 启用 `month_type_mapping` 时，合并输出会保留每行原始月类型值，不会统一改写为同一个月份文案

## 配置能力摘要

### `field_mappings`

- 推荐使用字典格式，显式声明 `source_column`、`target_column`、`transform`
- `target_column` 支持三种写法：
  - 模板表头列名
  - Excel 列字母，例如 `A`、`B`、`AA`
  - 从 `1` 开始的列索引
- 中文列名会按“列名”处理，不会误判成 Excel 列字母

### `transformations`

- `date_format`：支持多种日期输入，当前仅输出 `YYYY-MM-DD`
- `amount_decimal`：支持 `round`、`half_up`、`floor`、`ceil`、`down`、`up`
- `card_number`：支持去格式化和 Luhn 校验

### `validation_rules`

- 仅支持 `required_fields`、`data_types`、`value_ranges`
- 旧键名 `type_rules`、`range_rules` 会被直接拒绝
- `required_fields` 在转换前执行
- `data_types` 和 `value_ranges` 在转换后执行

### 其他常用项

- `clear_rows`：控制模板中预清空的数据区域；支持 `end_row`，兼容 `data_end_row`
- `fixed_values`：向模板列写固定值
- `auto_number`：自动写序号，支持 `column` 或 `column_name`
- `month_type_mapping`：根据月份参数写用途/摘要等字段
- `bank_branch_mapping`：仍兼容，但已废弃，建议直接改用 `field_mappings`

## 开发与测试

```bash
# 运行测试
uv run pytest tests/ -v

# 文档同步检查
uv run pytest tests/test_docs_sync.py -v

# 代码格式化与检查
uv run ruff format .
uv run ruff check . --fix

# 类型检查
uv run ty check
```

当前测试配置要求总覆盖率不低于 `92%`。

## Windows 打包

```powershell
pwsh ./scripts/build_windows.ps1
```

或：

```bash
uv run pyinstaller bank_template_processing.spec
```

## 项目结构

```text
bank-template-processing/
├── src/bank_template_processing/
│   ├── __main__.py
│   ├── main.py
│   ├── config_loader.py
│   ├── excel_reader.py
│   ├── excel_writer.py
│   ├── merge_folder.py
│   ├── pipeline.py
│   ├── sheet_utils.py
│   ├── template_selector.py
│   ├── transformer.py
│   └── validator.py
├── tests/
├── config.example.json
├── README.md
├── 配置文件说明.md
├── templates.example/
├── bank_template_processing.spec
└── run_for_pyinstaller.py
```
