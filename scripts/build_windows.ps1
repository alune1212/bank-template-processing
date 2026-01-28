<#
.SYNOPSIS
    Windows 打包脚本 - 将银行卡进卡模板处理系统打包为可执行文件

.DESCRIPTION
    此脚本执行以下步骤：
    1. 清理旧的构建产物
    2. 使用 PyInstaller 打包
    3. 复制运行所需的额外文件
    4. 生成可分发的 zip 压缩包

.NOTES
    前置条件：
    - uv (https://github.com/astral-sh/uv)
    - Python 3.13+
    - PyInstaller 在 dev 依赖组中，脚本会自动同步
#>

param(
    [switch]$SkipZip,
    [string]$OutputName = "bank-template-processing-win"
)

$ErrorActionPreference = "Stop"

# 获取脚本所在目录的上级目录（项目根目录）
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "银行卡进卡模板处理系统 - Windows 打包" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 步骤 1: 清理旧的构建产物
Write-Host "[1/4] 清理旧的构建产物..." -ForegroundColor Yellow
$DirsToClean = @("build", "dist", "__pycache__")
foreach ($dir in $DirsToClean) {
    if (Test-Path $dir) {
        Remove-Item -Recurse -Force $dir
        Write-Host "  已删除: $dir" -ForegroundColor Gray
    }
}

# 清理 .pyc 文件
Get-ChildItem -Recurse -Filter "*.pyc" -ErrorAction SilentlyContinue | Remove-Item -Force
Write-Host "  已清理 .pyc 缓存文件" -ForegroundColor Gray
Write-Host ""

# 步骤 2: 同步依赖并检查 PyInstaller
Write-Host "[2/4] 同步依赖并检查 PyInstaller..." -ForegroundColor Yellow
Write-Host "  正在同步 dev 依赖组（包含 PyInstaller）..." -ForegroundColor Gray
& uv sync --group dev
if ($LASTEXITCODE -ne 0) {
    Write-Host "错误: 无法同步依赖" -ForegroundColor Red
    exit 1
}
try {
    $pyinstallerVersion = & uv run pyinstaller --version 2>&1
    Write-Host "  PyInstaller 版本: $pyinstallerVersion" -ForegroundColor Gray
} catch {
    Write-Host "错误: 无法获取 PyInstaller 版本" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 步骤 3: 执行 PyInstaller 打包
Write-Host "[3/4] 执行 PyInstaller 打包..." -ForegroundColor Yellow
& uv run pyinstaller bank_template_processing.spec --noconfirm 2>&1 | ForEach-Object {
    if ($_ -match "WARNING.*upx") {
        # UPX 警告是正常的，只显示为灰色信息
        Write-Host $_ -ForegroundColor DarkGray
    } else {
        Write-Host $_
    }
}
# 检查是否生成了可执行文件，而不是仅依赖退出码（UPX 警告可能导致非零退出码）
if (-not (Test-Path "dist\bank-template-processing\bank-template-processing.exe")) {
    Write-Host "错误: PyInstaller 打包失败，未找到可执行文件" -ForegroundColor Red
    exit 1
}
Write-Host "  打包完成" -ForegroundColor Green
Write-Host ""

# 步骤 4: 复制额外文件并创建目录结构
Write-Host "[4/4] 准备分发目录..." -ForegroundColor Yellow
$DistDir = "dist\bank-template-processing"

# 创建 templates 目录（用户放置模板文件）
$TemplatesDir = "$DistDir\templates"
if (-not (Test-Path $TemplatesDir)) {
    New-Item -ItemType Directory -Path $TemplatesDir | Out-Null
    Write-Host "  已创建: templates\" -ForegroundColor Gray
}

# 创建 output 目录（默认输出目录）
$OutputDir = "$DistDir\output"
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
    Write-Host "  已创建: output\" -ForegroundColor Gray
}

# 复制 config.example.json（如果 spec 中未包含或需要额外复制）
if (Test-Path "config.example.json") {
    Copy-Item "config.example.json" "$DistDir\" -Force
    Write-Host "  已复制: config.example.json" -ForegroundColor Gray
}

# 创建快速使用说明
$QuickStartContent = @"
银行卡进卡模板处理系统 - 快速使用指南
========================================

1. 首次使用：
   - 将 config.example.json 复制为 config.json
   - 根据实际需求修改 config.json 中的配置

2. 准备文件：
   - 将银行模板文件放入 templates\ 目录
   - 确保 config.json 中的 template_path 指向正确的模板文件

3. 运行命令：
   打开命令提示符（CMD）或 PowerShell，执行：

   bank-template-processing.exe 输入文件.xlsx 单位名称 月份

   示例：
   bank-template-processing.exe input.xlsx 南京硕博睿达企业管理有限公司 01
   bank-template-processing.exe input.xlsx 南京硕博睿达企业管理有限公司 年终奖

4. 输出结果：
   处理后的文件将保存在 output\ 目录中

详细说明请参阅 README.md 和 配置文件说明.md
"@
$QuickStartContent | Out-File -FilePath "$DistDir\快速使用指南.txt" -Encoding UTF8
Write-Host "  已创建: 快速使用指南.txt" -ForegroundColor Gray

Write-Host ""

# 步骤 5: 创建 zip 压缩包
if (-not $SkipZip) {
    Write-Host "[5/5] 创建 zip 压缩包..." -ForegroundColor Yellow
    $ZipPath = "dist\$OutputName.zip"
    
    if (Test-Path $ZipPath) {
        Remove-Item $ZipPath -Force
    }
    
    Compress-Archive -Path $DistDir -DestinationPath $ZipPath -Force
    Write-Host "  已创建: $ZipPath" -ForegroundColor Green
    
    # 显示文件大小
    $ZipSize = (Get-Item $ZipPath).Length / 1MB
    Write-Host "  文件大小: $([math]::Round($ZipSize, 2)) MB" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "打包完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "输出目录: $DistDir" -ForegroundColor White
if (-not $SkipZip) {
    Write-Host "压缩包: dist\$OutputName.zip" -ForegroundColor White
}
Write-Host ""
Write-Host "目录结构:" -ForegroundColor White
Write-Host "  bank-template-processing\" -ForegroundColor Gray
Write-Host "    ├── bank-template-processing.exe  (主程序)" -ForegroundColor Gray
Write-Host "    ├── config.example.json           (配置示例)" -ForegroundColor Gray
Write-Host "    ├── README.md                     (说明文档)" -ForegroundColor Gray
Write-Host "    ├── 配置文件说明.md               (配置说明)" -ForegroundColor Gray
Write-Host "    ├── 快速使用指南.txt              (快速指南)" -ForegroundColor Gray
Write-Host "    ├── templates\                    (模板目录)" -ForegroundColor Gray
Write-Host "    └── output\                       (输出目录)" -ForegroundColor Gray
