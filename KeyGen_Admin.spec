# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for KeyGen_Admin (admin_keygen.py).
This spec includes all necessary data files and hidden imports.

Usage:
    pyinstaller KeyGen_Admin.spec
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Get customtkinter data files
ctk_datas = collect_data_files('customtkinter')

# Prepare data files list
datas_list = [
    # Include resources directory with icons
    ('resources', 'resources'),
] + ctk_datas

# Include .env file only if it exists
if os.path.exists('.env'):
    datas_list.append(('.env', '.'))

# Define analysis
a = Analysis(
    ['admin_keygen.py'],
    pathex=[],
    binaries=[],
    datas=datas_list,
    hiddenimports=[
        # Local modules that admin_keygen.py imports directly or indirectly
        'utils',
        'license_guard',
        'database_manager',
        # Supabase and related modules
        'supabase',
        'gotrue',
        'postgrest',
        'storage3',
        'realtime',
        # Cryptography
        'cryptography',
        'cryptography.fernet',
        # Other potentially needed modules
        'dotenv',
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
        # ReportLab (used by utils)
        'reportlab.pdfbase',
        'reportlab.pdfbase.ttfonts',
        'reportlab.pdfbase.pdfmetrics',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='KeyGen_Admin',
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
    icon='resources/admin_keygen.ico',
)
