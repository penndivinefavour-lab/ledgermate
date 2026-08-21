"""llama.cpp inference wrapper for LedgerMate."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

MODEL_PATH = Path(__file__).resolve().parents[3] / "model" / "llama-3.2-1b-instruct-q4_k_m.gguf"


def _find_llama_executable() -> str:
    candidates = [
        "llama-cli",
        "llama-server",
        "main",
        str(Path(__file__).resolve().parents[3] / "bin" / "llama-cli.exe"),
        str(Path(__file__).resolve().parents[3] / "bin" / "main.exe"),
    ]
    for name in candidates:
        path = subprocess.run(
            ["where", name] if os.name == "nt" else ["which", name],
            capture_output=True,
            text=True,
        ).stdout.strip()
        if path:
            return path.splitlines()[0]
    raise FileNotFoundError("llama.cpp executable not found on PATH.")


def run_llama(prompt: str, *, n_ctx: int = 1024, threads: int = 4, temperature: float = 0.0, max_tokens: int = 256) -> str:
    exe = _find_llama_executable()
    cmd = [
        exe,
        "-m",
        str(MODEL_PATH),
        "-p",
        prompt,
        "-n",
        str(max_tokens),
        "-c",
        str(n_ctx),
        "-t",
        str(threads),
        "--temp",
        str(temperature),
        "-ngl",
        "0",
        "--log-disable",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"llama.cpp failed: {exc.stderr}") from exc
    return result.stdout.strip()


def extract_transaction_json(prompt: str) -> dict[str, Any]:
    structured_prompt = (
        "Extract a bookkeeping transaction from the user message as JSON only. "
        "Return keys: date (YYYY-MM-DD), description, category, type (income|expense|transfer|debt_in|debt_out), "
        "amount (positive number), currency (XAF|USD|EUR|GBP|NGN|GHS|KES), payment_method (cash|mobile_money|bank|credit|other), "
        "counterparty, notes, transaction_id (slug).\n\nUser: "
        + prompt
        + "\nJSON:"
    )
    raw = run_llama(structured_prompt, max_tokens=512)
    try:
        start = raw.find("{")
        end = raw.rfind("}")
        return json.loads(raw[start : end + 1])
    except Exception:
        return {"raw": raw}
