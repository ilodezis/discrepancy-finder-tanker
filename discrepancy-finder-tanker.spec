# -*- mode: python ; coding: utf-8 -*-
import os

# Определяем пути
icon_file = os.path.abspath(os.path.join('assets', 'icons', 'ya_zapravki.ico'))
font_file = os.path.abspath(os.path.join('assets', 'fonts', 'Inter-VariableFont_opsz,wght.ttf'))

# Добавляем файлы в datas
datas = [
    (icon_file, 'assets/icons'),
    (font_file, 'assets/fonts'),
]

a = Analysis(
    ['discrepancy-finder-tanker.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Discrepancy Finder (Tanker Edition)',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Discrepancy Finder (Tanker Edition)'
)
