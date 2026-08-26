import os
import sys
from pathlib import Path

python_dlls = Path(r'C:\Users\USER\AppData\Local\Programs\Python\Python312\DLLs')
print(f'RTHOOK: python_dlls={python_dlls}')
print(f'RTHOOK: exists={python_dlls.exists()}')
print(f'RTHOOK: sys.path before={sys.path[:3]}')
if python_dlls.exists() and str(python_dlls) not in sys.path:
    sys.path.insert(0, str(python_dlls))
    print(f'RTHOOK: inserted dll path')
    try:
        os.add_dll_directory(str(python_dlls))
        print(f'RTHOOK: add_dll_directory ok')
    except Exception as exc:
        print(f'RTHOOK: add_dll_directory failed: {exc}')

try:
    import sqlite3
    print(f'RTHOOK: sqlite3 imported, version={sqlite3.sqlite_version}')
except Exception as exc:
    print(f'RTHOOK: sqlite3 import failed: {exc}')

import fastapi.middleware.cors
import fastapi.staticfiles
