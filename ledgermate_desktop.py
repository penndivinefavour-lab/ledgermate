"""LedgerMate desktop launcher.

Starts the local FastAPI backend, waits for health, then opens an embedded
browser window so the user never needs to open a terminal or browser manually.
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
import webview


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


def _start_backend() -> None:
    import os
    import sys
    import traceback

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

    log_path = Path("/tmp") / "ledgermate_backend.log"
    try:
        from ledgermate.api import app
        import uvicorn
        port = int(os.environ.get("LEDGERMATE_PORT", "8000"))
        with open(log_path, "a", encoding="utf-8") as handle:
            handle.write(f"=== BACKEND START on 127.0.0.1:{port} ===\n")
        uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
    except Exception:
        with open(log_path, "a", encoding="utf-8") as handle:
            handle.write("=== BACKEND ERROR ===\n")
            handle.write(traceback.format_exc())
            handle.write("\n")


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
    server_thread = threading.Thread(target=_start_backend, daemon=True)
    server_thread.start()

    if not _wait_for_health():
        print("LedgerMate could not start. Your business data has not been modified.")
        return 1

    if not _wait_for_health():
        print("LedgerMate could not start. Your business data has not been modified.")
        return 1

    window = webview.create_window(
        "LedgerMate",
        FRONTEND_URL,
        width=1280,
        height=800,
        resizable=True,
        text_select=True,
    )
    webview.start(debug=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
