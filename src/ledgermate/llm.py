"""llama.cpp inference wrapper for LedgerMate."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from decimal import Decimal
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
        "Loading",
        "llama.cpp",
        "/exit",
        "/regen",
        "/clear",
        "/read",
        "/glob",
    )
    kept: list[str] = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if any(stripped.startswith(p) for p in skip_prefixes):
            continue
        if not any(ch.isalnum() or ch in "{}[]\"':,./_-" for ch in stripped):
            continue
        kept.append(line)
    text = "\n".join(kept).strip()
    if text.startswith("```"):
        text = text.lstrip("`")
    return text.strip()


def _extract_json_object(text: str) -> dict[str, Any]:
    start = text.find("{")
    if start == -1:
        return {}
    depth = 0
    for idx in range(start, len(text)):
        char = text[idx]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start : idx + 1])
                except Exception:
                    return {}
    return {}


def _extract_json_array(text: str) -> list[dict[str, Any]]:
    start = text.find("[")
    if start == -1:
        return []
    depth = 0
    for idx in range(start, len(text)):
        char = text[idx]
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start : idx + 1])
                except Exception:
                    return []
    return []


def extract_transaction_json(prompt: str) -> dict[str, Any]:
    """Extract a transaction from natural language using LLM.
    
    Returns a dict with transaction fields. The backend should validate and
    compute amounts deterministically from items if the model output is ambiguous.
    """
    structured_prompt = (
        "Extract a bookkeeping transaction from the user message as JSON only. "
        "Return keys: date (YYYY-MM-DD), description, category, type (income|expense|transfer|debt_in|debt_out), "
        "currency (XAF|USD|EUR|GBP|NGN|GHS|KES), payment_method (cash|mobile_money|bank|credit|other), "
        "counterparty, notes, transaction_id (slug). "
        "Also include `items` as an array of objects with keys: description, quantity (number), unit_price (number), total (number). "
        "If there is only one item, still return it in `items`. Do not include extra prose.\n\nUser: "
        + prompt
        + "\nJSON:\n"
    )
    raw = run_llama(structured_prompt, max_tokens=512)
    text = _sanitize_llama_output(raw)
    transaction_part = _extract_json_object(text)
    items_part = _extract_json_array(text)
    if isinstance(transaction_part, list):
        items_part = transaction_part
        transaction_part = {}
    if not isinstance(transaction_part, dict):
        transaction_part = {}
    if isinstance(items_part, list) and items_part:
        transaction_part["items"] = items_part
        computed_total = Decimal("0")
        for item in items_part:
            if not isinstance(item, dict):
                continue
            try:
                amount_value = item.get("amount")
                total_value = item.get("total")
                qty = Decimal(str(item.get("quantity", 1)))
                unit = Decimal(str(item.get("unit_price", 0)))
                if amount_value is not None:
                    total = Decimal(str(amount_value))
                elif total_value is not None:
                    total = Decimal(str(total_value))
                else:
                    total = qty * unit
                if total <= 0:
                    # Fallback: extract number from description field
                    desc = str(item.get("description", ""))
                    m = re.search(r"(\d[\d,]*\.?\d*)", desc.replace(",", ""))
                    if m:
                        total = Decimal(m.group(1))
                    else:
                        continue
                computed_total += total
            except Exception:
                continue
        if computed_total > 0:
            transaction_part["amount"] = int(computed_total)
    return transaction_part