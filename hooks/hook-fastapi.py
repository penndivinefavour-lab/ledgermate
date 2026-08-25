"""PyInstaller hook for FastAPI staticfiles/middleware submodules."""
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules("fastapi")
