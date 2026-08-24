"""LedgerMate V2 — llama.cpp LLM provider."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from ledgermate.providers.base import ExtractedTransaction, LLMProvider


class LlamaCppProvider(LLMProvider):
    name = "llama.cpp"
    available = False  # set True when executable + model exist

    def __init__(self, model_path: Path | None = None, exe_path: Path | None = None) -> None:
        self.model_path = model_path or Path(__file__).resolve().parents[2] / "model" / "llama-3.2-1b-instruct-q4_k_m.gguf"
        self.exe_path = exe_path or self._find_executable()
        self.available = self.model_path.exists() and bool(self.exe_path)

    def _find_executable(self) -> str:
        env_path = os.environ.get("LLAMA_CLI_PATH")
        if env_path:
            path = Path(env_path)
            if not path.exists() or path.is_dir():
                raise RuntimeError(f"llama.cpp executable not found: {env_path}")
            if path.name.lower() not in {"llama-cli.exe", "llama-server.exe", "llama-cli", "llama-server"}:
                raise RuntimeError(f"Invalid llama.cpp executable: {env_path}")
            return str(path.resolve())
        for name in ["llama-cli", "llama-cli.exe", "llama-server", "llama-server.exe"]:
            path = shutil.which(name)
            if path:
                return path
        winget_dir = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages"
        if winget_dir.exists():
            for package_dir in winget_dir.iterdir():
                if "llamacpp" in package_dir.name.lower() or "ggml" in package_dir.name.lower():
                    for exe_name in ["llama-cli.exe", "llama-server.exe", "llama-cli", "llama-server"]:
                        candidate = package_dir / exe_name
                        if candidate.exists() and candidate.is_file():
                            return str(candidate.resolve())
        raise RuntimeError(
            "llama.cpp executable not found. Set LLAMA_CLI_PATH to the full path of llama-cli.exe."
        )

    def extract_transaction(self, transcript: str) -> ExtractedTransaction:
        structured_prompt = (
            "Extract a bookkeeping transaction from the user message as JSON only. "
            "Return keys: transaction_type (income|expense), amount (positive number without commas), "
            "currency (XAF|USD|EUR|GBP|NGN|GHS|KES), date (YYYY-MM-DD), description, category, counterparty, notes. "
            "If date is missing, use today's date. If amount is missing, use 0. Never invent values.\n\n"
            "User: " + transcript + "\nJSON:"
        )
        cmd = [
            str(self.exe_path),
            "-m", str(self.model_path),
            "-p", structured_prompt,
            "-n", "512",
            "-c", "1024",
            "-t", "4",
            "--temp", "0.0",
            "-ngl", "0",
            "--log-disable",
            "-st",
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, stdin=subprocess.PIPE)
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"llama.cpp failed: {exc.stderr}") from exc

        raw = result.stdout.strip()
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("LLM response did not contain JSON object")
        data = json.loads(raw[start : end + 1])
        return ExtractedTransaction(
            transaction_type=data.get("transaction_type", "expense"),
            amount=str(data.get("amount", "0")),
            currency=data.get("currency", "XAF"),
            date=data.get("date", ""),
            description=data.get("description", ""),
            category=data.get("category", "general"),
            counterparty=data.get("counterparty"),
            payment_method=data.get("payment_method"),
            notes=data.get("notes"),
        )
