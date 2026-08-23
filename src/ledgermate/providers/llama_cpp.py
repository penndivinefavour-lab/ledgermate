"""LedgerMate V2 — llama.cpp LLM provider."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

from ledgermate.providers.base import ExtractedTransaction, LLMProvider


class LlamaCppProvider(LLMProvider):
    name = "llama.cpp"
    available = False  # set True when executable + model exist

    def __init__(self, model_path: Path | None = None, exe_path: Path | None = None) -> None:
        self.model_path = model_path or Path(__file__).resolve().parents[3] / "model" / "llama-3.2-1b-instruct-q4_k_m.gguf"
        self.exe_path = exe_path or self._find_executable()
        self.available = self.model_path.exists() and bool(self.exe_path)

    def _find_executable(self) -> str:
        candidates = [
            "llama-cli",
            "llama-server",
            str(Path(__file__).resolve().parents[3] / "bin" / "llama-cli.exe"),
            str(Path(__file__).resolve().parents[3] / "bin" / "main.exe"),
        ]
        for name in candidates:
            result = subprocess.run(["where", name] if os.name == "nt" else ["which", name], capture_output=True, text=True)
            if result.stdout.strip():
                return result.stdout.strip().splitlines()[0]
        raise FileNotFoundError("llama.cpp executable not found on PATH")

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
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
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
