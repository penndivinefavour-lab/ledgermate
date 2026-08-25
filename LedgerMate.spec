# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['ledgermate_desktop.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('static', 'static'),
        ('src/ledgermate', 'src/ledgermate'),
        ('model', 'model'),
        ('docs', 'docs'),
        ('README.md', '.'),
    ],
    hiddenimports=[
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
        'pydantic',
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
    a.binaries,
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
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
