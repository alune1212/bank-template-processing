模板目录说明

本目录用于演示模板目录结构与放置方式，不包含任何真实模板文件。

使用方法：
1. 在项目根目录创建 `templates/` 目录。
2. 将实际银行模板文件放入 `templates/`。
3. 在 `config.json` 中的 `template_path` 填写相对路径，例如：
   - `templates/农业银行模板.xlsx`
   - `templates/跨行模板.xls`

注意事项：
- `templates/` 已加入 `.gitignore`，不会被 Git 跟踪。
- 请勿提交真实模板文件到仓库。
