模板目录说明

本目录仅用于说明 `templates/` 的目录结构和放置方式，不包含任何真实模板文件。

使用方式：

1. 在程序运行目录创建 `templates/` 目录。
2. 将实际银行模板文件放入 `templates/`。
3. 在 `config.json` 的 `template_path` 中填写相对路径，例如：
   - `templates/农业银行模板.xlsx`
   - `templates/跨行模板.xls`

路径说明：

- 源码运行时，相对路径会解析到项目根目录。
- 打包运行时，相对路径会解析到可执行文件所在目录。

注意事项：

- `templates/` 已加入 `.gitignore`，不会被 Git 跟踪。
- 请勿将真实模板文件提交到仓库。
- 推荐优先维护 `config.example.json` 中使用的新多规则组配置结构。
