# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all, collect_dynamic_libs

block_cipher = None

_websockets_datas, _websockets_binaries, _websockets_hidden = collect_all('websockets')

a = Analysis(
    ['ledgermate_desktop.py'],
    pathex=['src'],
    binaries=[
        ('C:\\Users\\USER\\AppData\\Local\\Programs\\Python\\Python312\\DLLs\\_sqlite3.pyd', 'DLLs'),
        ('C:\\Users\\USER\\AppData\\Local\\Programs\\Python\\Python312\\DLLs\\sqlite3.dll', 'DLLs'),
    ] + collect_dynamic_libs('sqlite3'),
    datas=[
        ('static', 'static'),
        ('src/ledgermate', 'ledgermate'),
        ('model', 'model'),
        ('docs', 'docs'),
        ('README.md', '.'),
        *_websockets_datas,
    ],
    hiddenimports=[
        'ledgermate',
        'ledgermate.api',
        'ledgermate.ledger',
        'ledgermate.llm',
        'ledgermate.services',
        'ledgermate.export',
        'ledgermate.validation',
        'ledgermate.schema',
        'ledgermate.config',
        'webview',
        'webview.platforms.winforms',
        'uvicorn',
        'fastapi',
        'fastapi.middleware.cors',
        'fastapi.staticfiles',
        'starlette',
        'anyio',
        'pydantic',
        'websockets',
        *_websockets_hidden,
        'dotenv',
        'rich',
        'sounddevice',
        'numpy',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['pyinstaller_rthook.py'],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries + _websockets_binaries,
    a.zipfiles,
    a.datas,
    [],
    name='LedgerMate',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
