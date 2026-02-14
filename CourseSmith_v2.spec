# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for CourseSmith_v2 (main.py).
This spec includes all necessary data files and hidden imports.

Usage:
    pyinstaller CourseSmith_v2.spec
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Get customtkinter data files
ctk_datas = collect_data_files('customtkinter')

# Collect additional package data
babel_datas = collect_data_files('babel')
pydantic_datas = collect_data_files('pydantic')

# Define analysis
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Include fonts directory with TTF files for PDF generation
        ('fonts', 'fonts'),
        # Include resources directory with icons
        ('resources', 'resources'),
        # Include .env file for configuration (if exists)
        ('.env', '.'),
    ] + ctk_datas + babel_datas + pydantic_datas,
    hiddenimports=[
        # Local modules that main.py imports directly or indirectly
        'utils',
        'license_guard',
        'session_manager',
        'ai_manager',
        'ai_worker',
        'coursesmith_engine',
        'database_manager',
        'docx_exporter',
        'export_base',
        'generator',
        'html_exporter',
        'markdown_exporter',
        'pdf_engine',
        'product_templates',
        'project_manager',
        # Standard library modules that might be missed
        'babel.numbers',
        'pydantic',
        'pydantic.deprecated',
        'pydantic.deprecated.decorator',
        # ReportLab modules for PDF generation
        'reportlab.pdfbase',
        'reportlab.pdfbase.ttfonts',
        'reportlab.pdfbase.pdfmetrics',
        'reportlab.lib.pagesizes',
        'reportlab.lib.units',
        'reportlab.lib.colors',
        'reportlab.platypus',
        # Supabase and related modules
        'supabase',
        'gotrue',
        'postgrest',
        'storage3',
        'realtime',
        # NTP module for time sync
        'ntplib',
        # Cryptography
        'cryptography',
        'cryptography.fernet',
        # Other potentially needed modules
        'dotenv',
        'PIL',
        'PIL.Image',
        'requests',
        'json',
        'threading',
        'datetime',
        # tkinter
        'tkinter',
        'tkinter.messagebox',
        'tkinter.filedialog',
        # CustomTkinter submodules
        'customtkinter',
        'customtkinter.windows',
        'customtkinter.windows.widgets',
        # python-docx for DOCX export
        'docx',
        'docx.shared',
        'docx.enum',
        'docx.enum.text',
        'lxml',
        'lxml._elementpath',
        'lxml.etree',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

# Remove .env from datas if it doesn't exist
a.datas = [(dest, src, type_) for dest, src, type_ in a.datas 
           if not (dest == '.env' and not os.path.exists(src))]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='CourseSmith_v2',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # windowed mode
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/coursesmithai.ico',
)
