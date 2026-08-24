"""llama.cpp inference wrapper for LedgerMate."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

MODEL_PATH = Path(__file__).resolve().parents[2] / "model" / "llama-3.2-1b-instruct-q4_k_m.gguf"


def _validate_llama_executable(path: str) -> str:
    """Validate that path is an actual llama-cli/llama-server executable."""
    p = Path(path)
    if not p.exists():
        raise RuntimeError(f"llama.cpp executable not found: {path}")
    if p.is_dir():
        raise RuntimeError(f"llama.cpp path is a directory: {path}")
    name = p.name.lower()
    if name not in {"llama-cli.exe", "llama-server.exe", "llama-cli", "llama-server"}:
        raise RuntimeError(
            f"Invalid llama.cpp executable: {path}. "
            "Expected llama-cli.exe or llama-server.exe."
        )
    return str(p.resolve())


def _find_llama_executable() -> str:
    """Find llama-cli or llama-server on Windows/Linux."""
    env_path = os.environ.get("LLAMA_CLI_PATH")
    if env_path:
        return _validate_llama_executable(env_path)
    candidates = [
        "llama-cli",
        "llama-cli.exe",
        "llama-server",
        "llama-server.exe",
    ]
    for name in candidates:
        path = shutil.which(name)
        if path:
            return _validate_llama_executable(path)
    winget_dir = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages"
    if winget_dir.exists():
        for package_dir in winget_dir.iterdir():
            if "llamacpp" in package_dir.name.lower() or "ggml" in package_dir.name.lower():
                for exe_name in ["llama-cli.exe", "llama-server.exe", "llama-cli", "llama-server"]:
                    candidate = package_dir / exe_name
                    if candidate.exists() and candidate.is_file():
                        return _validate_llama_executable(str(candidate))
    raise RuntimeError(
        "llama.cpp executable not found. Set LLAMA_CLI_PATH to the full path of llama-cli.exe."
    )


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
        "-st",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, stdin=subprocess.PIPE)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"llama.cpp failed: {exc.stderr}") from exc
    return _sanitize_llama_output(result.stdout)


def _sanitize_llama_output(raw: str) -> str:
    """Remove llama.cpp runtime metadata from user-facing output."""
    lines = raw.splitlines()
    kept: list[str] = []
    skip_prefixes = (
        "build",
        "model",
        "ftype",
        "modalities",
        "available commands:",
        "> ",
        "[ Prompt:",
        "[ Generation:",
        "Exiting...",
    )
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(skip_prefixes):
            continue
        if stripped.startswith("llama.cpp"):
            continue
        kept.append(line)
    text = "\n".join(kept).strip()
    # Remove markdown code fences when model adds them around JSON/answer blocks
    if text.startswith("```"):
        text = text.lstrip("`")
    return text.strip()


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
