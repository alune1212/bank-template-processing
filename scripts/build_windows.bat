@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo ========================================
echo 银行卡进卡模板处理系统 - Windows 打包
echo ========================================
echo.

:: 获取脚本所在目录的上级目录（项目根目录）
cd /d "%~dp0.."

:: 步骤 1: 清理旧的构建产物
echo [1/5] 清理旧的构建产物...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "__pycache__" rmdir /s /q "__pycache__"
echo   清理完成
echo.

:: 步骤 2: 检查 PyInstaller
echo [2/5] 检查 PyInstaller...
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo   PyInstaller 未安装，正在安装...
    pip install pyinstaller
    if errorlevel 1 (
        echo 错误: 无法安装 PyInstaller
        pause
        exit /b 1
    )
)
echo   PyInstaller 已就绪
echo.

:: 步骤 3: 执行 PyInstaller 打包
echo [3/5] 执行 PyInstaller 打包...
python -m PyInstaller bank_template_processing.spec --noconfirm
if errorlevel 1 (
    echo 错误: PyInstaller 打包失败
    pause
    exit /b 1
)
echo   打包完成
echo.

:: 步骤 4: 准备分发目录
echo [4/5] 准备分发目录...
set "DIST_DIR=dist\bank-template-processing"

:: 创建 templates 目录
if not exist "%DIST_DIR%\templates" mkdir "%DIST_DIR%\templates"
echo   已创建: templates\

:: 创建 output 目录
if not exist "%DIST_DIR%\output" mkdir "%DIST_DIR%\output"
echo   已创建: output\

:: 复制 config.example.json
if exist "config.example.json" (
    copy /y "config.example.json" "%DIST_DIR%\" >nul
    echo   已复制: config.example.json
)

:: 创建快速使用说明
(
echo 银行卡进卡模板处理系统 - 快速使用指南
echo ========================================
echo.
echo 1. 首次使用：
echo    - 将 config.example.json 复制为 config.json
echo    - 根据实际需求修改 config.json 中的配置
echo.
echo 2. 准备文件：
echo    - 将银行模板文件放入 templates\ 目录
echo    - 确保 config.json 中的 template_path 指向正确的模板文件
echo.
echo 3. 运行命令：
echo    打开命令提示符（CMD）或 PowerShell，执行：
echo.
echo    bank-template-processing.exe 输入文件.xlsx 单位名称 月份
echo.
echo    示例：
echo    bank-template-processing.exe input.xlsx 南京硕博睿达企业管理有限公司 01
echo    bank-template-processing.exe input.xlsx 南京硕博睿达企业管理有限公司 年终奖
echo.
echo 4. 输出结果：
echo    处理后的文件将保存在 output\ 目录中
echo.
echo 详细说明请参阅 README.md 和 配置文件说明.md
) > "%DIST_DIR%\快速使用指南.txt"
echo   已创建: 快速使用指南.txt
echo.

:: 步骤 5: 创建 zip 压缩包（需要 PowerShell）
echo [5/5] 创建 zip 压缩包...
set "ZIP_PATH=dist\bank-template-processing-win.zip"
if exist "%ZIP_PATH%" del /f "%ZIP_PATH%"

powershell -Command "Compress-Archive -Path '%DIST_DIR%' -DestinationPath '%ZIP_PATH%' -Force"
if errorlevel 1 (
    echo 警告: 无法创建 zip 压缩包，请手动压缩 dist\bank-template-processing 目录
) else (
    echo   已创建: %ZIP_PATH%
)
echo.

echo ========================================
echo 打包完成！
echo ========================================
echo.
echo 输出目录: %DIST_DIR%
echo 压缩包: %ZIP_PATH%
echo.
echo 目录结构:
echo   bank-template-processing\
echo     ├── bank-template-processing.exe  ^(主程序^)
echo     ├── config.example.json           ^(配置示例^)
echo     ├── README.md                     ^(说明文档^)
echo     ├── 配置文件说明.md               ^(配置说明^)
echo     ├── 快速使用指南.txt              ^(快速指南^)
echo     ├── templates\                    ^(模板目录^)
echo     └── output\                       ^(输出目录^)
echo.
pause
