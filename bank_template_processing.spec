# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包规格文件
用于将银行卡进卡模板处理系统打包为 Windows 可执行文件
"""

import sys
from pathlib import Path

# 获取项目根目录
project_root = Path(SPECPATH)

a = Analysis(
    ['main.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        # 包含配置示例文件
        ('config.example.json', '.'),
        # 包含文档
        ('README.md', '.'),
        ('配置文件说明.md', '.'),
    ],
    hiddenimports=[
        # openpyxl 相关
        'openpyxl',
        'openpyxl.cell',
        'openpyxl.workbook',
        'openpyxl.worksheet',
        'openpyxl.styles',
        'openpyxl.utils',
        # xlrd/xlwt 相关
        'xlrd',
        'xlwt',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的模块以减小体积
        'tkinter',
        'unittest',
        'test',
        'tests',
        'pytest',
        'pytest_cov',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='bank-template-processing',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # 命令行程序，需要控制台
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='bank-template-processing',
)
