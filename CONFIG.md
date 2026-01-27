# 配置文件详细说明

本文档详细说明了银行卡进卡模板处理系统的配置文件（`config.json`）的格式和各个字段的含义。

---

## 目录

- [文件概览](#文件概览)
- [顶层结构](#顶层结构)
- [组织单位配置](#组织单位配置)
- [字段映射配置](#字段映射配置)
- [转换配置](#转换配置)
- [验证规则配置](#验证规则配置)
- [高级功能配置](#高级功能配置)
  - [固定值配置](#固定值配置)
  - [自动编号配置](#自动编号配置)
  - [银行支行映射配置](#银行支行映射配置)
  - [月份类型映射配置](#月份类型映射配置)
  - [动态模板选择配置](#动态模板选择配置)
- [配置验证规则](#配置验证规则)
- [完整示例](#完整示例)
- [最佳实践](#最佳实践)
- [常见问题](#常见问题)

---

## 文件概览

配置文件使用 **JSON 格式**，定义了一个或多个组织单位的数据处理规则。

### 文件位置

默认配置文件位于项目根目录：`config.json`

### 通过参数指定自定义配置

```bash
python main.py input.xlsx 单位名称 01 --config custom_config.json
```

---

## 顶层结构

### 必填字段

| 字段名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| `version` | string | 配置文件版本号，用于配置兼容性管理 | `"1.0"` |
| `organization_units` | object | 组织单位配置字典，键为单位名称，值为单位配置 | 见下方 |

### 示例

```json
{
  "version": "1.0",
  "organization_units": {
    "农业银行": { /* 单位配置 */ },
    "工商银行": { /* 单位配置 */ }
  }
}
```

---

## 组织单位配置

每个组织单位是一个独立的配置对象，定义了该单位的数据处理规则。

### 基本配置字段（必填）

| 字段名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `template_path` | string | ✅ | Excel模板文件路径（相对或绝对路径） | `"templates/example_template.xlsx"` |
| `header_row` | integer | ✅ | 表头所在行号（从1开始计数） | `1` |
| `start_row` | integer | ❌ | 数据起始行号（从1开始计数），默认为 `header_row + 1` | `2` |
| `field_mappings` | object | ✅ | 字段映射配置，见 [字段映射配置](#字段映射配置) | 见下方 |
| `transformations` | object | ✅ | 数据转换参数配置，见 [转换配置](#转换配置) | 见下方 |

### 行号说明

- **行号从1开始**（不是0）
- `header_row`：模板中表头所在的行
- `start_row`：数据开始写入的行，必须大于 `header_row`

#### 示例1：简单模板

```
第1行：表头（序号 | 姓名 | 卡号 | ...）
第2行起：数据行
```

配置：
```json
{
  "header_row": 1,
  "start_row": 2
}
```

#### 示例2：复杂模板（多行标题）

```
第1行：标题
第2行：说明
第3行：空行
第4行：表头
第5行起：数据行
```

配置：
```json
{
  "header_row": 4,
  "start_row": 5
}
```

---

## 字段映射配置

`field_mappings` 定义了如何从输入Excel文件的列映射到模板的列，以及如何转换数据。

### 配置结构

```json
"field_mappings": {
  "模板列名": {
    "source_column": "输入列名或列索引",
    "transform": "转换方式",
    "required": true
  }
}
```

### 字段说明

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `source_column` | string / integer | ✅ | 输入Excel中的列名或列索引（0-based） |
| `transform` | string | ✅ | 数据转换转换方式，见下方 |
| `required` | boolean | ✅ | 该字段是否必填 |

### source_column 使用方式

#### 方式1：使用列名（推荐）

```json
{
  "姓名": {
    "source_column": "姓名",
    "transform": "none",
    "required": true
  }
}
```

当输入Excel的表头包含"姓名"列时，会自动匹配。

#### 方式2：使用列索引

```json
{
  "姓名": {
    "source_column": 0,
    "transform": "none",
    "required": true
  }
}
```

`0` 表示第1列，`1` 表示第2列，以此类推。

### transform 转换方式

| 值 | 说明 | 适用场景 |
|-----|------|----------|
| `"none"` | 不进行任何转换，直接复制原值 | 姓名、文本等不需要转换的字段 |
| `"date_format"` | 日期格式转换，统一转换为 `YYYY-MM-DD` 格式 | 日期字段 |
| `"amount_decimal"` | 金额舍入转换，保留指定位数小数 | 金额字段 |
| `"card_number"` | 卡号格式化，移除分隔符并执行 Luhn 校验 | 银行卡号 |

### 示例

```json
"field_mappings": {
  "姓名": {
    "source_column": "姓名",
    "transform": "none",
    "required": true
  },
  "卡号": {
    "source_column": "卡号",
    "transform": "card_number",
    "required": true
  },
  "金额": {
    "source_column": "金额",
    "transform": "amount_decimal",
    "required": true
  },
  "日期": {
    "source_column": "日期",
    "transform": "date_format",
    "required": true
  }
}
```

---

## 转换配置

`transformations` 定义了各种数据转换方式的具体参数。

### 配置结构

```json
"transformations": {
  "date_format": { /* 日期转换参数 */ },
  "amount_decimal": { /* 金额转换参数 */ },
  "card_number": { /* 卡号转换参数 */ }
}
```

### 1. date_format（日期转换）

定义日期格式转换的参数。

| 字段名 | 类型 | 必填 | 说明 | 默认值 |
|--------|------|------|------|--------|
| `output_format` | string | ✅ | 输出日期格式 | `"YYYY-MM-DD"` |

**支持的输入日期格式**：

| 格式 | 示例 |
|------|------|
| `YYYY-MM-DD` | `2024-01-15` |
| `DD/MM/YYYY` | `15/01/2024` |
| `MM/DD/YYYY` | `01/15/2024` |
| `YYYY年MM月DD日` | `2024年01月15日` |
| `YYYY-M-D` | `2024-1-15` |
| `YYYY/MM/DD` | `2024/01/15` |

**输出格式**：所有日期统一转换为 `YYYY-MM-DD` 格式

**示例**：
```json
"transformations": {
  "date_format": {
    "output_format": "YYYY-MM-DD"
  }
}
```

### 2. amount_decimal（金额转换）

定义金额舍入转换的参数。

| 字段名 | 类型 | 必填 | 说明 | 默认值 |
|--------|------|------|------|--------|
| `decimal_places` | integer | ✅ | 保留小数位数 | `2` |
| `rounding` | string | ✅ | 舍入方式，目前仅支持 `"round"`（四舍五入） | `"round"` |

**转换示例**：

| 输入值 | `decimal_places: 2` | `decimal_places: 4` |
|--------|--------------------|--------------------|
| `123.456789` | `123.46` | `123.4568` |
| `100.5` | `100.50` | `100.5000` |
| `78.9` | `78.90` | `78.9000` |

**示例**：
```json
"transformations": {
  "amount_decimal": {
    "decimal_places": 2,
    "rounding": "round"
  }
}
```

### 3. card_number（卡号转换）

定义银行卡号格式化转换的参数。

| 字段名 | 类型 | 必填 | 说明 | 默认值 |
|--------|------|------|------|--------|
| `remove_formatting` | boolean | ✅ | 是否移除格式字符（空格、横杠等） | `true` |
| `luhn_validation` | boolean | ✅ | 是否执行 Luhn 校验 | `true` |

**转换步骤**：

1. **移除格式字符**（如果 `remove_formatting: true`）：
   - 移除空格：`6222 1234 5678 9012` → `6222123456789012`
   - 移除横杠：`6222-1234-5678-9012` → `6222123456789012`
   - 移除其他非数字字符

2. **Luhn 校验**（如果 `luhn_validation: true`）：
   - 从右向左遍历
   - 偶数位（从右数）的数字乘以2
   - 如果乘积大于9，则减去9
   - 所有数字相加
   - 总和能被10整除则有效，否则抛出错误

**Luhn 算法示例**：

卡号：`6222123456789012`

从右向左：`2 1 0 9 8 7 6 5 4 3 2 1 2 2 2 6`

偶数位乘以2：`2 2 0 18 8 14 6 10 4 6 2 2 2 4 2 12`

减去9（如果>9）：`2 2 0 9 8 5 6 1 4 6 2 2 2 4 2 3`

总和：2+2+0+9+8+5+6+1+4+6+2+2+2+4+2+3 = **58**

58 不能被10整除 → **卡号无效**

**示例**：
```json
"transformations": {
  "card_number": {
    "remove_formatting": true,
    "luhn_validation": true
  }
}
```

---

## 验证规则配置

`validation_rules` 定义数据验证规则，确保输入数据的正确性。

### 配置结构

```json
"validation_rules": {
  "required_fields": ["字段1", "字段2"],
  "data_types": {
    "字段名": "数据类型"
  }
}
```

### 1. required_fields（必填字段）

列出所有必填的字段名称（模板列名）。

**规则**：
- 如果字段为空或不存在，验证失败
- 支持的字段包括 `field_mappings` 中定义的字段

**示例**：
```json
"validation_rules": {
  "required_fields": ["姓名", "卡号", "金额", "日期"]
}
```

### 2. data_types（数据类型验证）

定义字段的数据类型，确保数据格式正确。

**支持的数据类型**：

| 类型名 | 说明 | 验证规则 |
|--------|------|----------|
| `"numeric"` | 数值类型 | 可以被解析为 `int` 或 `float` |
| `"integer"` | 整数类型 | 可以被解析为 `int` |
| `"float"` | 浮点数类型 | 可以被解析为 `float` |
| `"string"` | 字符串类型 | 任何字符串都有效 |
| `"boolean"` | 布尔类型 | `true` 或 `false` |
| `"date"` | 日期类型 | 可以被日期转换器解析 |

**示例**：
```json
"validation_rules": {
  "data_types": {
    "金额": "numeric",
    "日期": "date",
    "姓名": "string",
    "年龄": "integer"
  }
}
```

---

## 高级功能配置

以下配置项都是可选的，根据实际需求选择启用。

---

## 固定值配置

`fixed_values` 为所有数据行的某些列填写固定值。

### 配置结构

```json
"fixed_values": {
  "模板列名": "固定值"
}
```

### 使用场景

- 填写固定的省份、城市信息
- 填写固定的业务类型
- 填写固定的银行名称等

### 示例

```json
"fixed_values": {
  "省份": "浙江省",
  "城市": "杭州市",
  "业务类型": "工资代发",
  "银行": "中国农业银行"
}
```

### 注意事项

- 固定值对所有数据行生效
- 如果 `field_mappings` 中也配置了相同的列，`fixed_values` 优先级更高
- 值必须是字符串类型

---

## 自动编号配置

`auto_number` 自动生成序号列，方便数据行序管理。

### 配置结构

`auto_number` 是一个完整的配置对象。

| 字段名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `enabled` | boolean | ✅ | 是否启用自动编号 | `true` |
| `column_name` | string | ✅ | 模板中序号列的列名 | `"序号"` |
| `start_from` | integer | ✅ | 起始编号 | `1` |

### 使用场景

- 需要为每行数据添加序号
- 便于数据追踪和统计

### 示例

```json
"auto_number": {
  "enabled": true,
  "column_name": "序号",
  "start_from": 1
}
```

### 效果

| 序号 | 姓名 | 金额 |
|-----|------|------|
| 1 | 张三 | 5000.00 |
| 2 | 李四 | 6000.00 |
| 3 | 王五 | 7000.00 |

### 注意事项

- 序号从 `start_from` 开始递增
- 如果输入Excel中已经有该列，会被覆盖
- 序号列不需要在 `field_mappings` 中配置

---

## 银行支行映射配置

`bank_branch_mapping` 将输入Excel的"开户银行"列的值映射到模板的"开户支行"列。

### 配置结构

`bank_branch_mapping` 是一个完整的配置对象。

| 字段名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `enabled` | boolean | ✅ | 是否启用银行支行映射 | `true` |
| `source_column` | string | ✅ | 输入Excel中开户银行列的列名 | `"开户银行"` |
| `target_column` | string | ✅ | 模板中开户支行列的列名 | `"开户支行"` |

### 使用场景

- 输入Excel包含"开户银行"列
- 模板需要"开户支行"列
- 两列的值相同，只是列名不同

### 示例

```json
"bank_branch_mapping": {
  "enabled": true,
  "source_column": "开户银行",
  "target_column": "开户支行"
}
```

### 效果

输入Excel：

| 姓名 | 开户银行 | 金额 |
|------|----------|------|
| 张三 | 中国农业银行杭州分行 | 5000.00 |

输出模板：

| 姓名 | 开户支行 | 金额 |
|------|----------|------|
| 张三 | 中国农业银行杭州分行 | 5000.00 |

### 注意事项

- 该功能只是简单地将 `source_column` 的值复制到 `target_column`
- 不需要进行复杂的映射或转换
- 如果目标列已在 `field_mappings` 中配置，会被覆盖

---

## 月份类型映射配置

`month_type_mapping` 根据命令行传入的月份参数，自动填写收入类型列。

### 配置结构

`month_type_mapping` 是一个完整的配置对象。

| 字段名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `enabled` | boolean | ✅ | 是否启用月份类型映射 | `true` |
| `target_column` | string | ✅ | 模板中收入类型列的列名 | `"收入类型"` |
| `month_format` | string | ✅ | 月份数据的格式模板，`{month}` 会被替换为月份值 | `"{month}月收入"` |
| `bonus_value` | string | ✅ | 当月份参数为"年终奖"时填写的值 | `"年终奖"` |
| `compensation_value` | string | ✅ | 当月份参数为"补偿金"时填写的值 | `"补偿金"` |

### 月份参数对应关系

命令行传入的月份参数会按以下规则处理：

| 月份参数 | 填写值 | 格式说明 |
|----------|--------|----------|
| `"01"` ~ `"12"` | 使用 `month_format` 模板 | 如 `{month}月收入` → `"01月收入"` |
| `"1"` ~ `"9"` | 使用 `month_format` 模板 | 如 `{month}月收入` → `"1月收入"` |
| `"年终奖"` | 使用 `bonus_value` | 如 `"年终奖"` |
| `"补偿金"` | 使用 `compensation_value` | 如 `"补偿金"` |

### 示例

```json
"month_type_mapping": {
  "enabled": true,
  "target_column": "收入类型",
  "month_format": "{month}月收入",
  "bonus_value": "年终奖",
  "compensation_value": "补偿金"
}
```

### 使用场景

命令行执行：

```bash
# 1月工资
python main.py input.xlsx 农业银行 01

# 年终奖
python main.py input.xlsx 农业银行 年终奖

# 补偿金
python main.py input.xlsx 农业银行 补偿金
```

### 效果

| 姓名 | 收入类型 | 金额 |
|------|----------|------|
| 张三 | 01月收入 | 5000.00 |

或

| 姓名 | 收入类型 | 金额 |
|------|----------|------|
| 张三 | 年终奖 | 10000.00 |

### 注意事项

- `month_format` 中必须包含 `{month}` 占位符
- 月份参数会在程序启动时进行验证
- 无效的月份参数会导致程序退出

---

## 动态模板选择配置

`template_selector` 根据输入Excel的"开户银行"字段自动选择不同的模板。

### 配置结构

`template_selector` 是一个完整的配置对象。

| 字段名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `enabled` | boolean | ✅ | 是否启用动态模板选择 | `true` |
| `default_bank` | string | ✅ | 默认银行名称，当开户银行等于此值时使用默认模板 | `"中国农业银行"` |
| `special_template` | string | ✅ | 特殊模板路径，当开户银行不等于默认银行时使用此模板 | `"templates/example_special_template.xlsx"` |

### 工作原理

1. 读取输入Excel的"开户银行"列
2. 将数据按"开户银行"值分成两组：
   - **默认组**：`开户银行 == default_bank` → 使用 `template_path`（默认模板）
   - **特殊组**：`开户银行 != default_bank` → 使用 `special_template`（特殊模板）
3. 两组数据分别写入对应的模板文件
4. 生成两个输出文件

### 使用场景

- 同一批数据包含不同银行的卡片
- 不同银行需要使用不同的模板格式
- 需要将数据拆分到多个输出文件

### 示例

```json
"template_selector": {
  "enabled": true,
  "default_bank": "中国农业银行",
  "special_template": "templates/example_special_template.xlsx"
}
```

### 输入Excel示例

| 姓名 | 卡号 | 开户银行 | 金额 |
|------|------|----------|------|
| 张三 | 6222... | 中国农业银行 | 5000.00 |
| 李四 | 6225... | 中国工商银行 | 6000.00 |
| 王五 | 6222... | 中国农业银行 | 7000.00 |

### 处理结果

**默认组**（`农业银行.xlsx`）：

| 姓名 | 卡号 | 金额 |
|------|------|------|
| 张三 | 6222... | 5000.00 |
| 王五 | 6222... | 7000.00 |

**特殊组**（`工商银行.xlsx`）：

| 姓名 | 卡号 | 金额 |
|------|`------|------|
| 李四 | 6225... | 6000.00 |

### 输出文件命名

- 单模板模式：`{unit_name}_{month}_{timestamp}.xlsx`
  - 示例：`农业银行_01_20240115_143025.xlsx`
- 动态模板模式：`{unit_name}_{template_name}_{month}_{timestamp}.xlsx`
  - 默认模板：`农业银行_农业银行模板_01_20240115_143025.xlsx`
  - 特殊模板：`农业银行_工商银行模板_01_20240115_143025.xlsx`

### 注意事项

- 启用此功能时，会生成两个或多个输出文件
- 输入Excel必须包含"开户银行"列
- 如果所有数据的"开户银行"都相同，只会生成一个文件
- 模板文件路径可以使用相对路径或绝对路径

---

## 配置验证规则

系统会在启动时自动验证配置文件的正确性，以下规则必须满足：

### 顶层验证

1. ✅ `version` 字段必须存在
2. ✅ `organization_units` 字段必须存在且不为空
3. ✅ `organization_units` 必须是字典类型

### 单位配置验证

1. ✅ 必填字段必须存在：
   - `template_path`
   - `header_row`
   - `field_mappings`
   - `transformations`
2. ✅ `template_path` 必须是字符串
3. ✅ `header_row` 必须是整数，且 ≥ 1
4. ✅ `start_row`（如果指定）必须 > `header_row`
5. ✅ `field_mappings` 必须是字典
6. ✅ `transformations` 必须是字典

### 字段映射验证

1. ✅ 每个映射必须有 `source_column`、`transform`、`required` 字段
2. ✅ `transform` 必须是以下值之一：
   - `"none"`
   - `"date_format"`
   - `"amount_decimal"`
   - `"card_number"`

### 转换配置验证

1. ✅ 如果使用了 `date_format`，`transformations.date_format` 必须存在
2. ✅ 如果使用了 `amount_decimal`，`transformations.amount_decimal` 必须存在
3. ✅了 `card_number`，`transformations.card_number` 必须存在

### 验证错误示例

```json
// 错误1：缺少必填字段
{
  "version": "1.0"
  // 缺少 organization_units
}

// 错误2：header_row 必须大于等于 1
{
  "header_row": 0
}

// 错误3：start_row 必须大于 header_row
{
  "header_row": 2,
  "start_row": 2  // 应该是 3 或更大
}

// 错误4：transform 值无效
{
  "transform": "invalid_transform"
}
```

---

## 完整示例到一个完整的配置文件示例：

```json
{
  "version": "1.0",
  "organization_units": {
    "农业银行": {
      "template_path": "templates/example_template.xlsx",
      "header_row": 1,
      "start_row": 2,
      "field_mappings": {
        "姓名": {
          "source_column": "姓名",
          "transform": "none",
          "required": true
        },
        "卡号": {
          "source_column": "卡号",
          "transform": "card_number",
          "required": true
        },
        "金额": {
          "source_column": "金额",
          "transform": "amount_decimal",
          "required": true
        },
        "日期": {
          "source_column": "日期",
          "transform": "date_format",
          "required": true
        }
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
      },
      "template_selector": {
        "enabled": true,
        "default_bank": "中国农业银行",
        "special_template": "templates/example_special_template.xlsx"
      },
      "transformations": {
        "date_format": {
          "output_format": "YYYY-MM-DD"
        },
        "amount_decimal": {
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
    "工商银行": {
      "template_path": "templates/complex_template.xlsx",
      "header_row": 4,
      "start_row": 5,
      "field_mappings": {
        "客户姓名": {
          "source_column": "姓名",
          "transform": "none",
          "required": true
        },
        "银行卡号": {
          "source_column": "卡号",
          "transform": "card_number",
          "required": true
        },
        "工资金额": {
          "source_column": "金额",
          "transform": "amount_decimal",
          "required": true
        },
        "工资日期": {
          "source_column": "日期",
          "transform": "date_format",
          "required": true
        }
      },
      "fixed_values": {
        "省": "北京市",
        "类型": "工资"
      },
      "transformations": {
        "date_format": {
          "output_format": "YYYY-MM-DD"
        },
        "amount_decimal": {
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
    }
  }
}
```

---

## 最佳实践

### 1. 配置文件管理

- ✅ 使用版本控制（Git）管理配置文件
- ✅ 为不同环境创建不同的配置文件（开发、测试、生产）
- ✅ 使用注释（通过JSON5或外部文档）说明复杂配置
- ❌ 不要在配置文件中硬编码敏感信息（密码、密钥）

### 2. 模板文件管理

- ✅ 将模板文件放在 `templates/` 目录下
- ✅ 使用有意义的文件名（如 `农业银行模板.xlsx`）
- ✅ 在模板文件中保留格式和公式，便于后续使用
- ✅ 定期备份模板文件

### 3. 字段映射

- ✅ 使用列名而不是列索引，提高可读性
- ✅ 为每个字段设置合理的 `required` 值
`- ✅ 根据实际需求选择合适的 `transform` 类型
- ❌ 避免在 `source_column` 中混用列名和列索引

### 4. 转换配置

- ✅ 根据业务需求设置 `decimal_places`
- ✅ 启用 Luhn 校验确保卡号有效性
- ✅ 统一日期格式，避免后续处理问题
- ❌ 不要在金额转换中设置过多小数位

### 5. 验证规则

- ✅ 设置合理的必填字段，确保数据完整性
- ✅ 对关键字段（金额、日期）进行类型验证
- ✅ 定期检查验证错误日志，发现数据质量问题
- ❌ 不要设置过多的必填字段，影响灵活性

### 6. 高级功能

- ✅ 根据实际需求启用高级功能
- ✅ 使用 `fixed_values` 填写固定信息，减少手动操作
- ✅ 启用 `auto_number` 便于数据追踪
- ✅ 合理使用 `template_selector` 处理多银行场景

### 7. 错误处理

- ✅ 仔细阅读错误日志，快速定位问题
- ✅ 验证输入数据格式是否符合预期
- ✅ 检查配置文件是否正确
- ✅ 验证模板文件是否存在且格式正确

### 8. 性能优化

- ✅ 处理大量数据时，考虑分批处理
- ✅ 使用合理的输出目录结构
- ✅ 定期清理旧的输出文件
- ✅ 使用日志记录处理进度

---

## 常见问题

### Q1: 配置文件放在哪里？

**A**: 默认配置文件位于项目根目录的 `config.json`。可以通过 `--config` 参数指定自定义配置文件路径。

```bash
python main.py input.xlsx 单位名称 01 --config custom_config.json
```

### Q2: 如何添加新的单位配置？

**A**: 在 `organization_units` 对象中添加新的键值对：

```json
"organization_units": {
  "农业银行": { /* 配置 */ },
  "工商银行": { /* 配置 */ },
  "建设银行": { /* 新单位配置 */ }
}
```

### Q3: `header_row` 和 `start_row` 是从0还是从1开始？

**A**: 从1开始。第1行是表头，第2行是第一个数据行。

### Q4: 如何处理多银行数据？

**A**: 启用 `template_selector` 功能：

```json
"template_selector": {
  "enabled": true,
  "default_bank": "中国农业银行",
  "special_template": "templates/other_banks.xlsx"
}
````

### Q5: 日期格式不匹配怎么办？

**A**: 系统支持多种日期格式，如果格式仍不匹配，请检查：
1. 输入Excel的日期列格式
2. 是否为文本格式而非日期格式
3. 日期值是否符合支持的格式

**支持的日期格式**：
- `YYYY-MM-DD`
- `DD/MM/YYYY`
- `MM/DD/YYYY`
- `YYYY年MM月DD日`
- `YYYY-M-D`
- `YYYY/MM/DD`

### Q6: 卡号校验失败怎么办？

**A**: Luhn 校验失败可能的原因：
1. 卡号本身无效
2. 卡号包含非数字字符（如字母）
3. 卡号长度不正确（通常16-19位）

如果需要禁用Luhn校验，设置：

```json
"transformations": {
  "card_number": {
    "luhn_validation": false
  }
}
```

### Q7: 如何自定义输出文件名？

**A**: 使用 `--output-filename-template` 参数：

```bash
python main.py input.xlsx 单位名称 01 \
  --output-filename-template "工资_{month}_{timestamp}.xlsx"
```

### Q8: `field_mappings` 中的 `source_column` 支持列名和列索引，哪个更好？

**A**: 推荐使用列名，原因：
- 更易读和维护
- 列顺序变化时不易出错
- 便于理解配置意图

如果列名不确定或频繁变化，可以使用列索引（0-based）。

### Q9: 如何处理金额的舍入问题？

**A**: 通过 `transformations.amount_decimal` 配置：

```json
"transformations": {
  "amount_decimal": {
    "decimal_places": 2,  // 保留2位小数
    "rounding": "round"    // 四舍五入
  }
}
```

### Q10: 如何禁用某个高级功能？

**A**: 将对应功能的 `enabled` 设置为 `false`：

```json
"auto_number": {
  "enabled": false
}
```

或直接删除该配置项（如果该功能是可选的）。

### Q11: 配置文件支持注释吗？

**A**: 标准 JSON 不支持注释。如果需要注释，可以：
1. 使用 JSON5 格式（需要第三方库支持）
2. 在外部文档（如本文档）中说明
3. 使用字段说明（如 `_comment` 字段）

### Q12: 如何验证配置文件是否正确？

**A**: 运行程序时，系统会自动验证配置文件。如果配置有误，会显示详细的错误信息。

常见的验证错误：
- 缺少必填字段
- 字段类型不正确
- 行号不符合规则（start_row > header_row）
- transform 值无效

### Q13: 如何处理空值或缺失值？

**A**:
- 如果字段标记为 `required: true`，空值会导致验证失败
- 如果字段标记为 `required: false`，空值会被跳过
- 建议在 `field_mappings` 中合理设置 `required` 值

### Q14: 模板文件的格式会被保留吗？

**A**: 会保留以下格式：
- 单元格格式（字体、颜色、边框等）
- 公式
- 合并单元格
- 列宽、行高

系统只会清除数据行，保留模板的所有格式。

### Q15: 如何查看详细的处理日志？

**A**: 程序默认输出 INFO 级别日志。日志格式：

```
2024-01-15 14:30:25 - __main__ - INFO - 加载配置文件: config.json
2024-01-15 14:30:25 - config_loader - INFO - 配置文件加载成功
```

日志包含：
- 配置加载和验证
- Excel文件读取
- 数据转换和验证
- 模板写入
- 错误和警告信息

### Q16: 支持哪些Excel格式？

**A**: 支持三种格式：
1. `.xlsx` - 使用 openpyxl 库
2. `.csv` - 使用 csv 模块
3. `.xls` - 使用 xlrd/xlwt 库

### Q17: 如何处理非常大的Excel文件？

**A**: 建议：
1. 分批处理数据
2. 关闭不必要的程序释放内存
3. 使用SSD硬盘提高I/O性能
4. 定期清理临时文件

### Q18: `start_row` 的默认值是什么？

**A**: 如果不指定 `start_row`，默认值为 `header_row + 1`。

例如，如果 `header_row: 1`，则 `start_row` 默认为 `2`。

### Q19: 如何处理多个输出文件？

**A**: 当启用 `template_selector` 时，会生成多个输出文件：

```bash
# 默认模板输出
农业银行_农业银行模板_01_20240115_143025.xlsx

# 特殊模板输出
农业银行_工商银行模板_01_20240115_143025.xlsx
```

### Q20: 配置文件的版本有什么用？

**A**: `version` 字段用于配置兼容性管理：
- 当前版本为 "1.0"
- 未来版本可能会引入新功能或废弃旧功能
- 系统会根据版本号进行适当的兼容性处理

---

## 附录：快速参考

### 必填字段清单

**顶层**：
- `version`
- `organization_units`

**单位配置**：
- `template_path`
- `header_row`
- `field_mappings`
- `transformations`

### 可选字段清单

**单位配置**：
- `start_row`
- `fixed_values`
- `auto_number`
- `bank_branch_mapping`
- `month_type_mapping`
- `template_selector`
- `validation_rules`

### Transform 类型清单

| 值 | 说明 |
|-----|------|
| `none` | 不转换 |
| `date_format` | 日期转换 |
| `amount_decimal` | 金额转换 |
| `card_number` | 卡号转换 |

### 数据类型清单

| 类型 | 说明 |
|------|------|
| `numeric` | 数值 |
| `integer` | 整数 |
| `float` | 浮点数 |
| `string` | 字符串 |
| `boolean` | 布尔值 |
| `date` | 日期 |

---

## 更新日志

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0 | 2024-01-15 | 初始版本 |

---

## 相关文档

- [README.md](README.md) - 项目概览和使用说明
- [tests/](tests/) - 测试用例示例
- [templates/](templates/) - 模板文件示例

---

**文档版本**: 1.0
**最后更新**: 2024-01-15
**维护者**: Bank Template Processing Team
