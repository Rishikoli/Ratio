# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

# Collect rapidocr_onnxruntime and onnxruntime resources & binaries
datas = [
    ('backend/ratio/core/bank_configs', 'ratio/core/bank_configs'),
    ('frontend/dist', 'frontend_dist')
]
binaries = []
hiddenimports = [
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.http.h11_impl',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'engineio.async_drivers.asgi',
    'fitz',
    'pymupdf',
    'cv2',
    'rapidocr_onnxruntime',
    'onnxruntime',
    'openpyxl',
    'pydantic'
]

# Collect extra data and binaries from rapidocr_onnxruntime, rapid_layout, rapidfuzz
for pkg in ['rapidocr_onnxruntime', 'rapid_layout', 'rapidfuzz']:
    try:
        tmp_datas, tmp_binaries, tmp_hidden = collect_all(pkg)
        datas.extend(tmp_datas)
        binaries.extend(tmp_binaries)
        hiddenimports.extend(tmp_hidden)
    except Exception as ex:
        print(f"PyInstaller collect_all warning for {pkg}:", ex)

a = Analysis(
    ['backend/app.py'],
    pathex=['backend'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'tkinter', 'PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'scipy', 'notebook', 'IPython'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Ratio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=True,
    upx=True,
    upx_exclude=[],
    name='Ratio',
)
