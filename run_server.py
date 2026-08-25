"""LedgerMate development server launcher with Windows port guard."""
from __future__ import annotations

import json
import os
import socket
import sys
from pathlib import Path

import uvicorn


def _port_in_use(port: int) -> bool:
    try:
        import subprocess
        out = subprocess.check_output(["netstat", "-ano"], text=True, timeout=5)
    except Exception:
        return False
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[1].endswith(f":{port}") and parts[-2].upper() == "LISTENING":
            return True
    return False


def _can_bind(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def _owner_process(port: int) -> dict | None:
    try:
        import subprocess
        out = subprocess.check_output(["netstat", "-ano"], text=True, timeout=5)
    except Exception:
        return None
    info: dict = {"bindings": [], "pids": []}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[1].endswith(f":{port}") and parts[-2].upper() == "LISTENING":
            pid = parts[-1]
            info["bindings"].append({"proto": parts[0], "addr": parts[1], "state": parts[-2], "pid": pid})
            info["pids"].append(pid)
    info["pids"] = sorted(set(info["pids"]))
    for pid in info["pids"]:
        try:
            cmd = subprocess.check_output(["tasklist", "/FI", f"PID eq {pid}", "/NH"], text=True, timeout=5).strip()
            info.setdefault("processes", {})[pid] = cmd
        except Exception:
            pass
    return info


def _is_ledgermate_health(port: int) -> bool:
    try:
        import urllib.request
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=2) as resp:
            body = resp.read().decode("utf-8")
            return '"status":"ok"' in body and '"offline"' in body
    except Exception:
        return False


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "src"))
    os.chdir(root)

    host = os.environ.get("LEDGERMATE_HOST", "127.0.0.1")
    port = int(os.environ.get("LEDGERMATE_PORT", "8000"))

    if _port_in_use(port):
        owner = _owner_process(port)
        ledgermate_running = bool(owner and _is_ledgermate_health(port))
        print(f"[LedgerMate] Port {host}:{port} is in use.")
        if owner:
            print(f"[LedgerMate] Owner diagnostics: {json.dumps(owner)}")
        if ledgermate_running:
            print(f"[LedgerMate] Existing LedgerMate instance detected at http://{host}:{port}")
            print("[LedgerMate] Open that URL instead of starting another instance.")
            return 0
        fallback = port + 1
        while _port_in_use(fallback) or not _can_bind(fallback):
            fallback += 1
        print(f"[LedgerMate] Falling back to http://{host}:{fallback}")
        port = fallback

    print(f"[LedgerMate] Starting server at http://{host}:{port}")
    uvicorn.run("ledgermate.api:app", host=host, port=port, reload=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
