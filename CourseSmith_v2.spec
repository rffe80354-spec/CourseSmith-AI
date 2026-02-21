# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for CourseSmith_v2 (app_custom_ui.py).
This spec includes all necessary data files and hidden imports.
Uses --onedir mode for faster startup and selective --collect-submodules.

Usage:
    pyinstaller CourseSmith_v2.spec
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Get customtkinter data files
ctk_datas = collect_data_files('customtkinter')

# Collect only necessary submodules instead of entire packages
ctk_submodules = collect_submodules('customtkinter')
reportlab_submodules = collect_submodules('reportlab')

# Prepare data files list
datas_list = [
    # Include fonts directory with TTF files for PDF generation (Cyrillic support)
    ('fonts', 'fonts'),
    # Include resources directory with icons
    ('resources', 'resources'),
] + ctk_datas

# Include .env file only if it exists
if os.path.exists('.env'):
    datas_list.append(('.env', '.'))

# Define analysis
a = Analysis(
    ['app_custom_ui.py'],
    pathex=[],
    binaries=[],
    datas=datas_list,
    hiddenimports=[
        # Local modules that app_custom_ui.py imports directly or indirectly
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
        'epub_exporter',
        'markdown_exporter',
        'pdf_engine',
        'product_templates',
        'project_manager',
        'secrets_manager',  # For Supabase API key retrieval
        # Standard library modules that might be missed
        'babel.numbers',
        # ReportLab modules for PDF generation
        'reportlab',
        'reportlab.pdfbase',
        'reportlab.pdfbase.ttfonts',
        'reportlab.pdfbase.pdfmetrics',
        'reportlab.lib.pagesizes',
        'reportlab.lib.units',
        'reportlab.lib.colors',
        'reportlab.platypus',
        # python-docx for DOCX export
        'docx',
        'docx.shared',
        'docx.enum',
        'docx.enum.text',
        # ebooklib for EPUB export
        'ebooklib',
        'ebooklib.epub',
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
        # lxml for document processing
        'lxml',
        'lxml._elementpath',
        'lxml.etree',
    ] + ctk_submodules + reportlab_submodules,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

# Use --onedir mode (COLLECT) for faster startup instead of --onefile
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CourseSmith_v2',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # windowed mode
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/coursesmithai.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CourseSmith_v2',
)
