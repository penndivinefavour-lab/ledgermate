"""LedgerMate desktop launcher.

Starts the local FastAPI backend, waits for health, then opens the default
browser so the user never needs to open a terminal manually.
"""
from __future__ import annotations

import os
import sys
import tempfile
import threading
import time
import traceback
import webbrowser
from pathlib import Path

import uvicorn


LOG_PATH = Path(tempfile.gettempdir()) / "ledgermate_desktop.log"
HOST = "127.0.0.1"
PORT = int(os.environ.get("LEDGERMATE_PORT", "8000"))
HEALTH_URL = f"http://{HOST}:{PORT}/api/health"
FRONTEND_URL = f"http://{HOST}:{PORT}/static/index.html"
STARTUP_TIMEOUT = 60


def _log(text: str) -> None:
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as handle:
            handle.write(text + "\n")
    except Exception:
        pass


_log(f"=== LEDGERMATE DESKTOP START === pid={os.getpid()} cwd={Path.cwd()}")


def _unhandled_exception_handler(exc_type, exc_value, exc_traceback):
    try:
        log_path = Path(tempfile.gettempdir()) / "ledgermate_desktop.log"
        with open(log_path, "a", encoding="utf-8") as handle:
            handle.write("=== UNHANDLED EXCEPTION ===\n")
            import traceback
            handle.write(''.join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
            handle.write("\n")
    except Exception:
        pass


sys.excepthook = _unhandled_exception_handler


def _start_backend() -> None:
    import os
    import sys
    import tempfile
    import traceback
    from pathlib import Path

    log_dir = Path(__file__).resolve().parents[1] / "logs"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    log_path = log_dir / "ledgermate_backend.log"
    try:
        with open(log_path, "a", encoding="utf-8") as handle:
            handle.write("=== BACKEND THREAD START ===\n")
            handle.write(f"cwd={Path.cwd()}\n")
            handle.write(f"sys.path={sys.path[:3]}\n")
            handle.flush()
    except Exception as exc:
        try:
            with open(Path(tempfile.gettempdir()) / "ledgermate_desktop.log", "a", encoding="utf-8") as handle:
                handle.write(f"BACKEND LOG SETUP ERROR: {exc}\n")
                handle.flush()
        except Exception:
            pass

    try:
        import fastapi_compat  # noqa: F401
    except Exception:
        pass

    repo_root = Path(__file__).resolve().parents[1]
    if hasattr(sys, "_MEIPASS"):
        src_path = str(Path(sys._MEIPASS) / "src")
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        os.chdir(Path(sys._MEIPASS))
    else:
        os.chdir(repo_root)
        if str(repo_root / "src") not in sys.path:
            sys.path.insert(0, str(repo_root / "src"))

    try:
        with open(log_path, "a", encoding="utf-8") as handle:
            handle.write("=== IMPORTING APP ===\n")
            handle.flush()
        python_dlls = Path(r'C:\Users\USER\AppData\Local\Programs\Python\Python312\DLLs')
        if python_dlls.exists() and str(python_dlls) not in sys.path:
            sys.path.insert(0, str(python_dlls))
            try:
                os.add_dll_directory(str(python_dlls))
            except Exception:
                pass
            with open(log_path, 'a', encoding='utf-8') as handle:
                handle.write(f'DLL DIR INJECT: {python_dlls}\n')
                handle.flush()
        from ledgermate.api import app
        with open(log_path, "a", encoding="utf-8") as handle:
            handle.write("APP IMPORT OK\n")
            handle.flush()
        import uvicorn
        port = int(os.environ.get("LEDGERMATE_PORT", "8000"))
        with open(log_path, "a", encoding="utf-8") as handle:
            handle.write(f"=== BACKEND START on 127.0.0.1:{port} ===\n")
            handle.flush()
        uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
    except Exception as exc:
        with open(log_path, "a", encoding="utf-8") as handle:
            handle.write(f"BACKEND ERROR: {exc}\n")
            handle.write(traceback.format_exc())
            handle.write("\n")
            handle.flush()


def _wait_for_health() -> bool:
    import urllib.request

    deadline = time.time() + STARTUP_TIMEOUT
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(HEALTH_URL, timeout=1) as response:
                if response.status == 200:
                    return True
        except Exception:
            time.sleep(0.25)
    return False


def main() -> int:
    if _wait_for_health():
        _log("Existing LedgerMate instance detected on port 8000.")
    else:
        _log("No existing instance. Starting backend...")
        server_thread = threading.Thread(target=_start_backend, daemon=True)
        server_thread.start()
        if not _wait_for_health():
            print("LedgerMate could not start. Your business data has not been modified.")
            return 1

    webbrowser.open(FRONTEND_URL)
    print(f"LedgerMate running at {FRONTEND_URL}")
    while _wait_for_health():
        time.sleep(5)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        try:
            log_path = Path(tempfile.gettempdir()) / "ledgermate_desktop.log"
            with open(log_path, "a", encoding="utf-8") as handle:
                handle.write("=== FATAL EXCEPTION IN MAIN ===\n")
                handle.write(f"{exc}\n")
                handle.write(traceback.format_exc())
                handle.write("\n")
        except Exception:
            pass
        raise
